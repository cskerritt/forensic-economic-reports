#!/usr/bin/env python3
"""
Integration Script for Forensic Reports Module

This script integrates the forensic reports functionality into your existing
economic analysis application seamlessly.
"""

import os
import sys
from pathlib import Path

def integrate_forensic_reports():
    """Integrate forensic reports into the existing application."""
    
    print("🔗 Integrating Forensic Reports Module")
    print("=" * 50)
    
    # Path to the economic analysis application
    app_path = Path("/Users/chrisskerritt/Dropbox/My Mac (chriss-MacBook-Pro.local)/Desktop/Website/economic-analysis")
    
    if not app_path.exists():
        print("❌ Economic analysis application not found!")
        return False
    
    # 1. Update the main app __init__.py to register the blueprint
    init_file = app_path / "forensic_econ_app" / "__init__.py"
    
    print("1️⃣ Updating application initialization...")
    
    if init_file.exists():
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check if forensic reports is already registered
        if 'forensic_reports' not in content:
            # Add the import and registration
            blueprint_registration = """
    # Register forensic reports blueprint (complete version with ALL data integration)
    from .routes import forensic_reports_complete
    app.register_blueprint(forensic_reports_complete.bp)
"""
            
            # Find the end of blueprint registrations and add ours
            if 'return app' in content:
                content = content.replace('return app', blueprint_registration + '\n    return app')
            else:
                content += blueprint_registration
            
            with open(init_file, 'w') as f:
                f.write(content)
            
            print("✅ Added forensic reports blueprint registration")
        else:
            print("✅ Forensic reports already integrated")
    
    # 2. Update the navigation template to include forensic reports
    base_template = app_path / "forensic_econ_app" / "templates" / "base.html"
    
    print("2️⃣ Updating navigation menu...")
    
    if base_template.exists():
        with open(base_template, 'r') as f:
            content = f.read()
        
        # Add forensic reports to navigation if not already there
        if 'forensic-reports' not in content:
            # Find the navigation section and add our menu item
            nav_item = '''
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('forensic_reports_complete.index') }}">
                                    <i class="bi bi-file-earmark-text"></i> Forensic Reports
                                </a>
                            </li>'''
            
            # Look for existing nav items and add after them
            if '<li class="nav-item">' in content:
                # Find the last nav item and add after it
                import re
                pattern = r'(<li class="nav-item">.*?</li>)'
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    last_nav_item = matches[-1]
                    content = content.replace(last_nav_item, last_nav_item + nav_item)
            
            with open(base_template, 'w') as f:
                f.write(content)
            
            print("✅ Added forensic reports to navigation menu")
        else:
            print("✅ Navigation menu already updated")
    
    # 3. Create reports directory in instance folder
    reports_dir = app_path / "instance" / "reports"
    reports_dir.mkdir(exist_ok=True)
    print("✅ Created reports directory")
    
    # 4. Update requirements.txt if needed
    requirements_file = app_path / "requirements.txt"
    
    print("3️⃣ Checking requirements...")
    
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            requirements = f.read()
        
        # Check if we need to add any new requirements
        new_requirements = []
        
        if 'pathlib' not in requirements and 'pathlib' not in requirements:
            # pathlib is built-in to Python 3.4+, no need to add
            pass
        
        if new_requirements:
            with open(requirements_file, 'a') as f:
                for req in new_requirements:
                    f.write(f"\n{req}")
            print(f"✅ Added {len(new_requirements)} new requirements")
        else:
            print("✅ No new requirements needed")
    
    # 5. Create a quick test script
    test_script = app_path / "test_forensic_integration.py"
    
    test_content = '''#!/usr/bin/env python3
"""
Test script for forensic reports integration
"""

import sys
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from forensic_econ_app import create_app
from forensic_econ_app.models.models import db, Evaluee, User

def test_integration():
    """Test the forensic reports integration."""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Forensic Reports Integration")
        print("=" * 40)
        
        # Test database connection
        try:
            evaluee_count = Evaluee.query.count()
            print(f"✅ Database connection: {evaluee_count} evaluees found")
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
        
        # Test blueprint registration
        try:
            with app.test_client() as client:
                response = client.get('/forensic-reports/')
                if response.status_code in [200, 302]:  # 302 for login redirect
                    print("✅ Forensic reports route accessible")
                else:
                    print(f"❌ Route error: Status {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Route test error: {e}")
            return False
        
        print("🎉 Integration test successful!")
        return True

if __name__ == "__main__":
    test_integration()
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print("✅ Created integration test script")
    
    # 6. Create deployment instructions
    instructions_file = app_path / "FORENSIC_REPORTS_INTEGRATION.md"
    
    instructions_content = '''# Forensic Reports Integration

