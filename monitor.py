import keyboard
import time
import ctypes, sys
from monitorcontrol import get_monitors

# create a dictionary of each monitor and its brightness
# ensures that the number of monitors that can be controlled is scalable and not limited to a fixed number of monitors
monitor_brightness = {}  # init a dict to hold the values
last_brightness = {}      # init a dict to hold the last brightness values

def ensure_admin():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    if not is_admin:
        # Relaunch with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def RetrieveMonitors():
    monitors = get_monitors()
    print(f"Detected monitors: {monitors}")
    return monitors


def ChangeBrightness(monitor, brightness):
    with monitor:
        try:
            monitor.set_luminance(brightness)
        except Exception as e:
            print(f"  Error interacting with monitor: {e}")
    print(f"  Set brightness to: {brightness}")


def RetrieveBrightness():
    for monitor in get_monitors():
        print(f"Monitor: {monitor}")
        with monitor:
            try:
                # Get the current brightness level
                brightness = monitor.get_luminance()
                print(f"  Current Brightness: {brightness}")
                # round the brightness to the nearest 10
                brightness = round(brightness, -1)
                monitor_brightness[monitor] = brightness
                last_brightness[monitor] = brightness
            except Exception as e:
                print(f"  Error interacting with monitor: {e}")
                print(f"  Invalid return value: {e.args}")
                if hasattr(e, 'response'):
                    print(f"  Raw response: {e.response}")


def on_key_press(event):
    if event.name == 'page up':
        # increase brightness
        for monitor in monitor_brightness:
            TargetBrightness = min(monitor_brightness[monitor] + 5, 100)
            if TargetBrightness != last_brightness.get(monitor, -1):
                ChangeBrightness(monitor, TargetBrightness)
                monitor_brightness[monitor] = TargetBrightness
                last_brightness[monitor] = TargetBrightness
    elif event.name == 'page down':
        # decrease brightness
        for monitor in monitor_brightness:
            TargetBrightness = max(monitor_brightness[monitor] - 5, 0)
            if TargetBrightness != last_brightness.get(monitor, -1):
                ChangeBrightness(monitor, TargetBrightness)
                monitor_brightness[monitor] = TargetBrightness
                last_brightness[monitor] = TargetBrightness


# main loop
ensure_admin()

keyboard.on_press(on_key_press)


print(f"Detected monitors: {RetrieveMonitors()}")

RetrieveBrightness()  # Get the initial brightness values

while True:
    time.sleep(1)  # Reduced frequency