#!/usr/bin/env python3
"""
Quick Python Installation Test
Tests if Python and basic packages work
"""

import sys
import subprocess

def test_python_installation():
    """Test Python installation and basic functionality."""
    print("🧪 Testing Python Installation")
    print("=" * 50)
    
    # Test 1: Python version
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Python Path: {sys.executable}")
    print()
    
    # Test 2: Basic imports
    print("📦 Testing basic imports...")
    try:
        import json
        import os
        import asyncio
        print("   ✅ Standard library imports work")
    except ImportError as e:
        print(f"   ❌ Standard library import failed: {e}")
        return False
    
    # Test 3: pip functionality
    print("📦 Testing pip...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ pip works: {result.stdout.strip()}")
        else:
            print(f"   ❌ pip failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ pip test failed: {e}")
        return False
    
    # Test 4: Package installation test
    print("📦 Testing package installation...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("   ✅ Package installation works")
            
            # Test the installed package
            import requests
            print("   ✅ Package import works")
        else:
            print(f"   ❌ Package installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Package test failed: {e}")
        return False
    
    print()
    print("🎉 Python installation is working perfectly!")
    print()
    print("🚀 Next steps:")
    print("   1. Run: start_webapp.bat")
    print("   2. Visit: http://localhost:8000/docs")
    print("   3. Test payment creation")
    
    return True

if __name__ == "__main__":
    success = test_python_installation()
    
    if success:
        print("\n✅ Ready to start the web application!")
    else:
        print("\n❌ Python setup needs attention")
        print("📖 See PYTHON_SETUP_GUIDE.md for help")
    
    input("\nPress Enter to continue...")
