# app.py - Enhanced Flask App with Built-in Error Handling

from flask import Flask, render_template, request, send_file, flash, jsonify, redirect, session
import csv
from fpdf import FPDF
import os
import threading
import time
import secrets
import socket
import requests
from datetime import datetime
import json
from engine import DelhiHighCourtScraper  # Your backend scraper

app = Flask(__name__)
# Generate a secure secret key for Flask sessions
app.secret_key = secrets.token_hex(32)

# File paths for generated reports
DATA_FILE_CSV = "case_data.csv"
DATA_FILE_PDF = "case_data.pdf"
LOG_FILE = "search_logs.json"

# Global variables to store case data and status
latest_case_data = None
scraping_status = {}
scraping_lock = threading.Lock()  # Thread safety

class SimpleLogger:
    """Simple logging class for case searches"""
    
    def __init__(self):
        self.log_file = LOG_FILE
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Ensure log file exists"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_search(self, case_id, case_type, case_number, filing_year, status, error_msg=None):
        """Log a search attempt"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'case_id': case_id,
                'case_type': case_type,
                'case_number': case_number,
                'filing_year': filing_year,
                'status': status,
                'error_message': error_msg,
                'ip_address': 'localhost'
            }
            
            # Read existing logs
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
            
            # Add new log
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Logging error: {e}")
    
    def get_recent_logs(self, limit=50):
        """Get recent search logs"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            return logs[-limit:] if logs else []
        except:
            return []

