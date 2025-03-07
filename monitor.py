import ctypes
import sys
import os
import logging
from PyQt5 import QtWidgets
from modules import (
    create_sun_pixmap,
    show_user_message,
    ensure_admin,
    RetrieveMonitors,
    ChangeBrightness,
    RetrieveBrightness,
    hide_console,
    BrightnessSlider,
    KeyboardListener,
    SystemTrayIcon,
    monitor_brightness,
    last_brightness,
    INITIAL_BRIGHTNESS,
    APP_NAME
)

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for the application.
    """
    try:
        hide_console()  # Hide console window
        ensure_admin()
        # add_to_startup() - Removed as this will be handled by the installer
        monitors = RetrieveMonitors()
        
        if not monitors:
            show_user_message("Error", "No compatible monitors detected.")
            return

        app = QtWidgets.QApplication(sys.argv)
        slider = BrightnessSlider()

        # Setup system tray icon using the correct class
        tray_icon = SystemTrayIcon(parent=slider)
        tray_icon.show()

        listener = KeyboardListener()
        listener.brightness_changed.connect(slider.show_slider)
        listener.start()

        sys.exit(app.exec_())
    except Exception as e:
        show_user_message("Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        show_user_message("Error", f"Application failed to start: {str(e)}")
        os.system("pause")
