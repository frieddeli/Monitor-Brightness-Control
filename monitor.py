import keyboard
import time
import logging
from monitorcontrol import get_monitors
from modules import * # import all functions from modules.py


#setup code 


#create a dictionary of each monitor and its brightness
#this ensures that the number of monitors that can be controlled is scalable and not limited to a fixed number of monitors
monitor_brightness = {} # init a dict to hold the values 




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
            monitor_brightness[monitor] = brightness # add the monitor and its brightness to the dictionary
    
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")\
                
                
print(f"Monitor Brightness: {monitor_brightness}")


