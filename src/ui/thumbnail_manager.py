"""
Thumbnail generation and caching system for image preview.

Provides efficient thumbnail generation with persistent caching and lazy loading
support for the Photo Archivist application.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image, ImageOps
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker, QTimer
from PyQt6.QtGui import QPixmap
import time

from ..utils.logger import get_logger


class ThumbnailGenerator:
    """Generates thumbnails with caching and error handling."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_cache_size: int = 1000):
        """
        Initialize thumbnail generator.
        
        Args:
            cache_dir: Directory for thumbnail cache (default: ~/.photo_archivist/thumbnails)
            max_cache_size: Maximum number of thumbnails to keep in cache
        """
        self.logger = get_logger(__name__)
        self.max_cache_size = max_cache_size
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".photo_archivist" / "thumbnails"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for quick access
        self.memory_cache: Dict[str, QPixmap] = {}
        self.cache_access_times: Dict[str, float] = {}
        
        # Supported image formats
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'
        }
        
        self.logger.info(f"Thumbnail generator initialized with cache dir: {cache_dir}")
    
    def get_cache_key(self, image_path: str, size: Tuple[int, int]) -> str:
        """
        Generate cache key for image and size combination.
        
        Args:
            image_path: Path to the image file
            size: Thumbnail size as (width, height)
            
        Returns:
            Cache key string
        """
        try:
            # Include file modification time in cache key for invalidation
            stat = Path(image_path).stat()
            mtime = str(int(stat.st_mtime))
            
            # Create hash from path, size, and modification time
            key_string = f"{image_path}:{size[0]}x{size[1]}:{mtime}"
            cache_key = hashlib.md5(key_string.encode()).hexdigest()
            
            return cache_key
            
        except (OSError, IOError) as e:
            self.logger.warning(f"Could not get file stats for {image_path}: {e}")
            # Fallback to path and size only
            key_string = f"{image_path}:{size[0]}x{size[1]}"
            return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cached thumbnail."""
        return self.cache_dir / f"{cache_key}.png"
    
    def generate_thumbnail(self, image_path: str, size: Tuple[int, int] = (150, 150)) -> Optional[QPixmap]:
        """
        Generate thumbnail for an image with caching.
        
        Args:
            image_path: Path to the image file
            size: Thumbnail size as (width, height)
            
        Returns:
            QPixmap thumbnail or None if generation failed
        """
        cache_key = self.get_cache_key(image_path, size)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            self.cache_access_times[cache_key] = time.time()
            return self.memory_cache[cache_key]
        
        # Check disk cache
        cache_path = self.get_cache_path(cache_key)
        if cache_path.exists():
            try:
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    self._add_to_memory_cache(cache_key, pixmap)
                    return pixmap
            except Exception as e:
                self.logger.warning(f"Could not load cached thumbnail {cache_path}: {e}")
        
        # Generate new thumbnail
        return self._generate_new_thumbnail(image_path, size, cache_key)
    
    def _generate_new_thumbnail(self, image_path: str, size: Tuple[int, int], cache_key: str) -> Optional[QPixmap]:
        """Generate a new thumbnail and cache it."""
        try:
            self.logger.debug(f"Generating thumbnail for {image_path}")
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create a centered thumbnail on white background
                thumb = Image.new('RGB', size, (255, 255, 255))
                
                # Calculate position to center the image
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                thumb.paste(img, (x, y))
                
                # Save to cache
                cache_path = self.get_cache_path(cache_key)
                thumb.save(cache_path, 'PNG', optimize=True)
                
                # Convert to QPixmap
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    self._add_to_memory_cache(cache_key, pixmap)
                    return pixmap
                
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
            return None
        
        return None
    
    def _add_to_memory_cache(self, cache_key: str, pixmap: QPixmap):
        """Add thumbnail to memory cache with LRU eviction."""
        # Remove oldest entries if cache is full
        while len(self.memory_cache) >= self.max_cache_size:
            # Find oldest entry
            oldest_key = min(self.cache_access_times.keys(), 
                           key=lambda k: self.cache_access_times[k])
            
            del self.memory_cache[oldest_key]
            del self.cache_access_times[oldest_key]
        
        # Add new entry
        self.memory_cache[cache_key] = pixmap
        self.cache_access_times[cache_key] = time.time()
    
    def create_placeholder_thumbnail(self, size: Tuple[int, int] = (150, 150), 
                                   text: str = "Loading...") -> QPixmap:
        """
        Create a placeholder thumbnail for loading or error states.
        
        Args:
            size: Thumbnail size as (width, height)
            text: Text to display on placeholder
            
        Returns:
            QPixmap placeholder thumbnail
        """
        from PyQt6.QtGui import QPainter, QFont, QColor
        from PyQt6.QtCore import Qt
        
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(128, 128, 128))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return pixmap
    
    def cleanup_cache(self, max_age_days: int = 30):
        """
        Clean up old cached thumbnails.
        
        Args:
            max_age_days: Maximum age in days for cached thumbnails
        """
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            cleaned_count = 0
            
            for cache_file in self.cache_dir.glob("*.png"):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old cached thumbnails")
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")


class ThumbnailWorkerThread(QThread):
    """Worker thread for generating thumbnails in background."""
    
    thumbnail_ready = pyqtSignal(str, QPixmap)  # image_path, thumbnail
    thumbnail_error = pyqtSignal(str, str)      # image_path, error_message
    
    def __init__(self, generator: ThumbnailGenerator):
        super().__init__()
        self.generator = generator
        self.logger = get_logger(__name__)
        self.request_queue = []
        self.mutex = QMutex()
        self.is_running = False
    
    def request_thumbnail(self, image_path: str, size: Tuple[int, int] = (150, 150)):
        """Request thumbnail generation for an image."""
        with QMutexLocker(self.mutex):
            # Avoid duplicate requests
            request = (image_path, size)
            if request not in self.request_queue:
                self.request_queue.append(request)
                
                # Start thread if not running
                if not self.is_running:
                    self.start()
    
    def run(self):
        """Process thumbnail generation requests."""
        self.is_running = True
        
        while True:
            # Get next request
            with QMutexLocker(self.mutex):
                if not self.request_queue:
                    break
                image_path, size = self.request_queue.pop(0)
            
            try:
                # Generate thumbnail
                thumbnail = self.generator.generate_thumbnail(image_path, size)
                
                if thumbnail and not thumbnail.isNull():
                    self.thumbnail_ready.emit(image_path, thumbnail)
                else:
                    self.thumbnail_error.emit(image_path, "Failed to generate thumbnail")
                    
            except Exception as e:
                error_msg = f"Thumbnail generation error: {str(e)}"
                self.logger.error(f"Error generating thumbnail for {image_path}: {e}")
                self.thumbnail_error.emit(image_path, error_msg)
        
        self.is_running = False


class ThumbnailManager:
    """Manages thumbnail generation and caching with lazy loading support."""
    
    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize thumbnail manager.
        
        Args:
            max_cache_size: Maximum number of thumbnails to keep in memory cache
        """
        self.logger = get_logger(__name__)
        self.generator = ThumbnailGenerator(max_cache_size=max_cache_size)
        self.worker_thread = ThumbnailWorkerThread(self.generator)
        
        # Connect worker thread signals
        self.worker_thread.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.worker_thread.thumbnail_error.connect(self._on_thumbnail_error)
        
        # Callbacks for thumbnail completion
        self.ready_callbacks: Dict[str, list] = {}
        self.error_callbacks: Dict[str, list] = {}
        
        self.logger.info("Thumbnail manager initialized")
    
    def get_thumbnail(self, image_path: str, size: Tuple[int, int] = (150, 150), 
                     callback=None, error_callback=None) -> Optional[QPixmap]:
        """
        Get thumbnail for an image with optional callback for async loading.
        
        Args:
            image_path: Path to the image file
            size: Thumbnail size as (width, height)
            callback: Function to call when thumbnail is ready (for async loading)
            error_callback: Function to call if thumbnail generation fails
            
        Returns:
            QPixmap thumbnail if available immediately, None if loading async
        """
        # Try to get from cache first
        thumbnail = self.generator.generate_thumbnail(image_path, size)
        
        if thumbnail and not thumbnail.isNull():
            return thumbnail
        
        # If not in cache and callback provided, load asynchronously
        if callback:
            # Store callbacks
            if image_path not in self.ready_callbacks:
                self.ready_callbacks[image_path] = []
            self.ready_callbacks[image_path].append(callback)
            
            if error_callback:
                if image_path not in self.error_callbacks:
                    self.error_callbacks[image_path] = []
                self.error_callbacks[image_path].append(error_callback)
            
            # Request async generation
            self.worker_thread.request_thumbnail(image_path, size)
            
            # Return placeholder
            return self.generator.create_placeholder_thumbnail(size, "Loading...")
        
        # Return error placeholder if no callback
        return self.generator.create_placeholder_thumbnail(size, "Error")
    
    def _on_thumbnail_ready(self, image_path: str, thumbnail: QPixmap):
        """Handle completed thumbnail generation."""
        if image_path in self.ready_callbacks:
            for callback in self.ready_callbacks[image_path]:
                try:
                    callback(image_path, thumbnail)
                except Exception as e:
                    self.logger.error(f"Error in thumbnail ready callback: {e}")
            
            del self.ready_callbacks[image_path]
            
            # Clean up error callbacks too
            if image_path in self.error_callbacks:
                del self.error_callbacks[image_path]
    
    def _on_thumbnail_error(self, image_path: str, error_message: str):
        """Handle thumbnail generation errors."""
        if image_path in self.error_callbacks:
            for callback in self.error_callbacks[image_path]:
                try:
                    callback(image_path, error_message)
                except Exception as e:
                    self.logger.error(f"Error in thumbnail error callback: {e}")
            
            del self.error_callbacks[image_path]
            
            # Clean up ready callbacks too
            if image_path in self.ready_callbacks:
                del self.ready_callbacks[image_path]
    
    def cleanup_cache(self, max_age_days: int = 30):
        """Clean up old cached thumbnails."""
        self.generator.cleanup_cache(max_age_days)
    
    def shutdown(self):
        """Shutdown thumbnail manager and worker thread."""
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(5000)  # Wait up to 5 seconds
        
        self.logger.info("Thumbnail manager shutdown complete")
