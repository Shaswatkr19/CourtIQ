# database_logger.py - Complete Database Logger with Auto Creation

import sqlite3
import os
import json
from datetime import datetime
import threading

class CaseSearchLogger:
    """Database logger for case search operations with automatic initialization"""
    
    def __init__(self, db_path="case_search.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            print(f"🔧 Initializing database: {self.db_path}")
            
            # Ensure database directory exists
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Create database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create searches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    case_type TEXT NOT NULL,
                    case_number INTEGER NOT NULL,
                    filing_year INTEGER NOT NULL,
                    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    status TEXT,
                    processing_time REAL,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create case_results table  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS case_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    result_data TEXT,
                    case_info TEXT,
                    parties TEXT,
                    filing_date TEXT,
                    next_hearing TEXT,
                    pdf_link TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES searches (case_id)
                )
            ''')
            
            # Create search_statistics table for analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    total_searches INTEGER DEFAULT 0,
                    successful_searches INTEGER DEFAULT 0,
                    failed_searches INTEGER DEFAULT 0,
                    avg_processing_time REAL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Commit and close
            conn.commit()
            conn.close()
            
            print(f"✅ Database initialized successfully: {self.db_path}")
            print(f"📊 Database file size: {os.path.getsize(self.db_path)} bytes")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    def log_search_start(self, case_id, case_type, case_number, filing_year, ip_address="unknown"):
        """Log the start of a case search"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO searches 
                    (case_id, case_type, case_number, filing_year, ip_address, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (case_id, case_type, case_number, filing_year, ip_address, "STARTED"))
                
                conn.commit()
                conn.close()
                print(f"📝 Logged search start: {case_id}")
                
        except Exception as e:
            print(f"❌ Error logging search start: {e}")
    
    def log_search_result(self, case_id, status, case_data=None, processing_time=0, error_message=None):
        """Log the result of a case search"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Update searches table with result
                cursor.execute('''
                    UPDATE searches 
                    SET status = ?, processing_time = ?, error_message = ?
                    WHERE case_id = ?
                ''', (status, processing_time, error_message, case_id))
                
                # If successful, store case data
                if case_data and status in ["SUCCESS", "SUCCESS_WITH_WARNING"]:
                    cursor.execute('''
                        INSERT INTO case_results 
                        (case_id, result_data, case_info, parties, filing_date, next_hearing, pdf_link)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        case_id,
                        json.dumps(case_data),
                        case_data.get('case_info', ''),
                        case_data.get('parties', ''),
                        case_data.get('filing_date', ''),
                        case_data.get('next_hearing', ''),
                        case_data.get('pdf_link', '')
                    ))
                
                conn.commit()
                conn.close()
                print(f"📝 Logged search result: {case_id} - {status}")
                
        except Exception as e:
            print(f"❌ Error logging search result: {e}")
    
    def get_recent_searches(self, limit=50):
        """Get recent searches from database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # Return rows as dictionaries
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM searches 
                    ORDER BY search_timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                # Convert to list of dictionaries
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"❌ Error getting recent searches: {e}")
            return []
    
    def get_search_statistics(self):
        """Get search statistics"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Total searches
                cursor.execute('SELECT COUNT(*) as total FROM searches')
                total_searches = cursor.fetchone()[0]
                
                # Successful searches
                cursor.execute('SELECT COUNT(*) as successful FROM searches WHERE status = "SUCCESS"')
                successful_searches = cursor.fetchone()[0]
                
                # Failed searches
                cursor.execute('SELECT COUNT(*) as failed FROM searches WHERE status = "FAILED"')
                failed_searches = cursor.fetchone()[0]
                
                # Average processing time
                cursor.execute('SELECT AVG(processing_time) as avg_time FROM searches WHERE processing_time > 0')
                avg_processing_time = cursor.fetchone()[0] or 0
                
                # Recent searches (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) as recent FROM searches 
                    WHERE search_timestamp > datetime('now', '-1 day')
                ''')
                recent_searches = cursor.fetchone()[0]
                
                conn.close()
                
                return {
                    'total_searches': total_searches,
                    'successful_searches': successful_searches,
                    'failed_searches': failed_searches,
                    'success_rate': round((successful_searches / total_searches * 100) if total_searches > 0 else 0, 2),
                    'avg_processing_time': round(avg_processing_time, 2),
                    'recent_searches_24h': recent_searches
                }
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
    
    def get_case_history(self, case_type, case_number, filing_year):
        """Get search history for a specific case"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT s.*, r.case_info, r.parties, r.filing_date, r.next_hearing 
                    FROM searches s
                    LEFT JOIN case_results r ON s.case_id = r.case_id
                    WHERE s.case_type = ? AND s.case_number = ? AND s.filing_year = ?
                    ORDER BY s.search_timestamp DESC
                ''', (case_type, case_number, filing_year))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"❌ Error getting case history: {e}")
            return []
    
    def cleanup_old_records(self, days_to_keep=30):
        """Clean up old records to prevent database bloat"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Delete old searches and their results
                cursor.execute('''
                    DELETE FROM case_results 
                    WHERE case_id IN (
                        SELECT case_id FROM searches 
                        WHERE search_timestamp < datetime('now', '-{} days')
                    )
                '''.format(days_to_keep))
                
                cursor.execute('''
                    DELETE FROM searches 
                    WHERE search_timestamp < datetime('now', '-{} days')
                '''.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                print(f"🧹 Cleaned up {deleted_count} old records")
                return deleted_count
                
        except Exception as e:
            print(f"❌ Error cleaning up records: {e}")
            return 0
    
    def test_database(self):
        """Test database connection and functionality"""
        try:
            # Test connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            expected_tables = ['searches', 'case_results', 'search_statistics']
            existing_tables = [table[0] for table in tables]
            
            return {
                'connection': True,
                'tables_created': all(table in existing_tables for table in expected_tables),
                'existing_tables': existing_tables,
                'database_path': self.db_path,
                'database_exists': os.path.exists(self.db_path),
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
            
        except Exception as e:
            return {
                'connection': False,
                'error': str(e),
                'database_path': self.db_path,
                'database_exists': os.path.exists(self.db_path)
            }

# Test function to verify database creation
def test_database_creation():
    """Test function to verify database is created properly"""
    print("🧪 Testing database creation...")
    
    logger = CaseSearchLogger()
    test_result = logger.test_database()
    
    print("📊 Database Test Results:")
    for key, value in test_result.items():
        print(f"   {key}: {value}")
    
    if test_result.get('connection') and test_result.get('tables_created'):
        print("✅ Database test passed!")
        return True
    else:
        print("❌ Database test failed!")
        return False

if __name__ == "__main__":
    # Run test when script is executed directly
    test_database_creation()