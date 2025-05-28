#!/usr/bin/env python3
"""
SS6 Game Installation Script
Installs necessary dependencies and sets up the game environment.
"""

import subprocess
import sys
import os
import platform

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 6):
        print("❌ Error: Python 3.6 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_package(package_name):
    """Install a package using pip."""
    try:
        print(f"📦 Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def check_package_installed(package_name):
    """Check if a package is already installed."""
    try:
        __import__(package_name)
        print(f"✅ {package_name} is already installed")
        return True
    except ImportError:
        print(f"📦 {package_name} not found, will install...")
        return False

def create_play_script():
    """Create the play script in the same directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the correct script extension and shebang based on OS
    if platform.system() == "Windows":
        play_script_name = "Play.bat"
        script_content = f'''@echo off
cd /d "{script_dir}"
python SS6.origional.py
pause
'''
    else:
        play_script_name = "Play.sh"
        script_content = f'''#!/bin/bash
cd "{script_dir}"
python3 SS6.origional.py
'''
    
    play_script_path = os.path.join(script_dir, play_script_name)
    
    try:
        with open(play_script_path, 'w') as f:
            f.write(script_content)
        
        # Make the script executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(play_script_path, 0o755)
        
        print(f"✅ Play script created: {play_script_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create play script: {e}")
        return False

def verify_game_files():
    """Verify that essential game files exist."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "SS6.origional.py",
        "settings.py",
        "universal_class.py",
        "welcome_screen.py"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(script_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    # Check for required directories
    required_dirs = ["levels", "utils"]
    for dir_name in required_dirs:
        dir_path = os.path.join(script_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"❌ Missing required directory: {dir_name}")
            return False
        else:
            print(f"✅ Found directory: {dir_name}")
    
    return True

def main():
    """Main installation function."""
    print("🎮 SS6 Game Installation")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return False
    
    # Verify game files
    print("\n📁 Checking game files...")
    if not verify_game_files():
        print("\n❌ Installation failed: Missing required game files.")
        input("Press Enter to exit...")
        return False
    
    # Check and install pygame
    print("\n📦 Checking dependencies...")
    if not check_package_installed("pygame"):
        if not install_package("pygame"):
            print("\n❌ Installation failed: Could not install pygame.")
            input("Press Enter to exit...")
            return False
    
    # Create play script
    print("\n🎯 Creating play script...")
    if not create_play_script():
        print("\n❌ Installation failed: Could not create play script.")
        input("Press Enter to exit...")
        return False
    
    # Final verification
    print("\n🔍 Final verification...")
    try:
        import pygame
        print("✅ pygame import test successful")
    except ImportError as e:
        print(f"❌ pygame import test failed: {e}")
        input("Press Enter to exit...")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Installation completed successfully!")
    print("\nTo play the game:")
    if platform.system() == "Windows":
        print("  - Double-click 'Play.bat'")
        print("  - Or run: python SS6.origional.py")
    else:
        print("  - Run: ./Play.sh")
        print("  - Or run: python3 SS6.origional.py")
    
    print("\nGame Controls:")
    print("  - Mouse/Touch: Click targets")
    print("  - ESC: Exit game")
    print("  - Space: Switch abilities (in some modes)")
    print("=" * 40)
    
    # Rename the installer to indicate completion
    try:
        current_script = os.path.abspath(__file__)
        script_dir = os.path.dirname(current_script)
        done_script = os.path.join(script_dir, "done.py")
        
        print("\n📝 Marking installation as complete...")
        os.rename(current_script, done_script)
        print("✅ Installation file renamed to 'done.py'")
        print("   (You can delete this file if you want)")
    except Exception as e:
        print(f"⚠️  Could not rename installer: {e}")
        print("   (Installation was still successful)")
    
    input("Press Enter to exit installer...")
    return True

if __name__ == "__main__":
    main() 