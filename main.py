#!/usr/bin/env python3
"""
Photo Archivist - Main entry point.

A macOS desktop application for managing duplicate and similar images.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.utils.logger import setup_logging, get_logger


def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting Photo Archivist application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Photo Archivist")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Photo Archivist Team")
    
    # Enable high DPI support for macOS Retina displays
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    try:
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run application event loop
        exit_code = app.exec()
        
        logger.info(f"Application exiting with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error during application startup: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
