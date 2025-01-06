import ctypes
import sys
import keyboard
import math
from monitorcontrol import get_monitors
from PyQt5 import QtWidgets, QtCore, QtGui
import os
import logging
from typing import List

# Constants
SLIDER_WIDTH = 240
SLIDER_HEIGHT = 30
MARGIN = 20
SPACING = 10
PADDING_LEFT = 4
FONT_STYLE = "12pt 'Segoe UI'"
LABEL_COLOR = "white"
WINDOW_OPACITY = 0.0
INITIAL_BRIGHTNESS = 50
GEOMETRY_OFFSET_Y = 30
TICK_INTERVAL = 10
TICK_POSITION = QtWidgets.QSlider.TicksBelow
INACTIVITY_INTERVAL = 2000  # milliseconds
DEBOUNCE_INTERVAL = 100  # milliseconds
FADE_IN_DURATION = 300  # milliseconds
FADE_OUT_DURATION = 1000  # milliseconds

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug dictionaries to store brightness levels by monitor index
monitor_brightness = {}
last_brightness = {}

# Cached list of monitor objects
cached_monitors: List = []

def ensure_admin():
    """
    Checks if the current process has administrator privileges on Windows.
    If not, attempts to restart the script with admin rights.
    """
    logger.debug("Checking for admin privileges...")
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        logger.debug(f"Is user admin: {is_admin}")
    except Exception as e:
        logger.error(f"Exception while checking admin status: {e}")
        is_admin = False

    if not is_admin:
        logger.debug("Relaunching script with admin rights...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas",
                sys.executable,
                " ".join(sys.argv),
                None, 1
            )
        except Exception as e:
            logger.error(f"Failed to relaunch as admin: {e}")
        sys.exit()

def RetrieveMonitors() -> List:
    """
    Retrieves the list of monitors, initializes the brightness dictionaries,
    and logs debug information.

    Returns:
        List of Monitor objects from the monitorcontrol library.
    """
    global cached_monitors
    logger.debug("Retrieving monitors...")
    monitors = get_monitors()
    cached_monitors = monitors  # Cache the monitors for later use
    logger.debug(f"Detected monitors: {monitors}")

    for idx, monitor in enumerate(monitors):
        with monitor:
            try:
                brightness = monitor.get_luminance()
                brightness = round(brightness, -1)
                monitor_brightness[idx] = brightness
                last_brightness[idx] = brightness
                logger.debug(f"Monitor {idx} brightness initialized to: {brightness}")
            except Exception as e:
                logger.error(f"Error retrieving brightness for Monitor {idx}: {e}")
                if hasattr(e, 'response'):
                    logger.debug(f"Raw response: {e.response}")
    return monitors

def ChangeBrightness(idx: int, brightness: int):
    """
    Changes the brightness of the monitor at the given index.

    Args:
        idx (int): The monitor index to adjust.
        brightness (int): The brightness level to set (0-100).
    """
    global cached_monitors
    if idx < 0 or idx >= len(cached_monitors):
        logger.debug(f"Invalid monitor index: {idx}")
        return

    monitor = cached_monitors[idx]
    logger.debug(f"Attempting to set brightness of Monitor {idx} to {brightness}...")
    try:
        with monitor:
            monitor.set_luminance(brightness)
        logger.debug(f"Brightness set to {brightness} for Monitor {idx}")
    except Exception as e:
        logger.error(f"Exception while setting brightness for Monitor {idx} to {brightness}: {e}")
        # Optionally, implement fallback mechanisms or notify the user here
    logger.debug(f"Finished setting brightness to: {brightness} for Monitor {idx}")

def RetrieveBrightness():
    """
    Retrieves current brightness for all monitors and updates the dictionaries.
    """
    logger.debug("Retrieving current brightness for all monitors...")
    for idx, monitor in enumerate(cached_monitors):
        logger.debug(f"Monitor {idx}: {monitor}")
        try:
            with monitor:
                brightness = monitor.get_luminance()
            logger.debug(f"Current Brightness for Monitor {idx}: {brightness}")
            brightness = round(brightness, -1)
            monitor_brightness[idx] = brightness
            last_brightness[idx] = brightness
            logger.debug(f"Brightness rounded to: {brightness} for Monitor {idx}")
        except Exception as e:
            logger.error(f"Error interacting with Monitor {idx}: {e}")
            if hasattr(e, 'response'):
                logger.debug(f"Raw response: {e.response}")

