#!/usr/bin/env python3
"""
Bus Pass System Server
Run this file to start the application
"""

import os
import sys
from app import IMAGES_DIR, PASSES_DIR, app, init_db

def print_banner():
    print("=" * 70)
    print("🚌 BUS PASS SYSTEM - STARTING SERVER")
    print("=" * 70)
    print()
    print("📍 ACCESS POINTS:")
    print("   Main Application:    http://127.0.0.1:5000")
    print("   User Login:          http://127.0.0.1:5000/login")
    print("   User Registration:   http://127.0.0.1:5000/register")
    print("   Admin Login:         http://127.0.0.1:5000/admin")
    print("   Admin Registration:  http://127.0.0.1:5000/admin/register")
    print("   About Page:          http://127.0.0.1:5000/about")
    print("   Contact Page:        http://127.0.0.1:5000/contact")
    print()
    print("🔐 DEFAULT ADMIN CREDENTIALS:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("🔑 ADMIN REGISTRATION:")
    print("   Registration Key: BUSPASS_ADMIN_2024")
    print("   (Required for new admin accounts)")
    print()
    print("📝 SAMPLE USER ACCOUNTS:")
    print("   (Register new accounts through the system)")
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(PASSES_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    init_db()
    
    # Print startup information
    print_banner()
    
    try:
        # Start the Flask application
        app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("Thank you for using Bus Pass System!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