class SimpleErrorHandler:
    """Simple error handling class"""
    
    def __init__(self):
        self.court_website = "https://delhihighcourt.nic.in"
    
    def is_website_accessible(self, timeout=10):
        """Check if court website is accessible"""
        try:
            response = requests.get(self.court_website, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
        except Exception:
            return False
    
    def validate_case_inputs(self, case_type, case_number, filing_year):
        """Validate case input parameters"""
        # Check if all fields are provided
        if not all([case_type, case_number, filing_year]):
            return False, "Please fill in all required fields."
        
        try:
            case_number_int = int(case_number)
            filing_year_int = int(filing_year)
            
            if case_number_int <= 0:
                return False, "Case number must be a positive number."
            
            if filing_year_int < 1990 or filing_year_int > 2030:
                return False, "Please enter a valid filing year (1990-2030)."
            
            return True, "Valid inputs"
            
        except ValueError:
            return False, "Case number and filing year must be valid numbers."
    
    def classify_error(self, error):
        """Classify error type for better handling"""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return "TIMEOUT"
        elif "connection" in error_str or "network" in error_str:
            return "NETWORK"
        elif "dns" in error_str or "name resolution" in error_str:
            return "DNS_ERROR"
        elif "selenium" in error_str or "webdriver" in error_str:
            return "BROWSER_ERROR"
        elif "element not found" in error_str or "no such element" in error_str:
            return "ELEMENT_NOT_FOUND"
        else:
            return "UNKNOWN"
    
    def get_user_friendly_message(self, error, error_type):
        """Get user-friendly error message"""
        if error_type == "TIMEOUT":
            return "⏱️ Request timed out. The court website is responding slowly. Please try again."
        elif error_type == "NETWORK":
            return "🌐 Network connection issue. Please check your internet connection and try again."
        elif error_type == "DNS_ERROR":
            return "🔍 Unable to reach the court website. Please check your internet connection."
        elif error_type == "BROWSER_ERROR":
            return "🌐 Browser setup issue. Please try refreshing the page or contact support."
        elif error_type == "ELEMENT_NOT_FOUND":
            return "📋 Court website layout has changed. Please try again or contact support."
        else:
            return f"❌ An unexpected error occurred: {str(error)[:100]}..."
    
    def should_retry(self, error_type):
        """Determine if error is retryable"""
        retryable_errors = ["TIMEOUT", "NETWORK", "ELEMENT_NOT_FOUND"]
        return error_type in retryable_errors
    
    def get_retry_delay(self, attempt_number):
        """Get delay before retry (exponential backoff)"""
        return min(2 ** attempt_number, 10)  # Max 10 seconds
    
    def handle_error(self, error, context=""):
        """Main error handling method"""
        error_type = self.classify_error(error)
        user_message = self.get_user_friendly_message(error, error_type)
        should_retry = self.should_retry(error_type)
        delay = self.get_retry_delay(1) if should_retry else 0
        
        # Log the error
        print(f"❌ Error in {context}: {error}")
        print(f"📝 Error type: {error_type}")
        print(f"👤 User message: {user_message}")
        
        return user_message, should_retry, delay

# Initialize logger and error handler
logger = SimpleLogger()
error_handler = SimpleErrorHandler()

# Try to use database logger if available
try:
    from database_logger import CaseSearchLogger
    print("🔧 Initializing database logger...")
    db_logger = CaseSearchLogger()  # This will auto-create case_search.db
    
    # Test database functionality
    test_result = db_logger.test_database()
    if test_result.get('connection') and test_result.get('tables_created'):
        use_database = True
        print("✅ Database logger initialized successfully!")
        print(f"📊 Database: {test_result.get('database_path')} ({test_result.get('database_size')} bytes)")
    else:
        use_database = False
        print("❌ Database connection failed - using JSON logging only")
        print(f"Error details: {test_result}")
        
except ImportError as e:
    db_logger = None
    use_database = False
    print("⚠️ Database logger not found - using JSON logging only")
    print(f"Import error: {e}")
except Exception as e:
    db_logger = None
    use_database = False
    print(f"❌ Database initialization failed: {e}")
    print("🔄 Using JSON logging as fallback")

class CaseDataPDF(FPDF):
    """Custom PDF class for generating case reports"""
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Delhi High Court - Case Information Report', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def save_case_data_to_files(case_data):
    """Save case data to both CSV and PDF files with comprehensive error handling"""
    global latest_case_data
    
    try:
        with scraping_lock:
            latest_case_data = case_data.copy()  # Thread-safe copy
        
        # Save to CSV
        with open(DATA_FILE_CSV, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field', 'Value'])  # Header
            for key, value in case_data.items():
                writer.writerow([key, str(value)])
        
        # Save to PDF
        pdf = CaseDataPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        for key, value in case_data.items():
            try:
                # Handle long text by wrapping
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(50, 10, txt=f"{key.replace('_', ' ').title()}:", ln=False)
                pdf.set_font("Arial", size=12)
                
                # Split long values into multiple lines
                value_str = str(value)
                if len(value_str) > 50:
                    lines = [value_str[i:i+50] for i in range(0, len(value_str), 50)]
                    pdf.cell(0, 10, txt=lines[0], ln=True)
                    for line in lines[1:]:
                        pdf.cell(50, 10, txt="", ln=False)  # Empty space for alignment
                        pdf.cell(0, 10, txt=line, ln=True)
                else:
                    pdf.cell(0, 10, txt=value_str, ln=True)
                
                pdf.ln(2)  # Add small spacing between fields
            except Exception as e:
                print(f"⚠️ Error adding field {key} to PDF: {e}")
                continue
        
        pdf.output(DATA_FILE_PDF)
        print(f"✅ Files saved: {DATA_FILE_CSV}, {DATA_FILE_PDF}")
        return True
        
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "save_case_data_to_files")
        print(f"❌ Error saving files: {error_msg}")
        return False

def scrape_case_background(case_id, case_type, case_number, filing_year):
    """Background function to scrape case information with comprehensive error handling"""
    global latest_case_data, scraping_status
    
    start_time = time.time()
    
    try:
        print(f"🔍 Starting background scrape for case: {case_id}")
        
        # Update status with thread safety
        with scraping_lock:
            scraping_status[case_id] = {
                'status': 'starting',
                'message': 'Initializing case search...',
                'progress': 10,
                'timestamp': time.time(),
                'data_ready': False
            }
        
        # Pre-flight checks
        print("🌐 Checking website accessibility...")
        if not error_handler.is_website_accessible():
            raise ConnectionError("Delhi High Court website is not accessible")
        
        # Create scraper instance
        scraper = DelhiHighCourtScraper()
        
        # Update progress
        with scraping_lock:
            scraping_status[case_id].update({
                'status': 'running',
                'message': 'Browser initialized, accessing court website...',
                'progress': 30
            })
        
        print(f"🌐 Scraping case: {case_type} {case_number}/{filing_year}")
        
        # Scrape case information with retry logic
        max_attempts = 3
        case_data = None
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"🔄 Attempt {attempt}/{max_attempts}")
                with scraping_lock:
                    scraping_status[case_id]['message'] = f'Searching case information (attempt {attempt}/{max_attempts})...'
                    scraping_status[case_id]['progress'] = 30 + (attempt * 20)
                
                case_data = scraper.get_case_information(case_type, case_number, filing_year)
                break  # Success, exit retry loop
                
            except Exception as e:
                last_error = e
                print(f"❌ Attempt {attempt} failed: {str(e)}")
                
                if attempt == max_attempts:
                    raise e  # Re-raise the last exception
                
                # Handle retryable errors
                error_msg, should_retry, delay = error_handler.handle_error(e, "scrape_case_background")
                
                if not should_retry:
                    raise e  # Don't retry for non-retryable errors
                
                # Update status for retry
                with scraping_lock:
                    scraping_status[case_id]['message'] = f'Retrying in {delay} seconds... (attempt {attempt + 1}/{max_attempts})'
                
                if delay > 0:
                    time.sleep(delay)
        
        print(f"📊 Scraping result: {case_data}")
        
        # Update progress
        with scraping_lock:
            scraping_status[case_id]['progress'] = 90
            scraping_status[case_id]['message'] = 'Processing retrieved data...'
        
        processing_time = time.time() - start_time
        
        if case_data and case_data.get('status') == 'Success':
            # Save data to files
            if save_case_data_to_files(case_data):
                with scraping_lock:
                    scraping_status[case_id] = {
                        'status': 'completed',
                        'message': 'Case information retrieved and saved successfully!',
                        'progress': 100,
                        'timestamp': time.time(),
                        'data_ready': True
                    }
                
                # Log successful result
                logger.log_search(case_id, case_type, case_number, filing_year, "SUCCESS")
                if use_database and db_logger:
                    db_logger.log_search_result(case_id, "SUCCESS", case_data, processing_time=processing_time)
                print("✅ Case data retrieved and saved successfully")
                
            else:
                with scraping_lock:
                    scraping_status[case_id] = {
                        'status': 'completed_with_warning',
                        'message': 'Case information retrieved but file saving failed',
                        'progress': 100,
                        'timestamp': time.time(),
                        'data_ready': True
                    }
                logger.log_search(case_id, case_type, case_number, filing_year, "SUCCESS_WITH_WARNING", "File saving failed")
                if use_database and db_logger:
                    db_logger.log_search_result(case_id, "SUCCESS_WITH_WARNING", case_data, error_message="File saving failed", processing_time=processing_time)
        else:
            error_msg = case_data.get('error', 'Case not found or scraping failed') if case_data else 'Unknown error occurred'
            with scraping_lock:
                scraping_status[case_id] = {
                    'status': 'failed',
                    'message': f'Search completed but no data found: {error_msg}',
                    'progress': 100,
                    'timestamp': time.time(),
                    'data_ready': False
                }
                latest_case_data = {
                    'status': 'Failed',
                    'error': error_msg,
                    'case_info': 'N/A',
                    'parties': 'N/A',
                    'filing_date': 'N/A',
                    'next_hearing': 'N/A',
                    'pdf_link': '#'
                }
            
            # Log failed result
            logger.log_search(case_id, case_type, case_number, filing_year, "NO_DATA", error_msg)
            if use_database and db_logger:
                db_logger.log_search_result(case_id, "NO_DATA", case_data, error_message=error_msg, processing_time=processing_time)
            print(f"⚠️ No data found: {error_msg}")
            
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Handle the error using our error handler
        user_error_msg, should_retry, delay = error_handler.handle_error(e, "scrape_case_background")
        error_type = error_handler.classify_error(e)
        
        print(f"❌ Background scraping failed: {user_error_msg}")
        
        with scraping_lock:
            scraping_status[case_id] = {
                'status': 'failed',
                'message': user_error_msg,
                'progress': 100,
                'timestamp': time.time(),
                'error_type': error_type,
                'retryable': should_retry,
                'data_ready': False
            }
            
            # Create user-friendly error data
            latest_case_data = {
                'status': 'Failed',
                'error': user_error_msg,
                'error_type': error_type,
                'case_info': 'N/A',
                'parties': 'N/A',
                'filing_date': 'N/A',
                'next_hearing': 'N/A',
                'pdf_link': '#',
                'retryable': should_retry
            }
        
        # Log failed result
        logger.log_search(case_id, case_type, case_number, filing_year, "FAILED", str(e))
        if use_database and db_logger:
            db_logger.log_search_result(case_id, "FAILED", latest_case_data, error_message=str(e), processing_time=processing_time)

