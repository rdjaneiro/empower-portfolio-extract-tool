#!/usr/bin/env python3
import argparse
import subprocess
import sys

def run_streamlit_dev():
    print("Starting Streamlit in development mode on port 8502...")
    subprocess.run([
        "streamlit", "run", 
        "streamlit_app.py",
        "--server.port", "8502",
        "--server.address", "localhost"
    ])

def run_dash_dev():
    print("Starting Dash in development mode on port 8052...")
    subprocess.run([
        "python", "dash_app.py",
        "--port", "8052",
        "--host", "localhost"
    ])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run development servers")
    parser.add_argument(
        "app",
        choices=["streamlit", "dash"],
        help="Which app to run in development mode"
    )
    
    args = parser.parse_args()
    
    try:
        if args.app == "streamlit":
            run_streamlit_dev()
        else:
            run_dash_dev()
    except KeyboardInterrupt:
        print("\nDevelopment server stopped")
        sys.exit(0)
