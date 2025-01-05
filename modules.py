import keyboard
import time
import logging
from monitorcontrol import get_monitors




#function to change the brightness of a monitor
def ChangeBrightness(monitor, brightness):
    with monitor:
    #query the user for the desired brightness level
        brightness = input(f"Enter the desired brightness level (0-100) for monitor {monitor}: ")
        brightness = int(brightness)
        try:
            monitor.set_luminance(brightness)
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")
    print(f"  Set brightness to: {brightness}")

