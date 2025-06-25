#!/usr/bin/env python3
"""
Professional Forensic Economic Report Generator - Quick Launch

Launch script for the Kincaid Wolstein professional report generator
with enhanced features and download capabilities.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def check_requirements():
    """Check if required dependencies are installed."""
    required_packages = ['tkinter', 'openai', 'anthropic', 'sqlite3']
    
    missing = []
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
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
        print("\n🔧 To create the database:")
        print("   1. Navigate to: /Users/chrisskerritt/EconomicAnalysis")
        print("   2. Run: python app.py")
        print("   3. Add evaluee data through the web interface")
        return False
    
    print(f"✅ Database found: {db_path}")
    return True


def setup_reports_folder():
    """Create reports folder if it doesn't exist."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    print(f"✅ Reports folder ready: {reports_dir.absolute()}")


def run_professional_gui():
    """Launch the professional GUI interface."""
    try:
        from forensic_report_gui_template import main as gui_main
        print("🚀 Starting Kincaid Wolstein Professional Report Generator...")
        print("📊 Features: Professional Template, Download Reports, Search Functionality")
        gui_main()
    except Exception as e:
        print(f"❌ Error starting Professional GUI: {e}")
        print("🔧 Make sure all dependencies are installed and try again.")


def run_template_cli(args):
    """Run the template-based command line interface."""
    try:
        from forensic_report_agent_template import main as cli_main
        
        cli_args = [
            "--evaluee-id", str(args.evaluee_id),
            "--provider", args.provider
        ]
        
        if args.model:
            cli_args.extend(["--model", args.model])
        
        if args.output_dir:
            cli_args.extend(["--output-dir", args.output_dir])
        
        # Set sys.argv for argparse in the agent
        original_argv = sys.argv
        sys.argv = ["forensic_report_agent_template.py"] + cli_args
        
        try:
            print(f"🚀 Generating professional report for evaluee ID {args.evaluee_id}...")
            cli_main()
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Error running CLI: {e}")


def create_sample_data():
    """Create sample evaluee data for testing."""
    try:
        import sqlite3
        from datetime import datetime, date
        
        db_path = "/Users/chrisskerritt/EconomicAnalysis/instance/app.db"
        
        print("📝 Creating sample evaluee data...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                date_of_injury TEXT NOT NULL,
                gender TEXT NOT NULL,
                age_at_injury REAL NOT NULL,
                education_level TEXT,
                occupation TEXT,
                pre_injury_earnings REAL,
                post_injury_capacity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS earnings_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluee_id INTEGER NOT NULL,
                scenario_name TEXT NOT NULL,
                annual_earnings REAL NOT NULL,
                growth_rate REAL,
                present_value REAL,
                discount_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (evaluee_id) REFERENCES evaluees (id)
            )
        """)
        
        # Insert sample evaluees
        sample_evaluees = [
            ("John Smith", "1980-05-15", "2023-03-10", "Male", 42.8, 
             "Bachelor's Degree", "Software Engineer", 85000.0, "Severely Limited"),
            ("Maria Rodriguez", "1975-08-22", "2023-06-15", "Female", 47.9,
             "Master's Degree", "Nurse Practitioner", 95000.0, "Moderately Limited"),
            ("David Johnson", "1990-01-30", "2023-09-05", "Male", 33.6,
             "High School Diploma", "Construction Worker", 65000.0, "Unable to Work")
        ]
        
        evaluee_ids = []
        for evaluee in sample_evaluees:
            cursor.execute("""
                INSERT INTO evaluees (name, date_of_birth, date_of_injury, gender, 
                                    age_at_injury, education_level, occupation, 
                                    pre_injury_earnings, post_injury_capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, evaluee)
            evaluee_ids.append(cursor.lastrowid)
        
        # Insert sample earnings scenarios
        for i, evaluee_id in enumerate(evaluee_ids):
            base_earnings = sample_evaluees[i][7]  # pre_injury_earnings
            scenarios = [
                (evaluee_id, "Pre-Injury Baseline", base_earnings, 2.5, base_earnings * 15, 3.0),
                (evaluee_id, "Post-Injury Capacity", base_earnings * 0.3, 2.5, base_earnings * 4, 3.0),
                (evaluee_id, "Conservative Growth", base_earnings, 2.0, base_earnings * 13, 3.5)
            ]
            
            cursor.executemany("""
                INSERT INTO earnings_scenarios (evaluee_id, scenario_name, annual_earnings, 
                                              growth_rate, present_value, discount_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, scenarios)
        
        conn.commit()
        
        print(f"✅ Sample data created successfully!")
        print(f"📊 Added {len(sample_evaluees)} evaluees with earnings scenarios:")
        for i, evaluee in enumerate(sample_evaluees):
            print(f"   {evaluee_ids[i]}. {evaluee[0]} - {evaluee[6]} (${evaluee[7]:,.0f})")
        
        print(f"\n🧪 Test the professional report generator:")
        print(f"   python run_professional_reports.py gui")
        print(f"   python run_professional_reports.py cli --evaluee-id {evaluee_ids[0]}")
        
        return evaluee_ids
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="Kincaid Wolstein Professional Report Generator")
    parser.add_argument("mode", choices=["gui", "cli", "check", "sample"], 
                       help="Run mode: gui (professional interface), cli (command line), check (verify setup), sample (create test data)")
    
    # CLI-specific arguments
    parser.add_argument("--evaluee-id", type=int, help="Evaluee ID for CLI mode")
    parser.add_argument("--provider", choices=["openai", "claude"], default="openai",
                       help="AI provider")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--output-dir", default="reports", help="Output directory")
    
    args = parser.parse_args()
    
    print("🏢 Kincaid Wolstein Vocational and Rehabilitation Services")
    print("📋 Professional Forensic Economic Report Generator")
    print("=" * 60)
    
    if args.mode == "check":
        print("🔍 System Check\n")
        
        print("1️⃣ Checking dependencies...")
        deps_ok = check_requirements()
        print()
        
        print("2️⃣ Checking API keys...")
        api_ok = check_api_keys()
        print()
        
        print("3️⃣ Checking database...")
        db_ok = check_database()
        print()
        
        print("4️⃣ Setting up reports folder...")
        setup_reports_folder()
        print()
        
        if deps_ok and api_ok and db_ok:
            print("🎉 All checks passed! Ready to generate professional reports.")
            print("\n🚀 Launch the application:")
            print("   python run_professional_reports.py gui")
        else:
            print("⚠️  Some issues found. Please resolve them before proceeding.")
    
    elif args.mode == "sample":
        print("📝 Creating Sample Data\n")
        if not check_database():
            print("🔧 Please create the database first by running the EconomicAnalysis app.")
        else:
            evaluee_ids = create_sample_data()
            if evaluee_ids:
                print(f"\n🧪 Test with sample data:")
                print(f"   python run_professional_reports.py cli --evaluee-id {evaluee_ids[0]}")
    
    elif args.mode == "gui":
        print("🖥️  Starting Professional GUI\n")
        if check_requirements() and check_database():
            setup_reports_folder()
            run_professional_gui()
        else:
            print("❌ Please resolve issues before starting GUI.")
    
    elif args.mode == "cli":
        if not args.evaluee_id:
            print("❌ Error: --evaluee-id is required for CLI mode")
            return
        
        print("💻 Starting CLI Mode\n")
        if check_requirements() and check_database():
            setup_reports_folder()
            run_template_cli(args)
        else:
            print("❌ Please resolve issues before running CLI.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()