import keyboard
import time
import logging
from monitorcontrol import get_monitors

#create a dictionary of each monitor and its brightness


# Retrieve monitors
monitors = get_monitors()
print(f"Detected monitors: {monitors}")

for monitor in monitors:
    print(f"Monitor: {monitor}")
    with monitor:  # Open a context for the monitor
        try:
            # Get the current brightness level
            brightness = monitor.get_luminance()
            print(f"  Current Brightness: {brightness}")
    
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")