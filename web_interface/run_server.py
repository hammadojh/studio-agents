#!/usr/bin/env python3
"""
Simple runner script for the LangGraph Agent System Web Interface

This script starts the FastAPI server with WebSocket support for the
LangGraph agent system. It provides a convenient way to launch the
web interface with proper configuration and error handling.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path to import dependencies
sys.path.append(str(Path(__file__).parent.parent))

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'websockets',
        'langgraph',
        'langchain',
        'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if required environment variables are set"""
    required_env_vars = ['OPENAI_API_KEY']
    optional_env_vars = ['ANTHROPIC_API_KEY', 'LANGCHAIN_API_KEY']
    
    missing_required = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\n🔑 Set them with:")
        for var in missing_required:
            print(f"   export {var}=your_key_here")
        return False
    
    # Show status of optional variables
    print("✅ Environment Variables:")
    for var in required_env_vars + optional_env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✓ {var}: {'*' * (len(value) - 4) + value[-4:]}")
        else:
            print(f"   ○ {var}: Not set (optional)" if var in optional_env_vars else f"   ✗ {var}: Not set")
    
    return True

def main():
    """Main entry point"""
    print("🚀 LangGraph Agent System - Web Server Launcher")
    print("=" * 60)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies OK")
    
    # Check environment
    print("\n🔑 Checking environment...")
    if not check_environment():
        sys.exit(1)
    print("✅ Environment OK")
    
    # Check if main.py exists
    main_py_path = Path(__file__).parent / "main.py"
    if not main_py_path.exists():
        print(f"❌ main.py not found at {main_py_path}")
        sys.exit(1)
    
    print("\n🌐 Starting web server...")
    print("=" * 60)
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 Web interface: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("📋 Sessions info: http://localhost:8000/sessions")
    print("=" * 60)
    print("💡 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start the server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        # Change to the web_interface directory
        os.chdir(Path(__file__).parent)
        
        # Run the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 