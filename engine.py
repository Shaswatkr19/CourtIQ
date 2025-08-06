from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import pandas as pd
from datetime import datetime
import geckodriver_autoinstaller
import requests
from PIL import Image
import io
import base64

class DelhiHighCourtScraper:
    def __init__(self, headless=False, timeout=45):
        self.timeout = timeout
        self.base_url = "https://delhihighcourt.nic.in/app/get-case-type-status"
        self.driver = None
        self.wait = None
        self.case_data = {}
        
        # Auto-install geckodriver if not found
        try:
            geckodriver_autoinstaller.install()
        except:
            print("⚠️ Geckodriver auto-install failed, assuming it's already installed")
    
    def setup_driver(self, headless=False):
        """Initialize Firefox WebDriver with proper configuration"""
        try:
            firefox_options = Options()
            if headless:
                firefox_options.add_argument("--headless")
            
            # Firefox specific options for better performance
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            firefox_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Set preferences for better stability and captcha handling
            firefox_options.set_preference("network.http.connection-timeout", 60)
            firefox_options.set_preference("network.http.response.timeout", 60)
            firefox_options.set_preference("dom.max_script_run_time", 60)
            firefox_options.set_preference("browser.download.folderList", 2)
            firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
            firefox_options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
            
            self.driver = webdriver.Firefox(options=firefox_options)
            self.driver.set_page_load_timeout(self.timeout)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            print("🦊 Firefox WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Firefox WebDriver: {e}")
            print("📝 Make sure Firefox is installed and geckodriver is available")
            return False
    
    def navigate_to_site(self, max_retries=3):
        """Navigate to Delhi High Court new URL with retry mechanism"""
        for attempt in range(max_retries):
            try:
                print(f"🌐 Loading Delhi High Court (Attempt {attempt + 1}/{max_retries})...")
                print(f"🔗 URL: {self.base_url}")
                
                self.driver.get(self.base_url)
                
                # Wait for page to be ready
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                
                # Wait for main content to load
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                print("📄 Page loaded successfully")
                time.sleep(5)  # Additional wait for dynamic content and scripts
                
                # Print current page title and URL for debugging
                print(f"📋 Page Title: {self.driver.title}")
                print(f"🔗 Current URL: {self.driver.current_url}")
                
                return True
                
            except TimeoutException:
                print(f"⏰ Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    print("🔄 Retrying...")
                    time.sleep(5)
                else:
                    print("❌ Failed to load page after all retries")
                    return False
            except Exception as e:
                print(f"❌ Navigation error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return False
        return False
    
    def debug_page_elements(self):
        """Debug function to print all form elements"""
        try:
            print("🔍 Debugging page elements...")
            
            # Find all input elements
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"📝 Found {len(inputs)} input elements:")
            for i, inp in enumerate(inputs):
                try:
                    print(f"  {i+1}. Type: {inp.get_attribute('type')}, Name: {inp.get_attribute('name')}, ID: {inp.get_attribute('id')}, Placeholder: {inp.get_attribute('placeholder')}")
                except:
                    pass
            
            # Find all select elements
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            print(f"📋 Found {len(selects)} select elements:")
            for i, sel in enumerate(selects):
                try:
                    print(f"  {i+1}. Name: {sel.get_attribute('name')}, ID: {sel.get_attribute('id')}")
                    options = sel.find_elements(By.TAG_NAME, "option")
                    print(f"     Options: {[opt.text for opt in options[:5]]}")  # First 5 options
                except:
                    pass
            
            # Find all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"🔘 Found {len(buttons)} button elements:")
            for i, btn in enumerate(buttons):
                try:
                    print(f"  {i+1}. Text: '{btn.text}', Type: {btn.get_attribute('type')}, ID: {btn.get_attribute('id')}")
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
    
    def wait_for_element(self, locator, timeout=15):
        """Wait for element with custom timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            print(f"⏰ Element not found within {timeout} seconds: {locator}")
            return None
    
    def safe_click(self, element, max_retries=3):
        """Safely click element with retries"""
        for attempt in range(max_retries):
            try:
                # Scroll to element first
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                
                # Try different click methods
                try:
                    # Method 1: Regular click
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
                    element.click()
                    return True
                except:
                    # Method 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                    
            except Exception as e:
                print(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return False
    
    def solve_captcha_bypass(self):
        """Bypass captcha by reading the displayed value from span element"""
        try:
            print("🔐 Attempting to bypass captcha...")
            
            # Look for the captcha code span element using the exact path you provided
            captcha_code_selectors = [
                (By.ID, "captcha-code"),  # Direct ID
                (By.XPATH, "/html/body/div[3]/div/div/div/div/div/div/div[2]/div[1]/div/label/span"),  # Full path
                (By.CLASS_NAME, "captcha-code"),  # Class name
                (By.XPATH, "//span[@id='captcha-code']"),  # XPath with ID
                (By.XPATH, "//span[contains(@class, 'captcha-code')]"),  # XPath with class
                (By.XPATH, "//span[contains(@id, 'captcha')]"),  # Any span with captcha in ID
            ]
            
            captcha_code = None
            captcha_span = None
            
            # Try to find the captcha code span
            for selector in captcha_code_selectors:
                try:
                    captcha_span = self.driver.find_element(*selector)
                    if captcha_span and captcha_span.is_displayed():
                        captcha_code = captcha_span.text.strip()
                        print(f"✅ Found captcha code using {selector}: '{captcha_code}'")
                        break
                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue
            
            if not captcha_code:
                print("❌ Could not find captcha code span element")
                return False
            
            # Now find the captcha input field to enter the code
            captcha_input_selectors = [
                (By.NAME, "captcha"),
                (By.ID, "captcha"),
                (By.NAME, "captchaInput"),
                (By.ID, "captchaInput"),
                (By.NAME, "captcha_code"),
                (By.ID, "captcha_code"),
                (By.XPATH, "//input[contains(@name, 'captcha')]"),
                (By.XPATH, "//input[contains(@id, 'captcha')]"),
                (By.XPATH, "//input[contains(@placeholder, 'captcha')]"),
                (By.XPATH, "//input[@type='text'][last()]"),  # Often the last text input
            ]
            
            captcha_input_found = False
            
            for selector in captcha_input_selectors:
                try:
                    captcha_input = self.driver.find_element(*selector)
                    if captcha_input and captcha_input.is_displayed() and captcha_input.is_enabled():
                        # Clear and enter the captcha code
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_code)
                        print(f"✅ Captcha filled successfully with: '{captcha_code}'")
                        captcha_input_found = True
                        time.sleep(1)  # Small delay after filling
                        break
                except Exception as e:
                    print(f"⚠️ Input selector {selector} failed: {e}")
                    continue
            
            if not captcha_input_found:
                print("❌ Could not find captcha input field")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Captcha bypass error: {e}")
            return False
    
    def auto_fill_case_details(self, case_type, case_number, filing_year):
        """Auto-fill case search form with FIXED year selection"""
        try:
            print("📝 Auto-filling case details...")
            time.sleep(3)  # Wait for form to be ready
            
            # Debug page elements first
            self.debug_page_elements()
            
            # Fill Case Type - Try multiple approaches
            print("🔍 Filling Case Type...")
            case_type_selectors = [
                (By.NAME, "case_type"),
                (By.ID, "case_type"),
                (By.NAME, "caseType"),
                (By.ID, "caseType"),
                (By.XPATH, "//select[contains(@class, 'case')]"),
                (By.XPATH, "//select[contains(@name, 'type')]"),
                (By.XPATH, "//select[position()=1]"),  # First select element
                (By.XPATH, "//input[contains(@name, 'type')]"),
                (By.XPATH, "//select[@aria-label='Case Type']")
            ]
            
            case_type_filled = False
            for selector in case_type_selectors:
                try:
                    element = self.wait_for_element(selector, 5)
                    if element:
                        if element.tag_name.lower() == "select":
                            select = Select(element)
                            print(f"📋 Available options: {[opt.text for opt in select.options[:10]]}")
                            # Try different ways to select
                            try:
                                select.select_by_visible_text(case_type)
                                print(f"✅ Case type selected by text: {case_type}")
                            except:
                                try:
                                    select.select_by_value(case_type)
                                    print(f"✅ Case type selected by value: {case_type}")
                                except:
                                    # Try partial match
                                    for option in select.options:
                                        if case_type.upper() in option.text.upper():
                                            select.select_by_visible_text(option.text)
                                            print(f"✅ Case type selected by partial match: {option.text}")
                                            break
                        else:
                            element.clear()
                            element.send_keys(case_type)
                            print(f"✅ Case type entered in input: {case_type}")
                        
                        case_type_filled = True
                        break
                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue
            
            if not case_type_filled:
                print("❌ Could not fill case type field")
            
            # Fill Case Number
            print("🔢 Filling Case Number...")
            case_number_selectors = [
                (By.NAME, "case_number"),
                (By.ID, "case_number"),
                (By.NAME, "caseNumber"),
                (By.ID, "caseNumber"),
                (By.NAME, "case_no"),
                (By.ID, "case_no"),
                (By.XPATH, "//input[contains(@name, 'number')]"),
                (By.XPATH, "//input[contains(@placeholder, 'number')]"),
                (By.XPATH, "//input[@type='number']"),
                (By.XPATH, "//input[@type='text'][1]")  # First text input
            ]
            
            case_number_filled = False
            for selector in case_number_selectors:
                try:
                    element = self.wait_for_element(selector, 5)
                    if element:
                        element.clear()
                        element.send_keys(str(case_number))
                        print(f"✅ Case number filled: {case_number}")
                        case_number_filled = True
                        break
                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue
            
            if not case_number_filled:
                print("❌ Could not fill case number field")
            
            # Fill Filing Year - FIXED with exact selectors
            print("📅 Filling Filing Year...")
            year_selectors = [
                (By.NAME, "case_year"),  # Exact name from HTML
                (By.ID, "case_year"),    # Exact ID from HTML
                (By.XPATH, "/html/body/div[3]/div/div/div/div/div/div/div[1]/div[3]/div/select"),  # Full path
                (By.XPATH, "//select[@name='case_year']"),  # XPath with name
                (By.XPATH, "//select[@id='case_year']"),    # XPath with ID
                (By.XPATH, "//select[contains(@name, 'year')]"),
                (By.XPATH, "//select[contains(@id, 'year')]"),
                (By.XPATH, "//select[position()=2]"),  # Second select element (often year)
                (By.XPATH, "//select[last()]"),  # Last select element
            ]
            
            year_filled = False
            for selector in year_selectors:
                try:
                    element = self.wait_for_element(selector, 5)
                    if element and element.tag_name.lower() == "select":
                        select = Select(element)
                        print(f"📋 Year options available: {len(select.options)} options")
                        print(f"📋 First few year options: {[opt.text for opt in select.options[:5]]}")
                        
                        # Try different methods to select the year
                        try:
                            # Method 1: Select by value (most reliable)
                            select.select_by_value(str(filing_year))
                            print(f"✅ Year selected by value: {filing_year}")
                            year_filled = True
                            break
                        except Exception as e1:
                            print(f"⚠️ Select by value failed: {e1}")
                            try:
                                # Method 2: Select by visible text
                                select.select_by_visible_text(str(filing_year))
                                print(f"✅ Year selected by text: {filing_year}")
                                year_filled = True
                                break
                            except Exception as e2:
                                print(f"⚠️ Select by text failed: {e2}")
                                try:
                                    # Method 3: Find option and click directly
                                    year_option = element.find_element(By.XPATH, f"//option[@value='{filing_year}']")
                                    year_option.click()
                                    print(f"✅ Year selected by direct click: {filing_year}")
                                    year_filled = True
                                    break
                                except Exception as e3:
                                    print(f"⚠️ Direct click failed: {e3}")
                                    try:
                                        # Method 4: JavaScript selection
                                        self.driver.execute_script(f"arguments[0].value = '{filing_year}';", element)
                                        self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", element)
                                        print(f"✅ Year selected by JavaScript: {filing_year}")
                                        year_filled = True
                                        break
                                    except Exception as e4:
                                        print(f"⚠️ JavaScript selection failed: {e4}")
                                        continue
                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue
            
            if not year_filled:
                print("❌ Could not fill filing year field - trying manual approach")
                # Last resort - try to find any select and check if it has years
                try:
                    all_selects = self.driver.find_elements(By.TAG_NAME, "select")
                    for i, select_elem in enumerate(all_selects):
                        try:
                            select_obj = Select(select_elem)
                            option_texts = [opt.text for opt in select_obj.options]
                            if str(filing_year) in option_texts:
                                select_obj.select_by_visible_text(str(filing_year))
                                print(f"✅ Year selected from select #{i+1}: {filing_year}")
                                year_filled = True
                                break
                        except:
                            continue
                except:
                    pass
            
            # Handle captcha with bypass
            print("🔐 Handling captcha...")
            if not self.solve_captcha_bypass():
                print("⚠️ Captcha bypass failed, but continuing...")
            
            time.sleep(2)  # Wait after filling form
            return True
            
        except Exception as e:
            print(f"❌ Error in auto-fill: {e}")
            return False
    
    def search_cases(self):
        """Submit search form with enhanced button detection and wait for results"""
        try:
            print("🔍 Searching for cases...")
            
            # Enhanced search button selectors
            search_selectors = [
                # Specific ID that we found in logs
                (By.ID, "search"),
                (By.XPATH, "//button[@id='search']"),
                
                # Common button texts
                (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]"),
                (By.XPATH, "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]"),
                (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]"),
                (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get status')]"),
                (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'check')]"),
                
                # Standard form selectors
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
                (By.NAME, "submit"),
                (By.CLASS_NAME, "btn-search"),
                (By.CLASS_NAME, "search"),
                (By.CLASS_NAME, "submit"),
                (By.XPATH, "//button[contains(@class, 'search')]"),
                (By.XPATH, "//button[contains(@class, 'submit')]"),
                (By.XPATH, "//input[contains(@class, 'search')]"),
                (By.XPATH, "//input[contains(@class, 'submit')]"),
                
                # Fallback - any button or submit input
                (By.XPATH, "//button[position()=1]"),  # First button
                (By.XPATH, "//button[last()]"),  # Last button
                (By.XPATH, "//input[@type='submit'][position()=1]")  # First submit input
            ]
            
            search_clicked = False
            
            for i, selector in enumerate(search_selectors):
                try:
                    search_btn = self.wait_for_element(selector, 3)
                    if search_btn and search_btn.is_displayed() and search_btn.is_enabled():
                        print(f"🎯 Found search button using selector {i+1}: {selector}")
                        print(f"Button text: '{search_btn.text}', Type: {search_btn.get_attribute('type')}")
                        
                        if self.safe_click(search_btn):
                            print("🔍 Search button clicked successfully")
                            search_clicked = True
                            break
                        else:
                            print("⚠️ Click failed, trying next selector...")
                except Exception as e:
                    print(f"⚠️ Selector {i+1} failed: {e}")
                    continue
            
            if not search_clicked:
                # If no search button found, try submitting form directly
                try:
                    print("🔄 Trying to submit form using Enter key...")
                    form = self.driver.find_element(By.TAG_NAME, "form")
                    form.submit()
                    print("🔍 Form submitted using form.submit()")
                    search_clicked = True
                except:
                    pass
            
            if not search_clicked:
                # Last resort - try pressing Enter on active element
                try:
                    print("🔄 Trying Enter key on active element...")
                    ActionChains(self.driver).send_keys(Keys.RETURN).perform()
                    print("🔍 Enter key pressed")
                    search_clicked = True
                except:
                    pass
            
            if not search_clicked:
                print("❌ Could not find or click search button")
                return False
            
            # Wait for results - Enhanced waiting
            print("⏳ Waiting for results to load...")
            time.sleep(10)  # Initial wait
            
            # Check if URL changed (indicates successful submission)
            current_url = self.driver.current_url
            print(f"📋 Current URL after search: {current_url}")
            
            # Check for loading indicators
            loading_selectors = [
                (By.XPATH, "//*[contains(text(), 'Loading')]"),
                (By.XPATH, "//*[contains(text(), 'Please wait')]"),
                (By.CLASS_NAME, "loading"),
                (By.ID, "loading")
            ]
            
            # Wait for loading to complete
            for selector in loading_selectors:
                try:
                    loading_element = self.driver.find_element(*selector)
                    if loading_element.is_displayed():
                        print("⏳ Waiting for loading to complete...")
                        WebDriverWait(self.driver, 30).until(
                            EC.invisibility_of_element(loading_element)
                        )
                        break
                except:
                    continue
            
            # Additional wait for results
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ Error in search: {e}")
            return False
    
    def extract_case_information(self):
        """Extract comprehensive case information from results page - Enhanced"""
        try:
            print("📊 Extracting case information...")
            time.sleep(5)  # Wait for results to load completely
            
            # Check current URL and page title for debugging
            print(f"📋 Current URL: {self.driver.current_url}")
            print(f"📋 Page Title: {self.driver.title}")
            
            # Take a screenshot for debugging
            try:
                self.driver.save_screenshot("current_page.png")
                print("📸 Screenshot saved as current_page.png")
            except:
                pass
            
            # Get page source and body text
            page_source = self.driver.page_source
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            print(f"📄 Page content preview: {body_text[:300]}...")
            
            # Initialize case data structure
            case_info = {
                'status': 'Success',
                'case_info': 'N/A',
                'parties': 'N/A',
                'filing_date': 'N/A',
                'next_hearing': 'N/A',
                'case_status': 'N/A',
                'judge': 'N/A',
                'advocate': 'N/A',
                'pdf_link': '#',
                'extracted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'url': self.driver.current_url
            }
            
            # Check if we're still on the search page or got redirected
            if "get-case-type-status" in self.driver.current_url and len(body_text.strip()) < 500:
                print("⚠️ Appears to be still on search page - possible form submission issue")
                case_info['status'] = 'Failed'
                case_info['error'] = 'Form submission may have failed - still on search page'
                case_info['raw_content'] = body_text[:500]
                return case_info
            
            # Check for various error conditions
            page_text_lower = page_source.lower()
            body_text_lower = body_text.lower()
            
            # Error indicators
            error_phrases = [
                'no record found', 'case not found', 'invalid case', 
                'not available', 'error', 'no data found',
                'record does not exist', 'case does not exist',
                'invalid input', 'no results', 'not found'
            ]
            
            # Success indicators
            success_phrases = [
                'case details', 'case information', 'petitioner',
                'respondent', 'filing date', 'next hearing',
                'case status', 'judge', 'court', 'advocate'
            ]
            
            # Check for errors first
            error_found = any(phrase in body_text_lower for phrase in error_phrases)
            success_found = any(phrase in body_text_lower for phrase in success_phrases)
            
            if error_found and not success_found:
                case_info['status'] = 'Failed'
                case_info['error'] = 'Case not found in court records'
                case_info['raw_content'] = body_text[:500]
                print("❌ Case not found - error message detected")
                return case_info
            
            # Look for data tables or structured content
            data_found = False
            
            # Try to find case result tables
            table_selectors = [
                (By.XPATH, "//table[contains(@class, 'case')]"),
                (By.XPATH, "//table[contains(@class, 'result')]"),
                (By.XPATH, "//table[contains(@class, 'data')]"),
                (By.XPATH, "//div[contains(@class, 'case-detail')]"),
                (By.XPATH, "//div[contains(@class, 'result')]"),
                (By.ID, "caseTable"),
                (By.CLASS_NAME, "case-info"),
                (By.TAG_NAME, "table")
            ]
            
            main_content = None
            for selector in table_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for element in elements:
                        element_text = element.text.strip()
                        if len(element_text) > 50 and any(phrase in element_text.lower() for phrase in success_phrases):
                            main_content = element
                            print(f"✅ Found case data using: {selector}")
                            data_found = True
                            break
                    if data_found:
                        break
                except:
                    continue
            
            # If no structured data found, check for any meaningful content
            if not data_found:
                print("⚠️ No structured case data found, analyzing page content...")
                
                # Look for any content that might contain case information
                content_areas = [
                    (By.CLASS_NAME, "content"),
                    (By.CLASS_NAME, "main"),
                    (By.ID, "main"),
                    (By.ID, "content"),
                    (By.XPATH, "//div[contains(@class, 'container')]"),
                    (By.XPATH, "//div[contains(@id, 'result')]")
                ]
                
                for selector in content_areas:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for element in elements:
                            element_text = element.text.strip()
                            if len(element_text) > 100:
                                main_content = element
                                print(f"✅ Found content area: {selector}")
                                break
                        if main_content:
                            break
                    except:
                        continue
            
            # Extract information from content
            if main_content:
                content_text = main_content.text
                print(f"📄 Extracted content length: {len(content_text)} characters")
            else:
                content_text = body_text
                print("📄 Using full page content for extraction")
            
            # Enhanced text parsing
            lines = content_text.split('\n')
            
            # Store all lines for pattern matching
            all_text = ' '.join(lines).lower()
            
            # Extract case information using enhanced patterns
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                line_lower = line.lower()
                
                # Extract case number and title
                if any(pattern in line_lower for pattern in ['case no', 'case number', 'crl.m.c', 'vs', 'versus', 'v/s']):
                    if 'vs' in line_lower or 'versus' in line_lower or 'v/s' in line_lower:
                        case_info['case_info'] = line
                        # Extract parties
                        for separator in [' vs ', ' versus ', ' v/s ', ' v. ']:
                            if separator in line_lower:
                                parts = line.split(separator, 1)
                                if len(parts) == 2:
                                    case_info['parties'] = f"Petitioner: {parts[0].strip()}, Respondent: {parts[1].strip()}"
                                break
                
                # Extract dates with more patterns
                date_patterns = ['filing date', 'filed on', 'date of filing', 'registered on', 'instituted on']
                if any(pattern in line_lower for pattern in date_patterns):
                    # Try next line first
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if any(char.isdigit() for char in next_line) and len(next_line) > 5:
                            case_info['filing_date'] = next_line
                    
                    # Try same line
                    if case_info['filing_date'] == 'N/A':
                        parts = line.split(':')
                        if len(parts) > 1:
                            date_part = parts[-1].strip()
                            if any(char.isdigit() for char in date_part):
                                case_info['filing_date'] = date_part
                
                # Extract hearing dates
                hearing_patterns = ['next hearing', 'next date', 'hearing date', 'next listed', 'adjourned to']
                if any(pattern in line_lower for pattern in hearing_patterns):
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if any(char.isdigit() for char in next_line) and len(next_line) > 5:
                            case_info['next_hearing'] = next_line
                    
                    if case_info['next_hearing'] == 'N/A':
                        parts = line.split(':')
                        if len(parts) > 1:
                            date_part = parts[-1].strip()
                            if any(char.isdigit() for char in date_part):
                                case_info['next_hearing'] = date_part
                
                # Extract status
                status_patterns = ['status', 'stage', 'disposed', 'pending', 'dismissed', 'allowed']
                if any(pattern in line_lower for pattern in status_patterns) and len(line) > 10:
                    case_info['case_status'] = line
                
                # Extract judge
                judge_patterns = ['judge', 'hon\'ble', 'court of', 'before', 'coram']
                if any(pattern in line_lower for pattern in judge_patterns) and len(line) > 10:
                    case_info['judge'] = line
                
                # Extract advocate
                advocate_patterns = ['advocate', 'counsel', 'lawyer', 'represented by', 'for petitioner', 'for respondent']
                if any(pattern in line_lower for pattern in advocate_patterns) and len(line) > 10:
                    case_info['advocate'] = line
            
            # Try to find PDF or document links
            try:
                pdf_selectors = [
                    (By.XPATH, "//a[contains(@href, '.pdf')]"),
                    (By.XPATH, "//a[contains(text(), 'PDF')]"),
                    (By.XPATH, "//a[contains(text(), 'Download')]"),
                    (By.XPATH, "//a[contains(@href, 'download')]")
                ]
                
                for selector in pdf_selectors:
                    try:
                        pdf_links = self.driver.find_elements(*selector)
                        if pdf_links:
                            case_info['pdf_link'] = pdf_links[0].get_attribute('href')
                            print("✅ Found PDF link")
                            break
                    except:
                        continue
            except:
                pass
            
            # Store raw content for debugging (first 1000 chars)
            case_info['raw_content'] = content_text[:1000]
            
            # Final validation - check if we extracted meaningful data
            meaningful_data = any(case_info[key] != 'N/A' for key in ['case_info', 'parties', 'filing_date', 'next_hearing', 'case_status'])
            
            if not meaningful_data and len(content_text.strip()) < 200:
                case_info['status'] = 'Failed'
                case_info['error'] = 'No meaningful case data found - possible form submission issue'
                print("❌ No meaningful case data extracted")
            else:
                print(f"✅ Case information extracted successfully")
            
            return case_info
                
        except Exception as e:
            print(f"❌ Error in data extraction: {e}")
            return {
                'status': 'Failed',
                'error': f'Data extraction failed: {str(e)}',
                'case_info': 'N/A',
                'parties': 'N/A',
                'filing_date': 'N/A',
                'next_hearing': 'N/A',
                'pdf_link': '#',
                'raw_content': str(e)
            }
    
    def get_case_information(self, case_type, case_number, filing_year):
        """Main method to get case information - matches Flask interface"""
        try:
            print(f"🚀 Starting case search for {case_type} {case_number}/{filing_year}")
            
            # Setup driver
            if not self.setup_driver():
                return {
                    'status': 'Failed',
                    'error': 'Failed to initialize Firefox WebDriver',
                    'case_info': 'N/A',
                    'parties': 'N/A',
                    'filing_date': 'N/A',
                    'next_hearing': 'N/A',
                    'pdf_link': '#'
                }
            
            # Navigate to site
            if not self.navigate_to_site():
                return {
                    'status': 'Failed',
                    'error': 'Failed to load Delhi High Court website',
                    'case_info': 'N/A',
                    'parties': 'N/A',
                    'filing_date': 'N/A',
                    'next_hearing': 'N/A',
                    'pdf_link': '#'
                }
            
            # Auto-fill form
            if not self.auto_fill_case_details(case_type, case_number, filing_year):
                print("⚠️ Auto-fill failed, but continuing...")
            
            # Search for case
            if not self.search_cases():
                return {
                    'status': 'Failed',
                    'error': 'Failed to submit search form',
                    'case_info': 'N/A',
                    'parties': 'N/A',
                    'filing_date': 'N/A',
                    'next_hearing': 'N/A',
                    'pdf_link': '#'
                }
            
            # Extract case information
            case_data = self.extract_case_information()
            
            print(f"🎉 Case search completed for {case_type} {case_number}/{filing_year}")
            return case_data
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return {
                'status': 'Failed',
                'error': f'Unexpected error: {str(e)}',
                'case_info': 'N/A',
                'parties': 'N/A',
                'filing_date': 'N/A',
                'next_hearing': 'N/A',
                'pdf_link': '#'
            }
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                print("🧹 WebDriver cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

# Manual captcha solving utility
def manual_captcha_mode():
    """Run scraper with manual captcha solving"""
    print("🔐 Manual Captcha Mode - You'll need to solve captcha manually")
    scraper = DelhiHighCourtScraper(headless=False)
    
    case_type = input("Enter Case Type (e.g., CRL.M.C.): ").strip()
    case_number = input("Enter Case Number: ").strip()
    filing_year = input("Enter Filing Year: ").strip()
    
    if not all([case_type, case_number, filing_year]):
        print("❌ All fields are required!")
        return
    
    try:
        case_number = int(case_number)
        filing_year = int(filing_year)
    except ValueError:
        print("❌ Case number and year must be numbers!")
        return
    
    result = scraper.get_case_information(case_type, case_number, filing_year)
    
    print("\n" + "="*50)
    print("CASE SEARCH RESULT:")
    print("="*50)
    for key, value in result.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("="*50)

# Standalone usage example
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        manual_captcha_mode()
    else:
        # Automated test
        scraper = DelhiHighCourtScraper(headless=False)
        
        # Test with sample case
        result = scraper.get_case_information(
            case_type="CRL.M.C.",
            case_number=1234,
            filing_year=2024
        )
        
        print("\n" + "="*50)
        print("CASE SEARCH RESULT:")
        print("="*50)
        for key, value in result.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("="*50)