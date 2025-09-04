"""
Main window for Photo Archivist application.

Provides the primary user interface for duplicate image detection and management.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QStatusBar,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..utils.logger import get_logger


class MainWindow(QMainWindow):
    """Main application window for Photo Archivist."""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("Initializing Photo Archivist main window")

        # Initialize state
        self.selected_folder_path = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Photo Archivist")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Add title
        title_label = QLabel("Photo Archivist")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Add subtitle
        subtitle_label = QLabel("Duplicate Image Detection and Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # Add folder selection section
        folder_group = QGroupBox("Folder Selection")
        folder_layout = QVBoxLayout()

        # Folder selection row
        folder_row = QHBoxLayout()

        # Folder path display
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("Select a folder to scan for duplicate images...")
        self.folder_path_edit.setReadOnly(True)
        folder_row.addWidget(self.folder_path_edit)

        # Choose folder button
        self.choose_folder_button = QPushButton("Choose Folder")
        self.choose_folder_button.clicked.connect(self.on_choose_folder_clicked)
        folder_row.addWidget(self.choose_folder_button)

        folder_layout.addLayout(folder_row)
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)

        # Add placeholder content area
        content_area = QTextEdit()
        content_area.setPlainText(
            "Welcome to Photo Archivist!\n\n"
            "This is the initial version of the application.\n"
            "Features will be added in subsequent development iterations:\n\n"
            "- Folder selection for image scanning\n"
            "- Duplicate image detection\n"
            "- Visual comparison interface\n"
            "- Archive management\n\n"
            "Application initialized successfully."
        )
        content_area.setReadOnly(True)
        main_layout.addWidget(content_area)

        # Add button area
        button_layout = QHBoxLayout()

        # Placeholder buttons for future functionality
        self.scan_button = QPushButton("Scan for Duplicates")
        self.scan_button.setEnabled(False)  # Will be enabled when folder is selected
        self.scan_button.clicked.connect(self.on_scan_clicked)
        button_layout.addWidget(self.scan_button)

        settings_button = QPushButton("Settings")
        settings_button.setEnabled(False)  # Will be enabled in future stories
        settings_button.clicked.connect(self.on_settings_clicked)
        button_layout.addWidget(settings_button)

        main_layout.addLayout(button_layout)

        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.logger.info("Main window UI initialized successfully")

    def on_choose_folder_clicked(self):
        """Handle choose folder button click."""
        self.logger.info("Choose folder button clicked")

        # Open native macOS folder picker
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Scan",
            "",  # Start from home directory
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )

        if folder_path:
            self.logger.info(f"User selected folder: {folder_path}")
            self.set_selected_folder(folder_path)
        else:
            self.logger.info("User cancelled folder selection")

    def set_selected_folder(self, folder_path):
        """Set the selected folder and update UI state."""
        from pathlib import Path
        import os

        try:
            # Validate the selected path
            path = Path(folder_path)

            # Check if path exists and is a directory
            if not path.exists():
                self.show_error_message(
                    "Path Error", f"The selected path does not exist:\n{folder_path}"
                )
                return

            if not path.is_dir():
                self.show_error_message(
                    "Path Error", f"The selected path is not a directory:\n{folder_path}"
                )
                return

            # Check if path is readable
            if not os.access(folder_path, os.R_OK):
                self.show_error_message(
                    "Permission Error",
                    f"Cannot read the selected directory. Please check permissions:\n{folder_path}",
                )
                return

            # Path is valid, update UI
            self.selected_folder_path = folder_path
            self.folder_path_edit.setText(folder_path)
            self.scan_button.setEnabled(True)

            self.status_bar.showMessage(f"Selected folder: {folder_path}")
            self.logger.info(f"Successfully set selected folder: {folder_path}")

        except Exception as e:
            self.logger.error(f"Error validating selected folder: {e}", exc_info=True)
            self.show_error_message(
                "Validation Error",
                f"An error occurred while validating the selected folder:\n{str(e)}",
            )

    def show_error_message(self, title, message):
        """Show an error message dialog to the user."""
        self.logger.warning(f"Showing error dialog - {title}: {message}")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def on_scan_clicked(self):
        """Handle scan button click (placeholder)."""
        if self.selected_folder_path:
            self.logger.info(f"Scan button clicked for folder: {self.selected_folder_path}")
            message = f"Scan will be implemented in Story 1.4 for: {self.selected_folder_path}"
            self.status_bar.showMessage(message)
        else:
            self.logger.warning("Scan button clicked but no folder selected")
            self.status_bar.showMessage("Please select a folder first")

    def on_settings_clicked(self):
        """Handle settings button click (placeholder)."""
        self.logger.info("Settings button clicked (not implemented yet)")
        self.status_bar.showMessage("Settings functionality will be implemented in future stories")

    def closeEvent(self, event):
        """Handle application close event."""
        self.logger.info("Application closing")
        event.accept()
