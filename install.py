#!/usr/bin/env python3
"""
MES-Connect Installation Script
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    
    # List of required packages
    packages = [
        "streamlit==1.29.0",
        "pandas==2.1.4", 
        "plotly==5.18.0",
        "Pillow==10.1.0"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def create_structure():
    """Create necessary directories"""
    print("📁 Creating directory structure...")
    
    directories = [
        "data",
        "utils",
        "pages/Student",
        "pages/Alumni", 
        "pages/Admin"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created: {directory}/")
        except Exception as e:
            print(f"❌ Error creating {directory}: {e}")
    
    return True

def main():
    """Main installation function"""
    print("=" * 50)
    print("🎓 MES-CONNECT INSTALLATION")
    print("=" * 50)
    
    # Step 1: Create structure
    if not create_structure():
        print("❌ Failed to create directory structure")
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    print("\n" + "=" * 50)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 50)
    print("\nTo run the application:")
    print("1. First, create all the files from the provided code")
    print("2. Then run: streamlit run app.py")
    print("3. Open browser to: http://localhost:8501")
    print("\nDefault Admin Login:")
    print("👑 Username: mesadmin")
    print("🔑 Password: education")
    print("\nMade with ❤️ for MES College")

if __name__ == "__main__":
    main()