This document describes the integration of professional forensic economic report generation into your Economic Analysis application.

## Features Added

- **Professional Report Generation**: Generate Kincaid Wolstein formatted forensic economic reports
- **Complete Data Integration**: Uses ALL data from your economic analysis system including:
  - Comprehensive earnings scenarios (pre/post injury, seasonal employment, education impacts)
  - Healthcare scenarios with advanced inflation modeling
  - Fringe benefit scenarios using ECEC worker type data
  - Household services with staged valuation
  - Pension scenarios with retirement analysis
  - All economic factors (CPI rates, worker types, geographic regions)
- **Real-time Processing**: Background report generation with progress tracking
- **Download Capability**: Direct download of generated reports
- **User Security**: Reports are user-scoped and secure

## New Routes Added

- `/forensic-reports/` - Main forensic reports interface
- `/forensic-reports/evaluee/{id}/report` - Direct report generation for specific evaluee
- `/forensic-reports/api/evaluees` - API endpoint for evaluee list
- `/forensic-reports/api/generate-report` - API endpoint for report generation
- `/forensic-reports/api/download-report/{session_id}` - Download generated reports

## Navigation

A new "Forensic Reports" menu item has been added to your main navigation.

## File Storage

Generated reports are automatically saved in `instance/reports/` directory.

## Testing

Run the integration test:
```bash
python test_forensic_integration.py
```

## Deployment

1. Restart your application server
2. Clear any browser cache
3. Login and navigate to "Forensic Reports" in the menu
4. Select an evaluee and generate a professional report

## Professional Template & Complete Data Integration

Reports are generated using the professional Kincaid Wolstein template with:
- Complete economic loss analysis using ALL your data models
- Daubert-compliant methodology
- Present value calculations with proper discount rates
- Professional formatting and signatures
- Full integration with ALL economic analysis data including:
  - All earnings scenarios and calculations
  - Healthcare cost projections with inflation
  - Comprehensive fringe benefit analysis
  - Household services valuations
  - Pension and retirement calculations
  - Economic factors and regional adjustments

## Support

The forensic reports module integrates seamlessly with your existing:
- User authentication and security
- Complete evaluee management system
- ALL economic calculations and scenarios
- Comprehensive database structure with all models
- All calculation methodologies and factors

## Data Completeness Assurance

This integration ensures that ALL data from your economic analysis system is properly extracted and formatted in the professional reports:
- ✅ All EarningsScenario data (pre/post injury, seasonal, education)
- ✅ All HealthcareScenario projections with inflation modeling
- ✅ All FringeBenefitScenario calculations using ECEC data
- ✅ All HouseholdServicesScenario valuations
- ✅ All PensionScenario retirement analysis
- ✅ All economic factors and regional adjustments
- ✅ All discount rates and present value calculations
'''
    
    with open(instructions_file, 'w') as f:
        f.write(instructions_content)
    
    print("✅ Created integration documentation")
    
    print("\n🎉 Forensic Reports Integration Complete!")
    print("\nNext Steps:")
    print("1. Restart your Economic Analysis application")
    print("2. Login to your application")
    print("3. Look for 'Forensic Reports' in the navigation menu")
    print("4. Select an evaluee and generate a professional report")
    print("\nTest the integration:")
    print(f"cd {app_path}")
    print("python test_forensic_integration.py")
    
    return True

def main():
    """Main integration function."""
    success = integrate_forensic_reports()
    
    if success:
        print("\n✅ Integration completed successfully!")
        print("The forensic reports module is now part of your Economic Analysis application.")
    else:
        print("\n❌ Integration encountered issues.")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()