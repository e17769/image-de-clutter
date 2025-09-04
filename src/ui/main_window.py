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
        scan_button = QPushButton("Scan for Duplicates")
        scan_button.setEnabled(False)  # Will be enabled in future stories
        scan_button.clicked.connect(self.on_scan_clicked)
        button_layout.addWidget(scan_button)

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

    def on_scan_clicked(self):
        """Handle scan button click (placeholder)."""
        self.logger.info("Scan button clicked (not implemented yet)")
        self.status_bar.showMessage("Scan functionality will be implemented in Story 1.4")

    def on_settings_clicked(self):
        """Handle settings button click (placeholder)."""
        self.logger.info("Settings button clicked (not implemented yet)")
        self.status_bar.showMessage("Settings functionality will be implemented in future stories")

    def closeEvent(self, event):
        """Handle application close event."""
        self.logger.info("Application closing")
        event.accept()
