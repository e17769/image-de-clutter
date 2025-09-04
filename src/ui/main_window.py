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
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

from ..utils.logger import get_logger
from ..file_operations.file_scanner import ImageFileScannerThread


class MainWindow(QMainWindow):
    """Main application window for Photo Archivist."""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("Initializing Photo Archivist main window")

        # Initialize state
        self.selected_folder_path = None
        self.discovered_files = []
        self.scan_statistics = {}
        self.scanner_thread = None

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

        # Add scan progress section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        # Progress label
        self.progress_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Add results section
        results_group = QGroupBox("Discovered Images")
        results_layout = QVBoxLayout()

        # Results summary
        self.results_summary = QLabel("No images discovered yet")
        results_layout.addWidget(self.results_summary)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Filename", "Path", "Size", "Type"])

        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setMaximumHeight(200)  # Limit height for now

        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # Add placeholder content area (reduced)
        content_area = QTextEdit()
        content_area.setPlainText(
            "Welcome to Photo Archivist!\n\n"
            "Steps to use the application:\n"
            "1. Select a folder containing images using 'Choose Folder'\n"
            "2. Click 'Scan for Duplicates' to discover images\n"
            "3. Review discovered images in the table below\n\n"
            "Supported formats: JPG, PNG, GIF, TIFF, WebP, HEIC, BMP, RAW (CR2, NEF, ARW, DNG)\n\n"
            "Next features (coming in future stories):\n"
            "- Duplicate detection and similarity analysis\n"
            "- Visual comparison interface\n"
            "- Archive management"
        )
        content_area.setReadOnly(True)
        main_layout.addWidget(content_area)

        # Add button area
        button_layout = QHBoxLayout()

        # Scan button (now functional for image discovery)
        self.scan_button = QPushButton("Scan for Images")
        self.scan_button.setEnabled(False)  # Will be enabled when folder is selected
        self.scan_button.clicked.connect(self.on_scan_clicked)
        button_layout.addWidget(self.scan_button)

        # Cancel button (for cancelling scans)
        self.cancel_button = QPushButton("Cancel Scan")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.on_cancel_scan)
        button_layout.addWidget(self.cancel_button)

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
        """Handle scan button click - start image discovery."""
        if not self.selected_folder_path:
            self.logger.warning("Scan button clicked but no folder selected")
            self.status_bar.showMessage("Please select a folder first")
            return

        self.logger.info(f"Starting image discovery scan for: {self.selected_folder_path}")

        # Clear previous results
        self.discovered_files = []
        self.scan_statistics = {}
        self.results_table.setRowCount(0)
        self.results_summary.setText("Scanning in progress...")

        # Update UI state
        self.scan_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.choose_folder_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_label.setText("Discovering images...")

        # Start scanner thread
        self.scanner_thread = ImageFileScannerThread(self.selected_folder_path)
        self.scanner_thread.progress_update.connect(self.on_scan_progress)
        self.scanner_thread.scan_completed.connect(self.on_scan_completed)
        self.scanner_thread.scan_error.connect(self.on_scan_error)
        self.scanner_thread.start()

        self.status_bar.showMessage(f"Scanning for images in: {self.selected_folder_path}")

    def on_cancel_scan(self):
        """Handle cancel scan button click."""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.logger.info("User requested scan cancellation")
            self.scanner_thread.cancel_scan()
            self.on_scan_cancelled()

    def on_scan_progress(self, file_count: int, current_file: str):
        """Handle scan progress updates."""
        self.progress_label.setText(f"Found {file_count} images... {current_file}")
        self.status_bar.showMessage(f"Discovered {file_count} images so far...")

    def on_scan_completed(self, discovered_files: list, statistics: dict):
        """Handle scan completion."""
        self.logger.info(f"Scan completed: {len(discovered_files)} images discovered")

        # Store results
        self.discovered_files = discovered_files
        self.scan_statistics = statistics

        # Update UI
        self.populate_results_table()
        self.update_results_summary()
        self.reset_scan_ui()

        # Update status
        total_files = statistics.get("total_files", 0)
        scan_time = statistics.get("scan_time", 0)
        self.status_bar.showMessage(
            f"Scan completed: {total_files} images found in {scan_time:.1f}s"
        )

    def on_scan_error(self, error_message: str):
        """Handle scan error."""
        self.logger.error(f"Scan error: {error_message}")
        self.show_error_message(
            "Scan Error", f"An error occurred during scanning:\n{error_message}"
        )
        self.reset_scan_ui()
        self.status_bar.showMessage("Scan failed")

    def on_scan_cancelled(self):
        """Handle scan cancellation."""
        self.logger.info("Scan was cancelled")
        self.reset_scan_ui()
        self.status_bar.showMessage("Scan cancelled")

    def reset_scan_ui(self):
        """Reset UI state after scan completion/cancellation."""
        self.scan_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.choose_folder_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Ready to scan")

    def populate_results_table(self):
        """Populate the results table with discovered files."""
        self.results_table.setRowCount(len(self.discovered_files))

        for row, file_info in enumerate(self.discovered_files):
            # Extract filename from path
            filename = Path(file_info["path"]).name

            # Format file size
            size_bytes = file_info["size"]
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

            # Set table items
            self.results_table.setItem(row, 0, QTableWidgetItem(filename))
            self.results_table.setItem(row, 1, QTableWidgetItem(file_info["path"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(size_str))
            self.results_table.setItem(row, 3, QTableWidgetItem(file_info["extension"].upper()))

    def update_results_summary(self):
        """Update the results summary label."""
        if not self.scan_statistics:
            return

        total_files = self.scan_statistics.get("total_files", 0)
        total_size = self.scan_statistics.get("total_size", 0)
        extensions = self.scan_statistics.get("extensions_found", [])

        # Format total size
        if total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{total_size / (1024 * 1024 * 1024):.1f} GB"

        extensions_str = ", ".join(ext.upper() for ext in extensions[:5])  # Show first 5
        if len(extensions) > 5:
            extensions_str += f" and {len(extensions) - 5} more"

        summary = f"Found {total_files} images ({size_str}) - Types: {extensions_str}"
        self.results_summary.setText(summary)

    def on_settings_clicked(self):
        """Handle settings button click (placeholder)."""
        self.logger.info("Settings button clicked (not implemented yet)")
        self.status_bar.showMessage("Settings functionality will be implemented in future stories")

    def closeEvent(self, event):
        """Handle application close event."""
        self.logger.info("Application closing")
        event.accept()