@app.route("/", methods=["GET", "POST"])
def index():
    """Main route with comprehensive validation and error handling"""
    global latest_case_data, scraping_status
    
    if request.method == "POST":
        case_type = request.form.get("case_type", "").strip()
        case_number = request.form.get("case_number", "").strip()
        filing_year = request.form.get("filing_year", "").strip()
        
        # Validate inputs using error handler
        is_valid, validation_message = error_handler.validate_case_inputs(
            case_type, case_number, filing_year
        )
        
        if not is_valid:
            flash(validation_message, 'error')
            return render_template("index.html", data=latest_case_data)
        
        # Pre-flight website check
        if not error_handler.is_website_accessible():
            flash('🚫 Delhi High Court website is currently not accessible. Please try again later.', 'error')
            return render_template("index.html", data=latest_case_data)
        
        try:
            case_number_int = int(case_number)
            filing_year_int = int(filing_year)
            
            # Generate unique case ID
            case_id = f"{case_type}_{case_number}_{filing_year}_{int(time.time())}"
            
            # Store case_id in session
            session['current_case_id'] = case_id
            
            # Initialize status
            with scraping_lock:
                scraping_status[case_id] = {
                    'status': 'queued',
                    'message': 'Search request received, starting soon...',
                    'progress': 5,
                    'timestamp': time.time(),
                    'data_ready': False
                }
            
            # Start scraping in background thread
            thread = threading.Thread(
                target=scrape_case_background,
                args=(case_id, case_type, case_number_int, filing_year_int),
                daemon=True
            )
            thread.start()
            
            # Give user immediate feedback
            flash(f'🔍 Search started for {case_type} {case_number}/{filing_year}! Please wait for results...', 'info')
            
            return render_template("index.html", data=latest_case_data, case_id=case_id, searching=True)
            
        except Exception as e:
            error_msg, _, _ = error_handler.handle_error(e, "index_route")
            flash(error_msg, 'error')
            print(f"❌ Error in index route: {error_msg}")
    
    # Check if there's an active case in session
    current_case_id = session.get('current_case_id')
    searching = False
    
    if current_case_id and current_case_id in scraping_status:
        with scraping_lock:
            status_info = scraping_status.get(current_case_id, {})
            if status_info.get('status') in ['queued', 'starting', 'running']:
                searching = True
    
    return render_template("index.html", data=latest_case_data, case_id=current_case_id, searching=searching)

