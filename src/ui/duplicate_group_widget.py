"""
UI components for displaying duplicate image groups with thumbnails.

Provides widgets for showing grouped duplicate/similar images with visual
thumbnails, similarity information, and group management controls.
"""

from pathlib import Path
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSizePolicy, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QPalette

from ..utils.logger import get_logger
from .thumbnail_manager import ThumbnailManager


class ThumbnailWidget(QLabel):
    """Widget for displaying a single thumbnail with image information."""
    
    clicked = pyqtSignal(str)  # image_path
    
    def __init__(self, image_path: str, thumbnail_manager: ThumbnailManager, 
                 thumbnail_size: tuple = (150, 150)):
        super().__init__()
        self.image_path = image_path
        self.thumbnail_manager = thumbnail_manager
        self.thumbnail_size = thumbnail_size
        self.logger = get_logger(__name__)
        
        # Set up widget properties
        self.setFixedSize(thumbnail_size[0] + 20, thumbnail_size[1] + 40)  # Extra space for label
        self.setFrameStyle(QFrame.Shape.Box)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            ThumbnailWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }
            ThumbnailWidget:hover {
                border-color: #007AFF;
                background-color: #f0f8ff;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(thumbnail_size[0], thumbnail_size[1])
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        layout.addWidget(self.thumbnail_label)
        
        # File name label
        filename = Path(image_path).name
        self.name_label = QLabel(filename)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("border: none; font-size: 10px; color: #666;")
        layout.addWidget(self.name_label)
        
        self.setLayout(layout)
        
        # Load thumbnail
        self.load_thumbnail()
    
    def load_thumbnail(self):
        """Load thumbnail for this image."""
        def on_thumbnail_ready(image_path: str, thumbnail: QPixmap):
            if image_path == self.image_path:
                self.thumbnail_label.setPixmap(thumbnail)
        
        def on_thumbnail_error(image_path: str, error_message: str):
            if image_path == self.image_path:
                placeholder = self.thumbnail_manager.generator.create_placeholder_thumbnail(
                    self.thumbnail_size, "Error"
                )
                self.thumbnail_label.setPixmap(placeholder)
                self.logger.warning(f"Failed to load thumbnail for {image_path}: {error_message}")
        
        # Try to get thumbnail (may return placeholder if loading async)
        thumbnail = self.thumbnail_manager.get_thumbnail(
            self.image_path, 
            self.thumbnail_size,
            callback=on_thumbnail_ready,
            error_callback=on_thumbnail_error
        )
        
        if thumbnail:
            self.thumbnail_label.setPixmap(thumbnail)
    
    def mousePressEvent(self, event):
        """Handle mouse click to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class DuplicateGroupWidget(QGroupBox):
    """Widget for displaying a group of duplicate/similar images."""
    
    def __init__(self, duplicate_group: Dict, thumbnail_manager: ThumbnailManager):
        super().__init__()
        self.duplicate_group = duplicate_group
        self.thumbnail_manager = thumbnail_manager
        self.logger = get_logger(__name__)
        self.is_expanded = True
        
        # Set up group box
        self.setup_group_header()
        self.setup_group_content()
        
        # Apply styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def setup_group_header(self):
        """Set up the group header with information and controls."""
        algorithm = self.duplicate_group.get('algorithm', 'unknown')
        image_count = self.duplicate_group.get('image_count', 0)
        total_size = self.duplicate_group.get('total_size', 0)
        
        # Algorithm display name
        algorithm_names = {
            'dhash': 'Exact Duplicates (Hash)',
            'ahash': 'Exact Duplicates (Hash)', 
            'cnn': 'Similar Images (CNN)'
        }
        algorithm_display = algorithm_names.get(algorithm, algorithm)
        
        # Create header text
        size_str = self.format_file_size(total_size)
        header_text = f"{algorithm_display} - {image_count} images ({size_str})"
        
        # Add similarity info for CNN groups
        if algorithm == 'cnn' and 'similarity_score' in self.duplicate_group:
            similarity = self.duplicate_group['similarity_score'] * 100
            confidence = self.duplicate_group.get('confidence_level', 'unknown')
            header_text += f" - {similarity:.1f}% similar ({confidence} confidence)"
        
        self.setTitle(header_text)
    
    def setup_group_content(self):
        """Set up the group content with thumbnails."""
        # Main layout
        layout = QVBoxLayout()
        
        # Control buttons layout
        controls_layout = QHBoxLayout()
        
        # Expand/Collapse button
        self.expand_button = QPushButton("Collapse")
        self.expand_button.clicked.connect(self.toggle_expanded)
        self.expand_button.setMaximumWidth(100)
        controls_layout.addWidget(self.expand_button)
        
        controls_layout.addStretch()  # Push button to the left
        
        layout.addLayout(controls_layout)
        
        # Thumbnail scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(200)  # Limit height
        
        # Thumbnail container
        thumbnail_container = QWidget()
        thumbnail_layout = QHBoxLayout()
        thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        thumbnail_layout.setSpacing(10)
        
        # Add thumbnails for each image
        images = self.duplicate_group.get('images', [])
        for image_info in images:
            image_path = image_info.get('path', '')
            if image_path:
                thumbnail_widget = ThumbnailWidget(
                    image_path, 
                    self.thumbnail_manager,
                    thumbnail_size=(120, 120)
                )
                thumbnail_widget.clicked.connect(self.on_thumbnail_clicked)
                thumbnail_layout.addWidget(thumbnail_widget)
        
        thumbnail_layout.addStretch()  # Push thumbnails to the left
        thumbnail_container.setLayout(thumbnail_layout)
        self.scroll_area.setWidget(thumbnail_container)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
    
    def toggle_expanded(self):
        """Toggle the expanded state of the group."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.scroll_area.show()
            self.expand_button.setText("Collapse")
        else:
            self.scroll_area.hide()
            self.expand_button.setText("Expand")
    
    def on_thumbnail_clicked(self, image_path: str):
        """Handle thumbnail click."""
        self.logger.info(f"Thumbnail clicked: {image_path}")
        # TODO: Implement image preview or selection functionality
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class DuplicateGroupsDisplayWidget(QWidget):
    """Widget for displaying multiple duplicate groups with lazy loading."""
    
    def __init__(self, thumbnail_manager: ThumbnailManager):
        super().__init__()
        self.thumbnail_manager = thumbnail_manager
        self.logger = get_logger(__name__)
        self.group_widgets: List[DuplicateGroupWidget] = []
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Header
        self.header_label = QLabel("Duplicate Groups")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        self.header_label.setFont(header_font)
        layout.addWidget(self.header_label)
        
        # Scroll area for groups
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for group widgets
        self.groups_container = QWidget()
        self.groups_layout = QVBoxLayout()
        self.groups_layout.setContentsMargins(5, 5, 5, 5)
        self.groups_layout.setSpacing(10)
        self.groups_container.setLayout(self.groups_layout)
        
        self.scroll_area.setWidget(self.groups_container)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def display_duplicate_groups(self, duplicate_groups: List[Dict]):
        """
        Display duplicate groups with thumbnails.
        
        Args:
            duplicate_groups: List of duplicate group dictionaries
        """
        self.logger.info(f"Displaying {len(duplicate_groups)} duplicate groups")
        
        # Clear existing groups
        self.clear_groups()
        
        if not duplicate_groups:
            # Show no results message
            no_results_label = QLabel("No duplicate groups found.")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            self.groups_layout.addWidget(no_results_label)
            return
        
        # Update header
        total_images = sum(group.get('image_count', 0) for group in duplicate_groups)
        self.header_label.setText(f"Duplicate Groups ({len(duplicate_groups)} groups, {total_images} images)")
        
        # Sort groups by priority (exact duplicates first, then by similarity)
        sorted_groups = self.sort_groups_by_priority(duplicate_groups)
        
        # Create widgets for each group
        for group_dict in sorted_groups:
            try:
                group_widget = DuplicateGroupWidget(group_dict, self.thumbnail_manager)
                self.group_widgets.append(group_widget)
                self.groups_layout.addWidget(group_widget)
            except Exception as e:
                self.logger.error(f"Error creating group widget: {e}")
        
        # Add stretch to push groups to top
        self.groups_layout.addStretch()
    
    def sort_groups_by_priority(self, duplicate_groups: List[Dict]) -> List[Dict]:
        """
        Sort duplicate groups by priority for display.
        
        Args:
            duplicate_groups: List of duplicate group dictionaries
            
        Returns:
            Sorted list with highest priority groups first
        """
        def get_priority(group):
            algorithm = group.get('algorithm', 'unknown')
            
            # Hash-based duplicates have highest priority
            if algorithm in ['dhash', 'ahash']:
                return (0, -group.get('image_count', 0))  # Sort by image count desc
            
            # CNN-based duplicates sorted by similarity score
            elif algorithm == 'cnn':
                similarity = group.get('similarity_score', 0)
                return (1, -similarity, -group.get('image_count', 0))
            
            # Unknown algorithms last
            else:
                return (2, -group.get('image_count', 0))
        
        return sorted(duplicate_groups, key=get_priority)
    
    def clear_groups(self):
        """Clear all displayed groups."""
        # Remove all group widgets
        for group_widget in self.group_widgets:
            self.groups_layout.removeWidget(group_widget)
            group_widget.deleteLater()
        
        self.group_widgets.clear()
        
        # Clear any remaining widgets in layout
        while self.groups_layout.count():
            child = self.groups_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def collapse_all_groups(self):
        """Collapse all group widgets."""
        for group_widget in self.group_widgets:
            if group_widget.is_expanded:
                group_widget.toggle_expanded()
    
    def expand_all_groups(self):
        """Expand all group widgets."""
        for group_widget in self.group_widgets:
            if not group_widget.is_expanded:
                group_widget.toggle_expanded()
