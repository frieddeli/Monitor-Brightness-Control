import ctypes
import sys
import keyboard
import math
from monitorcontrol import get_monitors
from PyQt5 import QtWidgets, QtCore, QtGui
import os

# Debug dictionaries to store brightness levels by monitor index
monitor_brightness = {}
last_brightness = {}

# Cached list of monitor objects
cached_monitors = []

def ensure_admin():
    """
    Checks if the current process has administrator privileges on Windows.
    If not, attempts to restart the script with admin rights.
    """
    print("[DEBUG] Checking for admin privileges...")
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"[DEBUG] Is user admin: {is_admin}")
    except Exception as e:
        print(f"[DEBUG] Exception while checking admin status: {e}")
        is_admin = False

    if not is_admin:
        print("[DEBUG] Relaunching script with admin rights...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas",
                sys.executable,
                " ".join(sys.argv),
                None, 1
            )
        except Exception as e:
            print(f"[DEBUG] Failed to relaunch as admin: {e}")
        sys.exit()

def RetrieveMonitors():
    """
    Retrieves the list of monitors, initializes the brightness dictionaries,
    and logs debug information.

    Returns:
        List of Monitor objects from the monitorcontrol library.
    """
    global cached_monitors
    print("[DEBUG] Retrieving monitors...")
    monitors = get_monitors()
    cached_monitors = monitors  # Cache the monitors for later use
    print(f"[DEBUG] Detected monitors: {monitors}")

    for idx, monitor in enumerate(monitors):
        with monitor:
            try:
                brightness = monitor.get_luminance()
                brightness = round(brightness, -1)
                monitor_brightness[idx] = brightness
                last_brightness[idx] = brightness
                print(f"[DEBUG] Monitor {idx} brightness initialized to: {brightness}")
            except Exception as e:
                print(f"[DEBUG] Error retrieving brightness for Monitor {idx}: {e}")
                if hasattr(e, 'response'):
                    print(f"[DEBUG] Raw response: {e.response}")
    return monitors

def ChangeBrightness(idx, brightness):
    """
    Changes the brightness of the monitor at the given index.

    Args:
        idx (int): The monitor index to adjust.
        brightness (int): The brightness level to set (0-100).
    """
    global cached_monitors
    if idx < 0 or idx >= len(cached_monitors):
        print(f"[DEBUG] Invalid monitor index: {idx}")
        return

    monitor = cached_monitors[idx]
    print(f"[DEBUG] Attempting to set brightness of Monitor {idx} to {brightness}...")
    try:
        with monitor:
            monitor.set_luminance(brightness)
        print(f"[DEBUG] Brightness set to {brightness} for Monitor {idx}")
    except Exception as e:
        print(f"[DEBUG] Exception while setting brightness for Monitor {idx} to {brightness}: {e}")
        # Optionally, implement fallback mechanisms or notify the user here
    print(f"[DEBUG] Finished setting brightness to: {brightness} for Monitor {idx}")

def RetrieveBrightness():
    """
    Retrieves current brightness for all monitors and updates the dictionaries.
    """
    print("[DEBUG] Retrieving current brightness for all monitors...")
    for idx, monitor in enumerate(cached_monitors):
        print(f"[DEBUG] Monitor {idx}: {monitor}")
        try:
            with monitor:
                brightness = monitor.get_luminance()
            print(f"[DEBUG] Current Brightness for Monitor {idx}: {brightness}")
            brightness = round(brightness, -1)
            monitor_brightness[idx] = brightness
            last_brightness[idx] = brightness
            print(f"[DEBUG] Brightness rounded to: {brightness} for Monitor {idx}")
        except Exception as e:
            print(f"[DEBUG] Error interacting with Monitor {idx}: {e}")
            if hasattr(e, 'response'):
                print(f"[DEBUG] Raw response: {e.response}")

