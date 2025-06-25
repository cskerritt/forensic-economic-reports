#!/usr/bin/env python3
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
