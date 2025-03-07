from monitorcontrol import get_monitors
from PyQt5 import QtWidgets, QtCore, QtGui
import ctypes
import sys
import keyboard
import math
import os
import logging
from typing import List
import winreg
import win32con
import win32gui

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
APP_NAME = "MonitorBrightnessApp"

# Debug dictionaries to store brightness levels by monitor index
monitor_brightness = {}
last_brightness = {}

# Cached list of monitor objects
cached_monitors: List = []


def create_sun_pixmap(width: int, height: int) -> QtGui.QPixmap:
    """Creates a sun-shaped QPixmap by drawing with QPainter."""
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtCore.Qt.transparent)

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



def show_user_message(title, message):
    """Shows a user-friendly message dialog."""
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.exec_()

def ensure_admin():
    """
    Checks if the current process has administrator privileges on Windows.
    If not, attempts to restart the script with admin rights.
    Ensures this request happens only once by setting a registry key.
    """
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        is_admin = False

    if not is_admin:
        # Check if admin has been requested before
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software", 0, winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            winreg.OpenKey(key, APP_NAME)
            admin_requested = True
        except FileNotFoundError:
            admin_requested = False

        if not admin_requested:
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas",
                    sys.executable,
                    " ".join([os.path.abspath(sys.argv[0])] + sys.argv[1:]),
                    None, 1
                )
                # Set registry key to indicate admin has been requested
                app_key = winreg.CreateKey(key, APP_NAME)
                winreg.SetValueEx(app_key, "AdminRequested", 0, winreg.REG_SZ, "True")
                winreg.CloseKey(app_key)
            except Exception as e:
                show_user_message("Error", "Administrator privileges are required to run this application.")
            sys.exit()

# This function has been removed as it will be handled by the installer
# def add_to_startup():
#     """
#     Adds the script to Windows startup by creating a registry entry.
#     """
#     try:
#         exe_path = os.path.abspath(sys.argv[0])
#         key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
#                              r"Software\Microsoft\Windows\CurrentVersion\Run",
#                              0, winreg.KEY_SET_VALUE)
#         winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
#         winreg.CloseKey(key)
#     except Exception as e:
#         show_user_message("Warning", "Could not add application to startup. You'll need to start it manually.")

def RetrieveMonitors() -> List:
    """
    Retrieves the list of monitors, initializes the brightness dictionaries,
    and logs debug information.

    Returns:
        List of Monitor objects from the monitorcontrol library.
    """
    global cached_monitors
    try:
        monitors = get_monitors()
        cached_monitors = monitors  # Cache the monitors for later use

        for idx, monitor in enumerate(monitors):
            with monitor:
                try:
                    brightness = monitor.get_luminance()
                    brightness = round(brightness, -1)
                    monitor_brightness[idx] = brightness
                    last_brightness[idx] = brightness
                except Exception as e:
                    if hasattr(e, 'response'):
                        pass
    except Exception as e:
        show_user_message("Error", "Failed to detect monitors. Please ensure your monitors support DDC/CI.")
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
        return

    monitor = cached_monitors[idx]
    try:
        with monitor:
            monitor.set_luminance(brightness)
    except Exception as e:
        show_user_message("Error", f"Failed to change brightness for Monitor {idx+1}")

def RetrieveBrightness():
    """
    Retrieves current brightness for all monitors and updates the dictionaries.
    """
    for idx, monitor in enumerate(cached_monitors):
        try:
            with monitor:
                brightness = monitor.get_luminance()
            brightness = round(brightness, -1)
            monitor_brightness[idx] = brightness
            last_brightness[idx] = brightness
        except Exception as e:
            if hasattr(e, 'response'):
                pass

def hide_console():
    """Hide the console window"""
    window = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(window, win32con.SW_HIDE)

