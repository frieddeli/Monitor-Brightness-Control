# Monitor Brightness Control

A Windows system tray application for controlling monitor brightness across multiple displays. Features a modern Windows 11-style UI with smooth animations and global hotkeys. The goal is to produce a mininalistic brightness slider similar to the one found on windows laptops.

## Showcase 

![Light Mode](images/preview1.png)
![Dark Mode](images/preview2.png)

## Download

- EXE version provided under dist folder
- Clone to build fron source

## Features

✨ Modern floating slider UI with animations  
🎮 Global hotkeys (Ctrl + Up/Down)  
🖥️ Multi-monitor support (Including external monitors! )
🚀 Auto-starts with Windows  
🎯 System tray integration  
⚙️ DDC/CI monitor control
👆 Click to drag slider

## Usage

- System Tray:
  - Left click: Show brightness slider
  - Right click: Menu options
- Keyboard:
  - `Ctrl + ↑`: Increase brightness
  - `Ctrl + ↓`: Decrease brightness

## Requirements

- Windows 10/11
- DDC/CI compatible monitors
- Administrator privileges

### Technical Details
- Built with Python & PyQt5
- Uses DDC/CI protocol for monitor control
- Windows Registry integration for auto-start
- Smooth animations with QPropertyAnimation
- Efficient debounced brightness control

### Known Issues
- Could take up to 30 seconds to start again after a restart
- Some monitors may not support DDC/CI
- Reccommended to use HDMI as DP cables might face some issues 
- Requires admin privileges for first run
- May need manual startup addition on some systems

### License
- MIT License 