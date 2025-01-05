import keyboard
import time
import logging
from monitorcontrol import get_monitors
from modules import * # import all functions from modules.py


#create a dictionary of each monitor and its brightness
#this ensures that the number of monitors that can be controlled is scalable and not limited to a fixed number of monitors
monitor_brightness = {} # init a dict to hold the values 




# SHOW monitors
print(f"Detected monitors: {RetrieveMonitors()}")

for monitor in get_monitors():
    print(f"Monitor: {monitor}")
    with monitor:  # Open a context for the monitor
        try:
            # Get the current brightness level
            brightness = monitor.get_luminance()
            print(f"  Current Brightness: {brightness}")
            monitor_brightness[monitor] = brightness # add the monitor and its brightness to the dictionary
    
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")\
                
                
#poll the keyboard for keypresses of the hotkey
while True:
    try:
        #increase brightness 
        if keyboard.is_pressed('crtl+arrow-up'):
            print("Hotkey pressed")
            for monitor in monitor_brightness:
                ChangeBrightness(monitor, monitor_brightness[monitor]+10) # increase the brightness by 10
            time.sleep(1)
        #decrease brightness
        if keyboard.is_pressed('function+arrow-down'):
            print("Hotkey pressed")
            for monitor in monitor_brightness:
                ChangeBrightness(monitor, monitor_brightness[monitor]-10) # decrease the brightness by 10
            time.sleep(1)
            
    except Exception as e:
        print(f"Error polling keyboard: {e}")
        break
    time.sleep(0.1)