class BrightnessSlider(QtWidgets.QWidget):
    """
    A widget for displaying and adjusting the brightness slider.

    The slider stays on-screen as long as the user continues adjusting brightness
    (Page Up or Page Down). After inactivity, it fades out.
    """
    update_slider_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        logger.debug("Initializing BrightnessSlider...")
        super().__init__()

        # Keep the window always on top and frameless
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(WINDOW_OPACITY)  # Start fully transparent

        # Positioning the slider near the bottom center of the screen
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - SLIDER_WIDTH) // 2
        y = screen_geometry.height() - SLIDER_HEIGHT - GEOMETRY_OFFSET_Y
        self.setGeometry(x, y, SLIDER_WIDTH, SLIDER_HEIGHT)
        logger.debug(f"Slider geometry set to: x={x}, y={y}, width={SLIDER_WIDTH}, height={SLIDER_HEIGHT}")

        # Main layout
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(SPACING)

        # Insert Custom Icon (Programmatically Drawn)
        self.icon = self.create_icon()
        layout.addWidget(self.icon)

        # Label to display current brightness percentage
        self.percent_label = self.create_percent_label()
        layout.addWidget(self.percent_label)

        # Slider setup
        self.slider = self.create_slider()
        layout.addWidget(self.slider)

        self.setLayout(layout)
        self.hide()
        logger.debug("BrightnessSlider initialized and hidden by default.")

        self.update_slider_signal.connect(self.handle_update_slider)

        # Timer to hide the slider after inactivity
        self.inactivity_timer = QtCore.QTimer(self)
        self.inactivity_timer.setInterval(INACTIVITY_INTERVAL)  # 2 seconds of no activity
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.start_fade_out)

        # Debounce timer to limit brightness change frequency
        self.debounce_timer = QtCore.QTimer(self)
        self.debounce_timer.setInterval(DEBOUNCE_INTERVAL)  # 100 milliseconds
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.apply_brightness_change)
        self.latest_brightness = INITIAL_BRIGHTNESS  # Initial brightness

        # Subtle drop shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        logger.debug("Drop shadow effect applied to BrightnessSlider.")

        # Apply stylesheet for enhanced styling
        self.apply_stylesheet()

        # Fade-in animation
        self.fade_in = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(FADE_IN_DURATION)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(0.9)
        self.fade_in.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        # Fade-out animation with extended duration
        self.fade_out = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(FADE_OUT_DURATION)  # Increased from 700 to 1000 milliseconds
        self.fade_out.setStartValue(0.9)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.hide)
        logger.debug("Animations initialized with extended fade-out duration.")

    def apply_stylesheet(self):
        """
        Applies the stylesheet to the BrightnessSlider to mimic Windows 11 design.
        """
        self.setStyleSheet("""
            BrightnessSlider {
                background-color: rgba(30, 30, 30, 220);
                border-radius: 30px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #444;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0c7cd5;
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -5px 0; 
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #3399ff;
            }
            QSlider::sub-page:horizontal {
                background: #0c7cd5;
                border: 1px solid #777;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #444;
                border: 1px solid #777;
                height: 8px;
                border-radius: 4px;
            }
        """)
        logger.debug("Stylesheet applied to BrightnessSlider.")

    def create_icon(self) -> QtWidgets.QLabel:
        """
        Creates the sun icon label.

        Returns:
            QLabel: The label containing the sun pixmap.
        """
        icon_label = QtWidgets.QLabel()
        pixmap = self.create_sun_pixmap(24, 24)
        icon_label.setPixmap(pixmap)
        return icon_label

    def create_percent_label(self) -> QtWidgets.QLabel:
        """
        Creates the label to display current brightness percentage.

        Returns:
            QLabel: The percentage label.
        """
        label = QtWidgets.QLabel(f"{INITIAL_BRIGHTNESS}%")
        label.setStyleSheet(f"""
            QLabel {{
                font: {FONT_STYLE};
                color: {LABEL_COLOR};
                padding-left: {PADDING_LEFT}px;
            }}
        """)
        return label

    def create_slider(self) -> QtWidgets.QSlider:
        """
        Creates and initializes the brightness slider.

        Returns:
            QSlider: The brightness slider.
        """
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(INITIAL_BRIGHTNESS)
        slider.setTickPosition(TICK_POSITION)
        slider.setTickInterval(TICK_INTERVAL)
        slider.setSingleStep(1)
        slider.valueChanged.connect(self.slider_moved)
        logger.debug("Slider created and initialized.")
        return slider

    def create_sun_pixmap(self, width: int, height: int) -> QtGui.QPixmap:
        """
        Creates a sun-shaped QPixmap by drawing with QPainter.

        Args:
            width (int): Width of the pixmap.
            height (int): Height of the pixmap.

        Returns:
            QPixmap: The generated sun icon.
        """
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtCore.Qt.transparent)  # Start with a transparent pixmap

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw the sun's core
        core_color = QtGui.QColor('yellow')
        painter.setBrush(core_color)
        painter.setPen(QtGui.QPen(core_color))
        center = QtCore.QPoint(width // 2, height // 2)
        radius = min(width, height) // 4
        painter.drawEllipse(center, radius, radius)

        # Draw sun rays
        ray_color = QtGui.QColor('orange')
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(ray_color, 2))
        num_rays = 8
        ray_length = min(width, height) // 2
        for i in range(num_rays):
            angle = (360 / num_rays) * i
            radians = math.radians(angle)
            start_point = QtCore.QPointF(
                center.x() + radius * math.cos(radians),
                center.y() + radius * math.sin(radians)
            )
            end_point = QtCore.QPointF(
                center.x() + ray_length * math.cos(radians),
                center.y() + ray_length * math.sin(radians)
            )
            painter.drawLine(start_point, end_point)

        painter.end()
        return pixmap

    def slider_moved(self, value: int):
        """
        Called when the internal slider is manually adjusted.
        Updates the percentage label, resets the inactivity timer,
        and schedules a brightness update with debounce.

        Args:
            value (int): The new slider value.
        """
        logger.debug(f"slider_moved called with value: {value}")
        self.percent_label.setText(f"{value}%")

        self.latest_brightness = value

        # Reset the inactivity timer every time the user moves the slider
        self.inactivity_timer.stop()
        self.inactivity_timer.start()

        # Reset debounce timer to limit brightness change frequency
        self.debounce_timer.stop()
        self.debounce_timer.start()

    def apply_brightness_change(self):
        """
        Applies the brightness change for all monitors to the latest value set by the slider.
        """
        value = self.latest_brightness
        logger.debug(f"Applying brightness change to: {value}%")
        for idx in monitor_brightness:
            try:
                ChangeBrightness(idx, value)
                monitor_brightness[idx] = value
                last_brightness[idx] = value
                logger.debug(f"Updated Monitor {idx} brightness to: {value}")
            except Exception as e:
                logger.error(f"Failed to update brightness for Monitor {idx} to {value}: {e}")

    def show_slider(self, value: int):
        """
        Called externally (e.g., via KeyboardListener) to show the slider
        and set it to the specified brightness value.

        Args:
            value (int): The brightness value to set.
        """
        logger.debug(f"show_slider called with value: {value}")
        self.update_slider_signal.emit(value)

    @QtCore.pyqtSlot(int)
    def handle_update_slider(self, value: int):
        """
        Slot that handles updating the slider from an external signal.
        If the slider is hidden, fade in. If visible, just update the value.

        Args:
            value (int): The brightness value to set.
        """
        logger.debug(f"handle_update_slider called with value: {value}")
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self.fade_in.start()

        self.slider.setValue(value)
        self.percent_label.setText(f"{value}%")

        # Reset inactivity timer to keep it on screen while user is active
        self.inactivity_timer.stop()
        self.inactivity_timer.start()
        logger.debug("Inactivity timer reset.")

    def start_fade_out(self):
        """
        Initiates the fade-out animation after a period of inactivity.
        """
        logger.debug("Starting fade-out animation.")
        self.fade_out.start()

