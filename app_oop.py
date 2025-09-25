"""
Main entry point for the M-Pesa STK Push application.
Object-oriented, modular Flask application with proper separation of concerns.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app_factory import ApplicationFactory


def main():
    """Main application entry point."""
    try:
        # Create and run the application
        factory = ApplicationFactory()
        factory.run()
        
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()