@app.route("/download/<filename>")
def download(filename):
    """Handle file downloads with error handling"""
    try:
        if filename == "case_data.csv" and os.path.exists(DATA_FILE_CSV):
            return send_file(DATA_FILE_CSV, as_attachment=True, download_name="case_information.csv")
        elif filename == "case_data.pdf" and os.path.exists(DATA_FILE_PDF):
            return send_file(DATA_FILE_PDF, as_attachment=True, download_name="case_information.pdf")
        else:
            flash('📁 File not found or not ready for download. Please search for a case first.', 'error')
            return redirect('/')
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "download")
        flash(f'Download error: {error_msg}', 'error')
        return redirect('/')

@app.route("/status")
def status():
    """API endpoint to check overall status"""
    global latest_case_data
    
    with scraping_lock:
        if latest_case_data:
            return jsonify(latest_case_data)
    
    return jsonify({"status": "No data available"})

@app.route("/api/status/<case_id>")
def get_case_status(case_id):
    """API endpoint to check specific case scraping status"""
    global scraping_status
    
    with scraping_lock:
        if case_id in scraping_status:
            status_info = scraping_status[case_id].copy()
            
            # Clean up old statuses (older than 1 hour)
            current_time = time.time()
            to_delete = []
            for cid, status_data in scraping_status.items():
                if current_time - status_data.get('timestamp', 0) > 3600:  # 1 hour
                    to_delete.append(cid)
            
            for cid in to_delete:
                del scraping_status[cid]
            
            return jsonify({
                'found': True,
                'status': status_info['status'],
                'message': status_info['message'],
                'progress': status_info['progress'],
                'data_available': status_info.get('data_ready', False) and latest_case_data is not None,
                'error_type': status_info.get('error_type'),
                'retryable': status_info.get('retryable', False)
            })
        else:
            return jsonify({
                'found': False,
                'status': 'not_found',
                'message': 'Case ID not found or expired',
                'progress': 0,
                'data_available': False
            })

@app.route("/api/result")
def get_latest_result():
    """API endpoint to get latest scraping result"""
    global latest_case_data
    
    with scraping_lock:
        if latest_case_data:
            return jsonify(latest_case_data)
    
    return jsonify({
        'status': 'No Data',
        'error': 'No case data available'
    })