class KeyboardListener(QtCore.QThread):
    """
    Thread that listens for keyboard events using the 'keyboard' library.
    Emits 'brightness_changed' signal whenever Page Up or Page Down is pressed.
    """
    brightness_changed = QtCore.pyqtSignal(int)

    def run(self):
        logger.debug("KeyboardListener thread started.")
        keyboard.on_press(self.on_key_press)
        keyboard.wait()
        logger.debug("KeyboardListener thread ending.")

    def on_key_press(self, event):
        """
        Handles key press events. If Ctrl + Up or Ctrl + Down is pressed, adjust the
        brightness of all monitors and emit the 'brightness_changed' signal.

        Args:
            event: The keyboard event.
        """
        if keyboard.is_pressed('ctrl'):
            logger.debug("Key pressed: Ctrl")
            for idx in list(monitor_brightness.keys()):
                try:
                    if keyboard.is_pressed('up'):
                        target_brightness = min(monitor_brightness[idx] + 10, 100)
                    elif keyboard.is_pressed('down'):
                        target_brightness = max(monitor_brightness[idx] - 10, 0)

                    # Validate target_brightness
                    if target_brightness < 0 or target_brightness > 100:
                        logger.debug(f"TargetBrightness {target_brightness} is out of bounds for Monitor {idx}. Skipping.")
                        continue

                    if target_brightness != last_brightness.get(idx, -1):
                        ChangeBrightness(idx, target_brightness)
                        monitor_brightness[idx] = target_brightness
                        last_brightness[idx] = target_brightness
                        logger.debug(f"Brightness for Monitor {idx} set to {target_brightness}")
                        # Emit signal to update the slider
                        self.brightness_changed.emit(target_brightness)
                        logger.debug(f"brightness_changed signal emitted with value: {target_brightness}")
                except Exception as e:
                    logger.error(f"Exception while handling brightness change for Monitor {idx}: {e}")

def main():
    """
    Entry point for the application. Ensures admin privileges, retrieves monitors,
    creates the Qt application, sets up the slider and keyboard listener, and starts
    the event loop.
    """
    ensure_admin()
    RetrieveMonitors()

    app = QtWidgets.QApplication(sys.argv)
    slider = BrightnessSlider()

    listener = KeyboardListener()
    listener.brightness_changed.connect(slider.show_slider)
    logger.debug("Connected brightness_changed signal to slider.show_slider slot.")
    listener.start()
    logger.debug("KeyboardListener thread started.")

    # Optional: Test slider appearance on startup
    # slider.show_slider(50)

    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(e)
        os.system("pause")