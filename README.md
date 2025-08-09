# 📄 CourtIQ – Delhi High Court Case Status Fetcher 🏛️

**CourtIQ** is a full-stack web application that fetches **real-time Delhi High Court case status** using Python, Flask, Selenium, and automated CAPTCHA bypass.

This tool was built as part of an internship project and demonstrates advanced automation in web scraping with real, working components—**no dummy logic, no paid APIs**.

---
##  Browser Compatibility Notice
CourtIQ’s scraping engine is currently optimized only for Mozilla Firefox.
The project will not work on Google Chrome or other browsers because the automation and CAPTCHA bypass logic relies on Firefox + Geckodriver.
For best performance, use the latest version of Firefox ESR (Extended Support Release).

## ✨ Features

✅ Fill case details (Type, Number, Year) via an intuitive form  
✅ Auto-bypass CAPTCHA using logic (no manual solving or paid APIs)  
✅ Scrape **real** case data from the official DHC website  
✅ Display results on a beautiful, responsive Flask web page  
✅ Download the case data as CSV or PDF  
✅ Store all results locally in a SQLite3 database  

---

## ⚙️ Tech Stack

- **Backend**: Python 3.13, Flask
- **Scraping Engine**: Selenium (with Firefox)
- **Database**: SQLite3
- **Frontend**: HTML5, Tailwind CSS
- **PDF Export**: FPDF
- **CSV Export**: Python CSV module

---

## 🧪 Tested Case Example

> Case Type: `W.P.(C)`  
> Case No: `1234`  
> Year: `2023`  

---

## 🔧 How It Works

1. User enters case details in the form
2. The Selenium engine auto-opens the Delhi High Court website
3. CAPTCHA is bypassed automatically (without using paid APIs)
4. Data is submitted and scraped from the real DHC response
5. Result is displayed on the web page + available for download
6. Case data is stored in a local database for future use

---

## 🖼️ Screenshots

### 📥 Case Input Form
![Input Form](screenshots/input-form.png)

### 🧾 Scraped Result Display
![Result Page](screenshots/result-page.png)

### 📊 CSV Download
![CSV Download](screenshots/csv-download.png)

### 📄 PDF Export
![PDF Export](screenshots/pdf-export.png)

> Add your actual screenshots inside a `screenshots/` folder for correct display on GitHub.

---

## 🚫 Disclaimer

- This project is for **educational and internship purposes only**
- It does **not use any paid CAPTCHA-solving services**
- You must **not misuse** this tool for scraping protected or sensitive data

---

