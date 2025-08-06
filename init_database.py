# init_database.py - Database Initialization Script

"""
Run this script to manually create and initialize the database
Usage: python init_database.py
"""

import os
import sys
from database_logger import CaseSearchLogger, test_database_creation

def create_database():
    """Create and initialize the database"""
    print("🚀 Starting database initialization...")
    print("=" * 50)
    
    # Check if database already exists
    db_path = "case_search.db"
    if os.path.exists(db_path):
        print(f"⚠️  Database file already exists: {db_path}")
        response = input("Do you want to recreate it? (y/N): ").lower().strip()
        if response == 'y' or response == 'yes':
            os.remove(db_path)
            print("🗑️  Old database deleted.")
        else:
            print("✅ Using existing database.")
    
    # Initialize logger (this will create the database)
    try:
        logger = CaseSearchLogger(db_path)
        print(f"✅ Database created successfully: {db_path}")
        
        # Test the database
        print("\n🧪 Testing database functionality...")
        if test_database_creation():
            print("\n🎉 Database initialization completed successfully!")
            
            # Show database info
            stats = logger.get_search_statistics()
            print(f"\n📊 Database Info:")
            print(f"   📁 Path: {os.path.abspath(db_path)}")
            print(f"   📏 Size: {os.path.getsize(db_path)} bytes")
            print(f"   📈 Total searches: {stats.get('total_searches', 0)}")
            
            return True
        else:
            print("\n❌ Database test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return False

def main():
    """Main function"""
    print("🗄️  Delhi High Court Case Search - Database Initializer")
    print("=" * 60)
    
    if create_database():
        print("\n✅ Database is ready to use!")
        print("💡 You can now run your Flask app: python app.py")
    else:
        print("\n❌ Database initialization failed!")
        print("💡 Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()