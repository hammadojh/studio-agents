#!/usr/bin/env python3
"""
Quick launcher for the LangGraph Agent System Web Interface

This script provides an easy way to start the web interface from the root directory.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the web interface"""
    print("🚀 LangGraph Agent System - Web Interface Launcher")
    print("=" * 60)
    
    # Get the directory of this script (should be root)
    script_dir = Path(__file__).parent
    web_interface_dir = script_dir / "web_interface"
    
    # Check if web_interface directory exists
    if not web_interface_dir.exists():
        print("❌ web_interface directory not found!")
        print(f"   Expected at: {web_interface_dir}")
        sys.exit(1)
    
    # Check if run_server.py exists
    run_server_path = web_interface_dir / "run_server.py"
    if not run_server_path.exists():
        print("❌ run_server.py not found!")
        print(f"   Expected at: {run_server_path}")
        sys.exit(1)
    
    print("📂 Found web interface files")
    print(f"🎯 Starting server from: {run_server_path}")
    print()
    
    try:
        # Execute the run_server.py script
        subprocess.run([sys.executable, str(run_server_path)], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Web interface stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start web interface: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 