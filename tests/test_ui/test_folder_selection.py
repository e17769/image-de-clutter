"""
Unit tests for folder selection functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from PyQt6.QtWidgets import QMessageBox

from src.ui.main_window import MainWindow


@pytest.mark.ui
class TestFolderSelection:
    """Test folder selection functionality."""

    def test_folder_selection_ui_components_exist(self, qapp):
        """Test that folder selection UI components are present."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            window = MainWindow()
            
            # Check for folder selection components
            assert hasattr(window, 'folder_path_edit')
            assert hasattr(window, 'choose_folder_button')
            assert hasattr(window, 'scan_button')
            assert hasattr(window, 'selected_folder_path')
            
            # Check initial state
            assert window.selected_folder_path is None
            assert not window.scan_button.isEnabled()
            assert window.folder_path_edit.isReadOnly()

    def test_choose_folder_button_opens_dialog(self, qapp):
        """Test that choose folder button opens file dialog."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            with patch('src.ui.main_window.QFileDialog.getExistingDirectory') as mock_dialog:
                mock_dialog.return_value = ""  # User cancelled
                
                window = MainWindow()
                window.on_choose_folder_clicked()
                
                # Verify dialog was called with correct parameters
                mock_dialog.assert_called_once()
                args = mock_dialog.call_args[0]
                assert args[0] == window  # parent
                assert args[1] == "Select Folder to Scan"  # caption

    def test_valid_folder_selection_updates_ui(self, qapp, tmp_path):
        """Test that selecting a valid folder updates the UI correctly."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            window = MainWindow()
            test_folder = str(tmp_path)
            
            window.set_selected_folder(test_folder)
            
            # Verify UI updates
            assert window.selected_folder_path == test_folder
            assert window.folder_path_edit.text() == test_folder
            assert window.scan_button.isEnabled()
            
            # Verify logging
            mock_logger_instance.info.assert_called_with(
                f"Successfully set selected folder: {test_folder}"
            )

    def test_nonexistent_folder_shows_error(self, qapp):
        """Test that selecting a non-existent folder shows error."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            with patch.object(MainWindow, 'show_error_message') as mock_error:
                window = MainWindow()
                nonexistent_path = "/this/path/does/not/exist"
                
                window.set_selected_folder(nonexistent_path)
                
                # Verify error was shown
                mock_error.assert_called_once()
                args = mock_error.call_args[0]
                assert args[0] == "Path Error"
                assert nonexistent_path in args[1]
                
                # Verify UI state unchanged
                assert window.selected_folder_path is None
                assert not window.scan_button.isEnabled()

    def test_file_instead_of_folder_shows_error(self, qapp, tmp_path):
        """Test that selecting a file instead of folder shows error."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            # Create a temporary file
            test_file = tmp_path / "test_file.txt"
            test_file.write_text("test content")
            
            with patch.object(MainWindow, 'show_error_message') as mock_error:
                window = MainWindow()
                
                window.set_selected_folder(str(test_file))
                
                # Verify error was shown
                mock_error.assert_called_once()
                args = mock_error.call_args[0]
                assert args[0] == "Path Error"
                assert "not a directory" in args[1]

    def test_permission_denied_shows_error(self, qapp):
        """Test that permission denied shows appropriate error."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            with patch('pathlib.Path.exists') as mock_exists:
                with patch('pathlib.Path.is_dir') as mock_is_dir:
                    with patch('os.access') as mock_access:
                        with patch.object(MainWindow, 'show_error_message') as mock_error:
                            mock_exists.return_value = True
                            mock_is_dir.return_value = True
                            mock_access.return_value = False  # Permission denied
                            
                            window = MainWindow()
                            test_path = "/restricted/folder"
                            
                            window.set_selected_folder(test_path)
                            
                            # Verify error was shown
                            mock_error.assert_called_once()
                            args = mock_error.call_args[0]
                            assert args[0] == "Permission Error"
                            assert "permissions" in args[1].lower()

    def test_scan_button_behavior_with_folder_selection(self, qapp, tmp_path):
        """Test scan button behavior changes with folder selection."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            window = MainWindow()
            
            # Initially disabled
            assert not window.scan_button.isEnabled()
            
            # Enable after selecting folder
            window.set_selected_folder(str(tmp_path))
            assert window.scan_button.isEnabled()
            
            # Test scan button click with folder selected
            window.on_scan_clicked()
            mock_logger_instance.info.assert_called_with(
                f"Scan button clicked for folder: {str(tmp_path)}"
            )

    def test_error_message_dialog_creation(self, qapp):
        """Test that error message dialog is created correctly."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            with patch('src.ui.main_window.QMessageBox') as mock_msg_box:
                mock_box_instance = MagicMock()
                mock_msg_box.return_value = mock_box_instance
                
                window = MainWindow()
                
                window.show_error_message("Test Title", "Test Message")
                
                # Verify message box was configured correctly
                mock_msg_box.assert_called_once_with(window)
                # Note: We can't easily test the enum value due to mocking
                assert mock_box_instance.setIcon.called
                mock_box_instance.setWindowTitle.assert_called_once_with("Test Title")
                mock_box_instance.setText.assert_called_once_with("Test Message")
                mock_box_instance.exec.assert_called_once()

    def test_folder_selection_state_persistence(self, qapp, tmp_path):
        """Test that folder selection state is maintained during session."""
        with patch('src.ui.main_window.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            window = MainWindow()
            test_folder = str(tmp_path)
            
            # Select folder
            window.set_selected_folder(test_folder)
            
            # Verify state is maintained
            assert window.selected_folder_path == test_folder
            assert window.folder_path_edit.text() == test_folder
            assert window.scan_button.isEnabled()
            
            # Simulate other UI operations (state should persist)
            window.on_settings_clicked()
            
            # State should still be maintained
            assert window.selected_folder_path == test_folder
            assert window.folder_path_edit.text() == test_folder
            assert window.scan_button.isEnabled()