class BrightnessSlider(QtWidgets.QWidget):
    """
    A widget for displaying and adjusting the brightness slider.

    The slider stays on-screen as long as the user continues adjusting brightness
    (Page Up or Page Down). After inactivity, it fades out.
    """
    update_slider_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Modified window flags and attributes
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.MSWindowsFixedSizeDialogHint  # Add this instead of NoDropShadowWindowHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        
        # Add fixed size to prevent geometry issues
        self.setFixedSize(SLIDER_WIDTH + 2 * MARGIN, SLIDER_HEIGHT + 2 * MARGIN)
        
        # Positioning the slider near the bottom center of the screen
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.height() - self.height() - GEOMETRY_OFFSET_Y
        self.setGeometry(x, y, self.width(), self.height())

        # Main layout
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(SPACING)
        layout.setAlignment(QtCore.Qt.AlignCenter)

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

    def create_icon(self) -> QtWidgets.QLabel:
        """
        Creates the sun icon label.

        Returns:
            QLabel: The label containing the sun pixmap.
        """
        icon_label = QtWidgets.QLabel()
        pixmap = create_sun_pixmap(24, 24)  # Using imported function
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
        return slider


    def slider_moved(self, value: int):
        """
        Called when the internal slider is manually adjusted.
        Updates the percentage label, resets the inactivity timer,
        and schedules a brightness update with debounce.

        Args:
            value (int): The new slider value.
        """
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
        for idx in monitor_brightness:
            try:
                ChangeBrightness(idx, value)
                monitor_brightness[idx] = value
                last_brightness[idx] = value
            except Exception as e:
                show_user_message("Error", f"Could not adjust brightness for Monitor {idx+1}")

    def show_slider(self, value: int = INITIAL_BRIGHTNESS):
        """
        Called externally (e.g., via KeyboardListener) to show the slider
        and set it to the specified brightness value.

        Args:
            value (int): The brightness value to set.
        """
        # Ensure proper positioning before showing
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.height() - self.height() - GEOMETRY_OFFSET_Y
        self.setGeometry(x, y, self.width(), self.height())
        self.update_slider_signal.emit(value)

    @QtCore.pyqtSlot(int)
    def handle_update_slider(self, value: int):
        """
        Slot that handles updating the slider from an external signal.
        If the slider is hidden, fade in. If visible, just update the value.

        Args:
            value (int): The brightness value to set.
        """
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
            self.fade_in.start()

        self.slider.setValue(value)
        self.percent_label.setText(f"{value}%")

        # Reset inactivity timer to keep it on screen while user is active
        self.inactivity_timer.stop()
        self.inactivity_timer.start()

    def start_fade_out(self):
        """
        Initiates the fade-out animation after a period of inactivity.
        """
        self.fade_out.start()

class KeyboardListener(QtCore.QThread):
    """
    Thread that listens for keyboard events using the 'keyboard' library.
    Emits 'brightness_changed' signal whenever Ctrl + Up or Ctrl + Down is pressed.
    """
    brightness_changed = QtCore.pyqtSignal(int)

    def run(self):
        keyboard.on_press(self.on_key_press)
        keyboard.wait()

    def on_key_press(self, event):
        """
        Handles key press events. If Ctrl + Up or Ctrl + Down is pressed, adjust the
        brightness of all monitors and emit the 'brightness_changed' signal.

        Args:
            event: The keyboard event.
        """
        if keyboard.is_pressed('ctrl'):
            for idx in list(monitor_brightness.keys()):
                try:
                    if keyboard.is_pressed('up'):
                        target_brightness = min(monitor_brightness[idx] + 10, 100)
                    elif keyboard.is_pressed('down'):
                        target_brightness = max(monitor_brightness[idx] - 10, 0)
                    else:
                        continue  # No relevant key pressed

                    # Validate target_brightness
                    if target_brightness < 0 or target_brightness > 100:
                        continue

                    if target_brightness != last_brightness.get(idx, -1):
                        ChangeBrightness(idx, target_brightness)
                        monitor_brightness[idx] = target_brightness
                        last_brightness[idx] = target_brightness
                        # Emit signal to update the slider
                        self.brightness_changed.emit(target_brightness)
                except Exception as e:
                    show_user_message("Error", f"Failed to adjust brightness for Monitor {idx+1}")


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """
    System Tray Icon with context menu.
    """
    def __init__(self, parent=None):
        sun_icon = create_sun_pixmap(32, 32)
        super().__init__(QtGui.QIcon(sun_icon), parent)
        
        self.setToolTip(APP_NAME)
        menu = QtWidgets.QMenu(parent)

        show_action = menu.addAction("Show")
        quit_action = menu.addAction("Exit")

        show_action.triggered.connect(parent.show_slider)
        quit_action.triggered.connect(QtWidgets.QApplication.quit)

        self.setContextMenu(menu)
        self.activated.connect(self.on_click)

    def on_click(self, reason):
        if reason == self.Trigger:
            self.parent().show_slider(INITIAL_BRIGHTNESS)
