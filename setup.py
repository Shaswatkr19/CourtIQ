#!/usr/bin/env python3
"""
Setup script for Delhi High Court Case Information Retrieval System
This script handles installation of dependencies and system setup
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def setup_tesseract():
    """Setup Tesseract OCR based on operating system"""
    system = platform.system().lower()
    
    print(f"🔧 Setting up Tesseract OCR for {system}...")
    
    if system == "windows":
        print("""
        📋 Windows Setup Instructions:
        1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
        2. Install to: C:\\Program Files\\Tesseract-OCR\\
        3. Add to PATH: C:\\Program Files\\Tesseract-OCR\\
        4. Restart your terminal/IDE
        """)
    
    elif system == "darwin":  # macOS
        try:
            subprocess.check_call(["brew", "install", "tesseract"])
            print("✅ Tesseract installed successfully via Homebrew!")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("""
            📋 macOS Setup Instructions:
            1. Install Homebrew: https://brew.sh/
            2. Run: brew install tesseract
            OR
            1. Download from: https://github.com/tesseract-ocr/tesseract
            2. Follow installation instructions
            """)
    
    elif system == "linux":
        try:
            # Try different package managers
            for cmd in [["apt-get", "install", "-y", "tesseract-ocr"], 
                       ["yum", "install", "-y", "tesseract"],
                       ["pacman", "-S", "tesseract"]]:
                try:
                    subprocess.check_call(["sudo"] + cmd)
                    print("✅ Tesseract installed successfully!")
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                print("""
                📋 Linux Setup Instructions:
                Ubuntu/Debian: sudo apt-get install tesseract-ocr
                CentOS/RHEL: sudo yum install tesseract
                Arch: sudo pacman -S tesseract
                """)
        except Exception as e:
            print(f"⚠️ Auto-installation failed: {e}")

def setup_chrome_driver():
    """Instructions for Chrome WebDriver setup"""
    print("""
    🌐 Chrome WebDriver Setup:
    
    Option 1 (Recommended - Automatic):
    - The script will automatically download ChromeDriver using webdriver-manager
    
    Option 2 (Manual):
    1. Download ChromeDriver from: https://chromedriver.chromium.org/
    2. Match your Chrome browser version
    3. Add to PATH or place in project directory
    
    ⚠️ Make sure Google Chrome is installed on your system!
    """)

def create_project_structure():
    """Create necessary project directories and files"""
    print("📁 Creating project structure...")
    
    directories = ['templates', 'static', 'downloads']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create templates/index.html if it doesn't exist
    if not os.path.exists('templates/index.html'):
        print("⚠️ templates/index.html not found!")
        print("📝 Please copy your HTML template to templates/index.html")

def test_installation():
    """Test if all components are properly installed"""
    print("\n🧪 Testing installation...")
    
    tests_passed = 0
    total_tests = 4
    
    # Test Python imports
    try:
        import flask
        import selenium
        import pytesseract
        import PIL
        import cv2
        print("✅ Python packages imported successfully")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ Python package import failed: {e}")
    
    # Test Tesseract
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
    
    # Test Selenium WebDriver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("✅ Chrome WebDriver is working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ WebDriver test failed: {e}")
    
    # Test file structure
    if os.path.exists('templates') and os.path.exists('app.py') and os.path.exists('engine.py'):
        print("✅ Project structure is correct")
        tests_passed += 1
    else:
        print("❌ Project structure incomplete")
    
    print(f"\n📊 Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Installation completed successfully!")
        print("\n🚀 To run the application:")
        print("   python app.py")
        print("\n🌐 Then open: http://localhost:5000")
    else:
        print("⚠️ Some components need attention. Check the errors above.")

def main():
    """Main setup function"""
    print("🏛️ Delhi High Court Case Information Retrieval System")
    print("=" * 60)
    print("🔧 Setting up your development environment...\n")
    
    # Create project structure
    create_project_structure()
    
    # Install Python dependencies
    if not install_requirements():
        print("❌ Setup failed at Python dependencies")
        return
    
    # Setup Tesseract
    setup_tesseract()
    
    # Setup Chrome WebDriver info
    setup_chrome_driver()
    
    # Test installation
    test_installation()
    
    print("\n" + "=" * 60)
    print("📚 Additional Notes:")
    print("- This is for educational purposes only")
    print("- Respect the website's terms of service")
    print("- CAPTCHA solving may be 100% accurate")
    print("- Consider website load and rate limiting")
    print("=" * 60)

if __name__ == "__main__":
    main()