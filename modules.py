import keyboard
import time
import logging
from monitorcontrol import get_monitors




#function to retrieve the monitors connected to the computer
def RetrieveMonitors():
    monitors = get_monitors()
    print(f"Detected monitors: {monitors}")
    return monitors

#function to change the brightness of a monitor
def ChangeBrightness(monitor, brightness):
    with monitor:
    #query the user for the desired brightness level
        try:
            monitor.set_luminance(brightness)
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")
    print(f"  Set brightness to: {brightness}")

                
