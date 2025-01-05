import keyboard
import time
import logging
from monitorcontrol import get_monitors
from modules import * # import all functions from modules.py


#create a dictionary of each monitor and its brightness
#this ensures that the number of monitors that can be controlled is scalable and not limited to a fixed number of monitors
monitor_brightness = {} # init a dict to hold the values 


#define a function to poll the brightness of each monitor
def RetrieveBrightness():
    for monitor in get_monitors():
        print(f"Monitor: {monitor}")
        with monitor:  # Open a context for the monitor
            try:
                # Get the current brightness level
                brightness = monitor.get_luminance()
                print(f"  Current Brightness: {brightness}")
                #round the brightness to the nearest 10
                brightness = round(brightness, -1)
                monitor_brightness[monitor] = brightness # add the monitor and its brightness to the dictionary
        
            except Exception as e:
                print(f"  Error interacting with monitor: {e}")
                
                
#poll the keyboard for keypresses of the hotkey

def RetrieveKeyboard():
    try:
        #increase brightness 
        if keyboard.is_pressed('page up'):
            print("Hotkey pressed up")
            
            for monitor in monitor_brightness:
                TargetBrightness = monitor_brightness[monitor] + 10
                
                if TargetBrightness > 100:
                    print("  Maximum brightness reached")
                    TargetBrightness = 100
                    continue
          
                ChangeBrightness(monitor, TargetBrightness) # increase the brightness by 10
                monitor_brightness[monitor] += 10
            time.sleep(0.1)
            return 
        #decrease brightness
        if keyboard.is_pressed('page down'):
            print("Hotkey pressed down")
            
            #sanity check for the brightness level
            for monitor in monitor_brightness:
                
                TargetBrightness = monitor_brightness[monitor] - 10
                
                if TargetBrightness < 0:
                    print("  Monitor brightness too low")
                    TargetBrightness = 0
                    continue
            
                ChangeBrightness(monitor, TargetBrightness) # decrease the brightness by 10
                monitor_brightness[monitor] -= 10
            time.sleep(0.1)
            return
            
    except Exception as e:
        print(f"Error polling keyboard: {e}")
        return
    time.sleep(0.1)

                    
                    

# SHOW monitors
print(f"Detected monitors: {RetrieveMonitors()}")



#main loop
while True:
    RetrieveBrightness()
    RetrieveKeyboard()
    time.sleep(0.5)

