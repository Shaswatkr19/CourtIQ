# 🚀 Complete Installation & Usage Guide

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.7+** installed
- [ ] **Google Chrome** browser installed  
- [ ] **Internet connection** for scraping
- [ ] **Command line access** (Terminal/CMD)

## 🛠️ Step-by-Step Installation

### 1. Create Project Directory

```bash
# Create and enter project directory
mkdir delhi-court-scraper
cd delhi-court-scraper
```

### 2. Create Python Files

Create the following files with the provided code:

**File: `app.py`**
```python
# Copy the complete Flask application code from the app.py artifact
```

**File: `engine.py`**  
```python
# Copy the complete scraping engine code from the engine.py artifact
```

**File: `requirements.txt`**
```text
# Copy the dependencies list from requirements.txt artifact
```

**File: `setup.py`**
```python
# Copy the setup script from setup.py artifact
```

### 3. Create Templates Directory

```bash
# Create templates folder
mkdir templates

# Create templates/index.html with the provided HTML code
```

### 4. Install Dependencies

#### Option A: Automatic Setup (Recommended)
```bash
python setup.py
```

#### Option B: Manual Installation

**Install Python packages:**
```bash
pip install -r requirements.txt
```

**Install Tesseract OCR:**

**Windows:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. Add to PATH: `C:\Program Files\Tesseract-OCR\`

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Chrome WebDriver:**
- Will be automatically downloaded by webdriver-manager
- Or manually download from: https://chromedriver.chromium.org/

### 5. Test Installation

```bash
python engine.py  # Test scraping engine
python app.py     # Start Flask application
```

## 🎯 Usage Instructions

### Starting the Application

1. **Open Terminal/Command Prompt**
2. **Navigate to project directory:**
   ```bash
   cd delhi-court-scraper
   ```
3. **Start Flask server:**
   ```bash
   python app.py
   ```
4. **Open browser and visit:** `http://localhost:5000`

### Using the Web Interface

1. **Fill Search Form:**
   - **Case Type:** Select from dropdown (e.g., W.P.(C))
   - **Case Number:** Enter numeric value (e.g., 1234)
   - **Filing Year:** Select year (2010-2024)

2. **Submit Search:**
   - Click "Search Case Information"
   - Wait for automatic processing (30-60 seconds)

3. **View Results:**
   - Case information displays automatically
   - Download CSV/PDF reports if needed

### Expected Process Flow

```
User submits form → Flask receives data → Background thread starts
→ Selenium opens Delhi High Court website → Form auto-filled
→ CAPTCHA automatically solved using OCR → Form submitted
→ Results extracted → Data saved to CSV/PDF → Results displayed
```

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError
pip install -r requirements.txt --upgrade
```

#### 2. Tesseract Not Found
```bash
# Windows: Add to PATH or set environment variable
# Linux/Mac: sudo apt-get install tesseract-ocr
```

#### 3. WebDriver Issues
```bash
# Update Chrome browser
# Clear webdriver cache: 
rm -rf ~/.wdm/  # Linux/Mac
rmdir /s %USERPROFILE%\.wdm  # Windows
```

#### 4. CAPTCHA Recognition Fails
- **Normal behavior** - OCR success rate is 70-80%
- Try multiple times with different case numbers
- Check Tesseract installation

#### 5. Website Access Issues
- Verify internet connection
- Check if Delhi High Court website is accessible
- Try different case numbers (some may not exist)

### Debug Mode

For detailed error information:

```bash
# Run with debug output
python app.py  # Flask debug mode is already enabled

# For engine debugging
python engine.py  # Test standalone scraping
```

#### 6. Port Already in Use
```bash
# If port 5000 is busy, change in app.py:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

## 📁 Complete Project Structure

After setup, your folder should look like this:

```
delhi-court-scraper/
├── app.py                    # Main Flask application
├── engine.py                 # Web scraping engine  
├── requirements.txt          # Python dependencies
├── setup.py                  # Installation script
├── INSTALLATION_GUIDE.md     # This file (setup instructions)
├── README.md                 # Project documentation
├── templates/
│   └── index.html           # Web interface template
├── static/                  # Auto-created for static files
├── downloads/               # Auto-created for reports
├── case_data.csv           # Generated CSV reports
└── case_data.pdf           # Generated PDF reports
```

## 🔐 Security Configuration

The Flask secret key is currently set to a placeholder. For production use:

1. **Generate a secure secret key:**
```python
import secrets
print(secrets.token_hex(32))  # Generates random secure key
```

2. **Update in app.py:**
```python
app.secret_key = 'your-generated-secret-key-here'
```

## 📝 Quick Start Commands

```bash
# 1. Create project
mkdir delhi-court-scraper && cd delhi-court-scraper

# 2. Create all files (copy the provided code)

# 3. Install dependencies  
python setup.py

# 4. Run application
python app.py

# 5. Open browser
# Visit: http://localhost:5000
```

## 🎯 Test Cases

Try these sample searches to test functionality:

| Case Type | Number | Year | Expected |
|-----------|--------|------|----------|
| W.P.(C) | 1234 | 2023 | May exist or show "not found" |
| CRL.M.C. | 5678 | 2022 | Test different case type |
| FAO | 999 | 2021 | Test another format |

## 📞 Support

If you encounter issues:
1. Check all files are created correctly
2. Verify all dependencies installed
3. Test internet connection
4. Try different case numbers

Remember: This is for educational purposes only! 🎓