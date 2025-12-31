#!/usr/bin/env python3
"""
Test script for Windows Bot
Quick test to verify bot functionality
"""

import subprocess
import time
import requests
import sys
import os

def test_bot():
    print("=== BIN Search Bot Test ===")
    print()
    
    # Start bot in background
    print("[1/4] Starting bot...")
    try:
        bot_process = subprocess.Popen(
            [sys.executable, "run_windows_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for bot to start
        print("[2/4] Waiting for bot startup...")
        time.sleep(15)
        
        # Test health endpoint
        print("[3/4] Testing health endpoint...")
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✓ Health check successful!")
                print(f"  Status: {health_data.get('status', 'unknown')}")
                print(f"  Bot: {health_data.get('bot', 'unknown')}")
                print(f"  Username: {health_data.get('username', 'unknown')}")
                print(f"  Platform: {health_data.get('platform', 'unknown')}")
            else:
                print(f"✗ Health check failed with status: {response.status_code}")
        except Exception as e:
            print(f"✗ Health check failed: {e}")
        
        # Check if bot process is still running
        print("[4/4] Checking bot process...")
        if bot_process.poll() is None:
            print("✓ Bot process is running")
            
            # Show bot info
            print()
            print("Bot Information:")
            print("  • Username: @Cryptobinchecker_ccbot")
            print("  • Health URL: http://localhost:8001/health")
            print("  • Web Platform: https://5e336a94.bin-search-pro.pages.dev")
            print()
            print("To test the bot:")
            print("1. Go to Telegram and search for @Cryptobinchecker_ccbot")
            print("2. Send /start to begin")
            print("3. Try /help to see available commands")
            print()
            print("Press Ctrl+C to stop the test and bot")
            
            try:
                # Keep test running
                bot_process.wait()
            except KeyboardInterrupt:
                print("\n[STOP] Stopping bot...")
                bot_process.terminate()
                bot_process.wait()
                print("✓ Bot stopped")
        else:
            print("✗ Bot process has stopped")
            stdout, stderr = bot_process.communicate()
            if stderr:
                print(f"Error output: {stderr}")
    
    except Exception as e:
        print(f"✗ Failed to start bot: {e}")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("run_windows_bot.py"):
        print("Error: Please run this script from the mergebins directory")
        sys.exit(1)
    
    test_bot()