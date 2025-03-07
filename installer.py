import os
import sys
import winreg
import shutil
import ctypes
from PyQt5 import QtWidgets, QtCore

APP_NAME = "MonitorBrightnessApp"
INSTALL_DIR = os.path.join(os.environ["PROGRAMFILES"], APP_NAME)

class InstallerDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Brightness Installer")
        self.setFixedSize(400, 300)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Welcome message
        welcome_label = QtWidgets.QLabel("Welcome to the Monitor Brightness Control installer")
        welcome_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(welcome_label)
        
        description = QtWidgets.QLabel(
            "This installer will set up Monitor Brightness Control on your computer. "
            "It allows you to adjust your monitor brightness using keyboard shortcuts."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Installation options
        options_group = QtWidgets.QGroupBox("Installation Options")
        options_layout = QtWidgets.QVBoxLayout()
        
        self.install_dir_edit = QtWidgets.QLineEdit(INSTALL_DIR)
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(QtWidgets.QLabel("Install location:"))
        dir_layout.addWidget(self.install_dir_edit)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_install_location)
        dir_layout.addWidget(browse_button)
        options_layout.addLayout(dir_layout)
        
        # Auto-start option
        self.autostart_checkbox = QtWidgets.QCheckBox("Start automatically when Windows starts")
        self.autostart_checkbox.setChecked(True)
        options_layout.addWidget(self.autostart_checkbox)
        
        # Desktop shortcut option
        self.desktop_shortcut_checkbox = QtWidgets.QCheckBox("Create desktop shortcut")
        self.desktop_shortcut_checkbox.setChecked(True)
        options_layout.addWidget(self.desktop_shortcut_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.install_button = QtWidgets.QPushButton("Install")
        self.install_button.clicked.connect(self.install)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.install_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_install_location(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Installation Directory", self.install_dir_edit.text()
        )
        if dir_path:
            self.install_dir_edit.setText(dir_path)
    
    def install(self):
        # Check for admin rights
        if not ctypes.windll.shell32.IsUserAnAdmin():
            QtWidgets.QMessageBox.warning(
                self, "Administrator Rights Required",
                "This installer requires administrator rights. Please run as administrator."
            )
            return
        
        install_dir = self.install_dir_edit.text()
        
        # Create installation directory
        try:
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
                
            # Copy application files
            # In a real installer, you would copy all necessary files
            # For this example, we'll just show the concept
            src_dir = os.path.dirname(os.path.abspath(__file__))
            for file in ["monitor.py", "modules.py"]:
                shutil.copy(os.path.join(src_dir, file), os.path.join(install_dir, file))
            
            # Create executable (in a real installer, you might use PyInstaller output)
            exe_path = os.path.join(install_dir, "MonitorBrightness.exe")
            # Placeholder for actual executable creation
            with open(exe_path, "w") as f:
                f.write("# This would be the actual executable")
            
            # Add to startup if selected
            if self.autostart_checkbox.isChecked():
                self.add_to_startup(exe_path)
            
            # Create desktop shortcut if selected
            if self.desktop_shortcut_checkbox.isChecked():
                self.create_desktop_shortcut(exe_path)
            
            QtWidgets.QMessageBox.information(
                self, "Installation Complete",
                f"Monitor Brightness Control has been installed to {install_dir}"
            )
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Installation Failed",
                f"An error occurred during installation: {str(e)}"
            )
    
    def add_to_startup(self, exe_path):
        """Add the application to Windows startup"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Startup Registration Failed",
                f"Could not add to startup: {str(e)}"
            )
    
    def create_desktop_shortcut(self, exe_path):
        """Create a desktop shortcut for the application"""
        try:
            desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
            shortcut_path = os.path.join(desktop_path, f"{APP_NAME}.lnk")
            
            # In a real installer, you would use the Windows Script Host to create a proper .lnk file
            # For this example, we'll just create a simple batch file
            with open(shortcut_path + ".bat", "w") as f:
                f.write(f'@echo off\nstart "" "{exe_path}"')
                
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Shortcut Creation Failed",
                f"Could not create desktop shortcut: {str(e)}"
            )

def main():
    app = QtWidgets.QApplication(sys.argv)
    dialog = InstallerDialog()
    return dialog.exec_()

if __name__ == "__main__":
    sys.exit(main())