class BrightnessSlider(QtWidgets.QWidget):
    """
    A widget for displaying and adjusting the brightness slider.

    The slider stays on-screen as long as the user continues adjusting brightness
    (Page Up or Page Down). After inactivity, it fades out.
    """
    update_slider_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        print("[DEBUG] Initializing BrightnessSlider...")
        super().__init__()

        # Keep the window always on top and frameless
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)  # Start fully transparent

        # Positioning the slider near the bottom center of the screen
        screen_geometry = QtWidgets.QApplication.desktop().availableGeometry()
        slider_width = 240
        slider_height = 30
        x = (screen_geometry.width() - slider_width) // 2
        y = screen_geometry.height() - slider_height - 30
        self.setGeometry(x, y, slider_width, slider_height)
        print(f"[DEBUG] Slider geometry set to: x={x}, y={y}, width={slider_width}, height={slider_height}")

        # Main layout
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Insert Custom Icon (Programmatically Drawn)
        self.icon = QtWidgets.QLabel()
        pixmap = self.create_sun_pixmap(24, 24)
        self.icon.setPixmap(pixmap)
        layout.addWidget(self.icon)

        # Label to display current brightness percentage
        self.percent_label = QtWidgets.QLabel("50%")
        self.percent_label.setStyleSheet("""
            QLabel {
                font: 12pt 'Segoe UI';
                color: white;
                padding-left: 4px;
            }
        """)
        layout.addWidget(self.percent_label)

        # Slider setup
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.slider_moved)
        layout.addWidget(self.slider)

        self.setLayout(layout)
        self.hide()
        print("[DEBUG] BrightnessSlider initialized and hidden by default.")

        self.update_slider_signal.connect(self.handle_update_slider)

        # Timer to hide the slider after inactivity
        self.inactivity_timer = QtCore.QTimer(self)
        self.inactivity_timer.setInterval(2000)  # 2 seconds of no activity
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.start_fade_out)

        # Debounce timer to limit brightness change frequency
        self.debounce_timer = QtCore.QTimer(self)
        self.debounce_timer.setInterval(100)  # 100 milliseconds
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.apply_brightness_change)
        self.latest_brightness = 50  # Initial brightness

        # Subtle drop shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        print("[DEBUG] Drop shadow effect applied to BrightnessSlider.")

        # Apply stylesheet for enhanced styling
        self.apply_stylesheet()

        # Fade-in animation
        self.fade_in = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(0.9)
        self.fade_in.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        # Fade-out animation with extended duration
        self.fade_out = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(1000)  # Increased from 700 to 1000 milliseconds
        self.fade_out.setStartValue(0.9)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.hide)
        print("[DEBUG] Animations initialized with extended fade-out duration.")

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
        print("[DEBUG] Stylesheet applied to BrightnessSlider.")

    def create_sun_pixmap(self, width, height):
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

    def slider_moved(self, value):
        """
        Called when the internal slider is manually adjusted.
        We update the percentage label, reset the inactivity timer,
        and schedule a brightness update with debounce.
        """
        print(f"[DEBUG] slider_moved called with value: {value}")
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
        print(f"[DEBUG] Applying brightness change to: {value}%")
        for idx in monitor_brightness:
            try:
                ChangeBrightness(idx, value)
                monitor_brightness[idx] = value
                last_brightness[idx] = value
                print(f"[DEBUG] Updated Monitor {idx} brightness to: {value}")
            except Exception as e:
                print(f"[DEBUG] Failed to update brightness for Monitor {idx} to {value}: {e}")

    def show_slider(self, value):
        """
        Called externally (e.g., via KeyboardListener) to show the slider
        and set it to the specified brightness value.
        """
        print(f"[DEBUG] show_slider called with value: {value}")
        self.update_slider_signal.emit(value)

    @QtCore.pyqtSlot(int)
    def handle_update_slider(self, value):
        """
        Slot that handles updating the slider from an external signal.
        If the slider is hidden, fade in. If visible, just update the value.
        """
        print(f"[DEBUG] handle_update_slider called with value: {value}")
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self.fade_in.start()

        self.slider.setValue(value)
        self.percent_label.setText(f"{value}%")

        # Reset inactivity timer to keep it on screen while user is active
        self.inactivity_timer.stop()
        self.inactivity_timer.start()
        print("[DEBUG] Inactivity timer reset.")

    def start_fade_out(self):
        """
        Initiates the fade-out animation after a period of inactivity.
        """
        print("[DEBUG] Starting fade-out animation.")
        self.fade_out.start()

class KeyboardListener(QtCore.QThread):
    """
    Thread that listens for keyboard events using the 'keyboard' library.
    Emits 'brightness_changed' signal whenever Page Up or Page Down is pressed.
    """
    brightness_changed = QtCore.pyqtSignal(int)

    def run(self):
        print("[DEBUG] KeyboardListener thread started.")
        keyboard.on_press(self.on_key_press)
        keyboard.wait()
        print("[DEBUG] KeyboardListener thread ending.")

    def on_key_press(self, event):
        """
        Handles key press events. If Ctrl + Up or Ctrl + Down is pressed, adjust the
        brightness of all monitors and emit the 'brightness_changed' signal.
        """
        if keyboard.is_pressed('ctrl'):
            print(f"[DEBUG] Key pressed: Ctrl")
            for idx in list(monitor_brightness.keys()):
                try:
                    if keyboard.is_pressed('up'):
                        TargetBrightness = min(monitor_brightness[idx] + 10, 100)
                    elif keyboard.is_pressed('down'):
                        TargetBrightness = max(monitor_brightness[idx] - 10, 0)

                    # Validate TargetBrightness
                    if TargetBrightness < 0 or TargetBrightness > 100:
                        print(f"[DEBUG] TargetBrightness {TargetBrightness} is out of bounds for Monitor {idx}. Skipping.")
                        continue

                    if TargetBrightness != last_brightness.get(idx, -1):
                        ChangeBrightness(idx, TargetBrightness)
                        monitor_brightness[idx] = TargetBrightness
                        last_brightness[idx] = TargetBrightness
                        print(f"[DEBUG] Brightness for Monitor {idx} set to {TargetBrightness}")
                        # Emit signal to update the slider
                        self.brightness_changed.emit(TargetBrightness)
                        print(f"[DEBUG] brightness_changed signal emitted with value: {TargetBrightness}")
                except Exception as e:
                    print(f"[DEBUG] Exception while handling brightness change for Monitor {idx}: {e}")

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
    print("[DEBUG] Connected brightness_changed signal to slider.show_slider slot.")
    listener.start()
    print("[DEBUG] KeyboardListener thread started.")

    # Optional: Test slider appearance on startup
    # slider.show_slider(50)

    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        os.system("pause")