@app.route("/clear")
def clear_data():
    """Clear stored data and files"""
    global latest_case_data, scraping_status
    
    try:
        # Clear global data
        with scraping_lock:
            latest_case_data = None
            scraping_status.clear()
        
        # Clear session
        session.pop('current_case_id', None)
        
        # Remove files if they exist
        for file_path in [DATA_FILE_CSV, DATA_FILE_PDF]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        flash('✅ All data cleared successfully!', 'success')
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "clear_data")
        flash(f'Error clearing data: {error_msg}', 'error')
    
    return redirect('/')

@app.route("/test")
def test_scraper():
    """Test endpoint to verify scraper setup with enhanced diagnostics"""
    try:
        # Test website accessibility first
        if not error_handler.is_website_accessible():
            return jsonify({
                'status': 'error',
                'message': 'Delhi High Court website is not accessible',
                'browser': 'Firefox',
                'url': 'https://delhihighcourt.nic.in/app/get-case-type-status'
            }), 500
        
        # Test scraper setup
        scraper = DelhiHighCourtScraper()
        if scraper.setup_driver():
            scraper.driver.quit()
            return jsonify({
                'status': 'success',
                'message': 'Firefox WebDriver setup successful! Scraper is ready.',
                'browser': 'Firefox',
                'url': 'https://delhihighcourt.nic.in/app/get-case-type-status',
                'website_accessible': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to setup Firefox WebDriver. Please check Firefox installation.',
                'browser': 'Firefox',
                'website_accessible': True
            }), 500
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "test_scraper")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {error_msg}',
            'browser': 'Firefox',
            'website_accessible': False
        }), 500

@app.route("/logs")
def view_logs():
    """View recent search logs"""
    try:
        # Try database first, then fallback to JSON
        if use_database and db_logger:
            recent_logs = db_logger.get_recent_searches(limit=50)
            return jsonify({
                'status': 'success',
                'logs': recent_logs,
                'total_count': len(recent_logs),
                'source': 'database'
            })
        else:
            recent_logs = logger.get_recent_logs(limit=50)
            return jsonify({
                'status': 'success',
                'logs': recent_logs,
                'total_count': len(recent_logs),
                'source': 'json_file'
            })
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "view_logs")
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

@app.route("/database/status")
def database_status():
    """Check database status and statistics"""
    try:
        if use_database and db_logger:
            # Check if database file exists
            db_exists = os.path.exists(db_logger.db_path)
            
            if db_exists:
                # Get database stats
                stats = db_logger.get_search_statistics() if hasattr(db_logger, 'get_search_statistics') else {}
                return jsonify({
                    'status': 'success',
                    'database_available': True,
                    'database_path': db_logger.db_path,
                    'file_size': os.path.getsize(db_logger.db_path),
                    'statistics': stats
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'database_available': False,
                    'message': 'Database file not found - will be created on first search'
                })
        else:
            return jsonify({
                'status': 'info',
                'database_available': False,
                'message': 'Database logger not available - using JSON logging'
            })
    except Exception as e:
        error_msg, _, _ = error_handler.handle_error(e, "database_status")
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html') if os.path.exists('templates/404.html') else "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    error_msg, _, _ = error_handler.handle_error(error, "internal_server_error")
    return render_template('500.html', error_message=error_msg) if os.path.exists('templates/500.html') else f"Internal Server Error: {error_msg}", 500

if __name__ == "__main__":
    import webbrowser
    import threading
    
    # Ensure required directories exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Function to open browser after Flask starts
    def open_browser():
        import time
        time.sleep(2)  # Wait for Flask to start
        try:
            webbrowser.open('http://localhost:5001')
            print("🌐 Browser opened automatically!")
        except Exception as e:
            print(f"⚠️ Could not open browser automatically: {e}")
        print("🔗 Manual URL: http://localhost:5001")
    
    # Start browser opening in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("🚀 Starting Enhanced Delhi High Court Case Search System...")
    print("🦊 Using Firefox WebDriver with built-in error handling")
    print("🌐 Court URL: https://delhihighcourt.nic.in/app/get-case-type-status")
    print("📱 Flask server starting on port 5001...")
    print("🔄 Browser will open automatically in 2 seconds...")
    print("📋 Available endpoints:")
    print("   - Main app: http://localhost:5001")
    print("   - Test scraper: http://localhost:5001/test")
    print("   - View logs: http://localhost:5001/logs")
    print("   - Clear data: http://localhost:5001/clear")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)