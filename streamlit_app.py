# streamlit_app.py - Main Streamlit entry point
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import MemoryManagementApp

if __name__ == "__main__":
    app = MemoryManagementApp()
    app.run()