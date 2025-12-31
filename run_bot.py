#!/usr/bin/env python3
"""
Main entry point for BIN Search Bot
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bot.BINSearchCCGbot import main

if __name__ == "__main__":
    main()