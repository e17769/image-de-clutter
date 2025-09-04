"""
Unit tests for main window UI.
"""

import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QLabel

from src.ui.main_window import MainWindow


@pytest.mark.ui
class TestMainWindow:
    """Test main window functionality."""
    
    def test_main_window_initialization(self, qapp):
        """Test that main window initializes correctly."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            window = MainWindow()
            
            assert window.windowTitle() == "Photo Archivist"
            assert window.geometry().width() == 800
            assert window.geometry().height() == 600
    
    def test_main_window_has_required_widgets(self, qapp):
        """Test that main window contains required widgets."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            window = MainWindow()
            
            # Check for title label
            title_labels = window.findChildren(QLabel)
            title_found = any("Photo Archivist" in label.text() for label in title_labels)
            assert title_found
            
            # Check for buttons
            buttons = window.findChildren(QPushButton)
            button_texts = [btn.text() for btn in buttons]
            assert "Scan for Images" in button_texts
            assert "Cancel Scan" in button_texts
            assert "Settings" in button_texts
            assert "Choose Folder" in button_texts
    
    def test_scan_button_click_handler(self, qapp):
        """Test scan button click handler."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            window = MainWindow()
            window.on_scan_clicked()
            
            # Verify logger was called (scan with no folder selected)
            mock_logger_instance.warning.assert_called_with("Scan button clicked but no folder selected")
            
            # Verify status bar message
            assert "Please select a folder first" in window.status_bar.currentMessage()
    
    def test_settings_button_click_handler(self, qapp):
        """Test settings button click handler."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            window = MainWindow()
            window.on_settings_clicked()
            
            # Verify logger was called
            mock_logger_instance.info.assert_called_with("Settings button clicked (not implemented yet)")
            
            # Verify status bar message
            assert "future stories" in window.status_bar.currentMessage()
    
    def test_close_event_logging(self, qapp):
        """Test that close event is logged."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            window = MainWindow()
            
            # Create a mock close event
            from PyQt6.QtGui import QCloseEvent
            close_event = QCloseEvent()
            
            window.closeEvent(close_event)
            
            # Verify logger was called
            mock_logger_instance.info.assert_called_with("Application closing")
