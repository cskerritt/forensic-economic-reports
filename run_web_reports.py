#!/usr/bin/env python3
"""
Professional Forensic Economic Report Generator - Web Launcher

Launch the professional web-based report generator that opens in your browser.
"""

import sys
import os
import argparse
from pathlib import Path


def check_requirements():
    """Check if required dependencies are installed."""
    required_packages = ['flask', 'openai', 'anthropic', 'sqlite3']
    
    missing = []
    for package in required_packages:
        try:
            if package == 'flask':
                import flask
            elif package == 'openai':
                import openai
            elif package == 'anthropic':
                import anthropic
            elif package == 'sqlite3':
                import sqlite3
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required packages:")
        for package in missing:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        if 'flask' in missing:
            print("   pip install flask openai anthropic")
        else:
            print("   pip install openai anthropic")
        return False
    
    print("✅ All required packages are installed")
    return True


def check_api_keys():
    """Check if API keys are configured."""
    openai_key = os.getenv('OPENAI_API_KEY')
    claude_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not openai_key and not claude_key:
        print("⚠️  Warning: No AI API keys found!")
        print("📋 Set at least one of these environment variables:")
        print("   export OPENAI_API_KEY='your-openai-key'")
        print("   export ANTHROPIC_API_KEY='your-anthropic-key'")
        print("\n🌐 The web app will still start, but report generation will fail without API keys.")
        return False
    
    if openai_key:
        print("✅ OpenAI API key configured")
    if claude_key:
        print("✅ Anthropic API key configured")
    
    return True


def check_database():
    """Check if the economic analysis database exists."""
    db_path = "/Users/chrisskerritt/EconomicAnalysis/instance/app.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found at: {db_path}")
        print("\n🔧 To create sample data:")
        print("   python run_professional_reports.py sample")
        print("\n🔧 Or create the database manually:")
        print("   1. Navigate to: /Users/chrisskerritt/EconomicAnalysis")
        print("   2. Run: python app.py")
        print("   3. Add evaluee data through the web interface")
        return False
    
    print(f"✅ Database found: {db_path}")
    return True


def setup_environment():
    """Setup the environment for the web application."""
    # Create necessary directories
    directories = ['reports', 'templates']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Environment setup complete")


def run_web_app(host='127.0.0.1', port=5000):
    """Launch the web application."""
    try:
        from forensic_report_web_app import ReportWebApp
        
        print(f"🏢 Kincaid Wolstein Vocational and Rehabilitation Services")
        print(f"🌐 Professional Forensic Economic Report Generator")
        print(f"=" * 60)
        print(f"🚀 Starting web server...")
        print(f"📱 Browser will open automatically at http://{host}:{port}")
        print(f"💻 Features: Professional Templates, Download Reports, Live Preview")
        print(f"🛑 Press Ctrl+C to stop the server")
        print()
        
        app = ReportWebApp()
        app.run(host=host, port=port, debug=False, open_browser=True)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("🔧 Make sure all dependencies are installed:")
        print("   pip install flask openai anthropic")
    except Exception as e:
        print(f"❌ Error starting web application: {e}")


def create_sample_data():
    """Create sample evaluee data for testing."""
    try:
        from run_professional_reports import create_sample_data as create_data
        return create_data()
    except ImportError:
        print("❌ Could not import sample data creation function")
        return None


def main():
    parser = argparse.ArgumentParser(description="Kincaid Wolstein Web Report Generator")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--check", action="store_true", help="Check system requirements")
    parser.add_argument("--sample", action="store_true", help="Create sample data")
    
    args = parser.parse_args()
    
    if args.check:
        print("🏢 Kincaid Wolstein Professional Report Generator")
        print("🔍 System Check")
        print("=" * 50)
        print()
        
        print("1️⃣ Checking dependencies...")
        deps_ok = check_requirements()
        print()
        
        print("2️⃣ Checking API keys...")
        api_ok = check_api_keys()
        print()
        
        print("3️⃣ Checking database...")
        db_ok = check_database()
        print()
        
        print("4️⃣ Setting up environment...")
        setup_environment()
        print()
        
        if deps_ok and db_ok:
            print("🎉 System ready! Launch the web application:")
            print("   python run_web_reports.py")
            if not api_ok:
                print("\n⚠️  Note: Configure API keys before generating reports")
        else:
            print("⚠️  Some issues found. Please resolve them before proceeding.")
    
    elif args.sample:
        print("📝 Creating Sample Data")
        print("=" * 30)
        
        if not check_database():
            evaluee_ids = create_sample_data()
            if evaluee_ids:
                print(f"\n🧪 Test the web application:")
                print(f"   python run_web_reports.py")
        else:
            print("✅ Database already exists with data")
    
    else:
        # Check basic requirements before starting
        if not check_requirements():
            print("\n❌ Cannot start web application without required packages")
            return
        
        if not check_database():
            print("\n❌ Cannot start without database. Create sample data first:")
            print("   python run_web_reports.py --sample")
            return
        
        setup_environment()
        run_web_app(args.host, args.port)


if __name__ == "__main__":
    main()