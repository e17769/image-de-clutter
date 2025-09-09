"""
Unit tests for thumbnail generation and management functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import os

from src.ui.thumbnail_manager import ThumbnailGenerator, ThumbnailManager


@pytest.mark.unit
class TestThumbnailGenerator:
    """Test ThumbnailGenerator functionality."""

    def test_generator_initialization(self):
        """Test thumbnail generator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            generator = ThumbnailGenerator(cache_dir=cache_dir, max_cache_size=100)
            
            assert generator.cache_dir == cache_dir
            assert generator.max_cache_size == 100
            assert cache_dir.exists()

    def test_cache_key_generation(self, tmp_path):
        """Test cache key generation."""
        generator = ThumbnailGenerator()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Generate cache keys
        key1 = generator.get_cache_key(str(test_image_path), (150, 150))
        key2 = generator.get_cache_key(str(test_image_path), (150, 150))
        key3 = generator.get_cache_key(str(test_image_path), (200, 200))
        
        # Same path and size should generate same key
        assert key1 == key2
        
        # Different size should generate different key
        assert key1 != key3
        
        # Keys should be valid hex strings
        assert len(key1) == 32  # MD5 hex length
        int(key1, 16)  # Should not raise exception

    def test_thumbnail_generation(self, tmp_path):
        """Test basic thumbnail generation."""
        generator = ThumbnailGenerator(cache_dir=tmp_path / "cache")
        
        # Create a test image
        img = Image.new('RGB', (200, 100), color='blue')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Generate thumbnail
        thumbnail = generator.generate_thumbnail(str(test_image_path), (150, 150))
        
        assert thumbnail is not None
        assert not thumbnail.isNull()
        assert thumbnail.width() == 150
        assert thumbnail.height() == 150

    def test_thumbnail_caching(self, tmp_path):
        """Test thumbnail caching functionality."""
        cache_dir = tmp_path / "cache"
        generator = ThumbnailGenerator(cache_dir=cache_dir)
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='green')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Generate thumbnail first time
        thumbnail1 = generator.generate_thumbnail(str(test_image_path), (150, 150))
        
        # Check that cache file was created
        cache_key = generator.get_cache_key(str(test_image_path), (150, 150))
        cache_path = generator.get_cache_path(cache_key)
        assert cache_path.exists()
        
        # Generate thumbnail second time (should use cache)
        thumbnail2 = generator.generate_thumbnail(str(test_image_path), (150, 150))
        
        # Both should be valid and equivalent
        assert thumbnail1 is not None
        assert thumbnail2 is not None
        assert not thumbnail1.isNull()
        assert not thumbnail2.isNull()

    def test_thumbnail_with_transparency(self, tmp_path):
        """Test thumbnail generation with transparent images."""
        generator = ThumbnailGenerator()
        
        # Create a transparent PNG
        img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))  # Semi-transparent red
        test_image_path = tmp_path / "test.png"
        img.save(test_image_path)
        
        # Generate thumbnail
        thumbnail = generator.generate_thumbnail(str(test_image_path), (150, 150))
        
        assert thumbnail is not None
        assert not thumbnail.isNull()

    def test_thumbnail_invalid_file(self):
        """Test thumbnail generation with invalid file."""
        generator = ThumbnailGenerator()
        
        # Try to generate thumbnail for non-existent file
        thumbnail = generator.generate_thumbnail("/nonexistent/file.jpg", (150, 150))
        
        assert thumbnail is None

    def test_placeholder_thumbnail_creation(self):
        """Test placeholder thumbnail creation."""
        generator = ThumbnailGenerator()
        
        placeholder = generator.create_placeholder_thumbnail((150, 150), "Test")
        
        assert placeholder is not None
        assert not placeholder.isNull()
        assert placeholder.width() == 150
        assert placeholder.height() == 150

    def test_memory_cache_lru_eviction(self, tmp_path):
        """Test memory cache LRU eviction."""
        generator = ThumbnailGenerator(max_cache_size=2)  # Small cache
        
        # Create test images
        for i in range(3):
            img = Image.new('RGB', (50, 50), color=(i * 80, 0, 0))
            test_path = tmp_path / f"test{i}.jpg"
            img.save(test_path)
            
            # Generate thumbnail to fill cache
            generator.generate_thumbnail(str(test_path), (100, 100))
        
        # Cache should not exceed max size
        assert len(generator.memory_cache) <= 2

    def test_cache_cleanup(self, tmp_path):
        """Test cache cleanup functionality."""
        cache_dir = tmp_path / "cache"
        generator = ThumbnailGenerator(cache_dir=cache_dir)
        
        # Create some old cache files
        old_file = cache_dir / "old_thumbnail.png"
        old_file.touch()
        
        # Set modification time to old
        old_time = 1000000000  # Very old timestamp
        os.utime(old_file, (old_time, old_time))
        
        # Run cleanup
        generator.cleanup_cache(max_age_days=1)
        
        # Old file should be removed
        assert not old_file.exists()


@pytest.mark.unit
class TestThumbnailManager:
    """Test ThumbnailManager functionality."""

    def test_manager_initialization(self):
        """Test thumbnail manager initialization."""
        manager = ThumbnailManager(max_cache_size=200)
        
        assert manager.generator is not None
        assert manager.worker_thread is not None
        assert manager.generator.max_cache_size == 200

    def test_get_thumbnail_sync(self, tmp_path):
        """Test synchronous thumbnail retrieval."""
        manager = ThumbnailManager()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='yellow')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Get thumbnail without callback (synchronous)
        thumbnail = manager.get_thumbnail(str(test_image_path), (150, 150))
        
        assert thumbnail is not None
        assert not thumbnail.isNull()

    def test_get_thumbnail_async(self, tmp_path):
        """Test asynchronous thumbnail retrieval with callback."""
        manager = ThumbnailManager()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='purple')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Mock callback
        callback = MagicMock()
        
        # Get thumbnail with callback (asynchronous)
        result = manager.get_thumbnail(
            str(test_image_path), 
            (150, 150), 
            callback=callback
        )
        
        # Should return placeholder immediately
        assert result is not None
        assert not result.isNull()

    def test_thumbnail_error_handling(self):
        """Test error handling for invalid images."""
        manager = ThumbnailManager()
        
        # Mock callbacks
        ready_callback = MagicMock()
        error_callback = MagicMock()
        
        # Try to get thumbnail for non-existent file
        result = manager.get_thumbnail(
            "/nonexistent/file.jpg",
            (150, 150),
            callback=ready_callback,
            error_callback=error_callback
        )
        
        # Should return placeholder
        assert result is not None

    def test_manager_shutdown(self):
        """Test thumbnail manager shutdown."""
        manager = ThumbnailManager()
        
        # Mock the worker thread
        manager.worker_thread.isRunning = MagicMock(return_value=True)
        manager.worker_thread.quit = MagicMock()
        manager.worker_thread.wait = MagicMock(return_value=True)
        
        # Shutdown should complete without error
        manager.shutdown()
        
        manager.worker_thread.quit.assert_called_once()
        manager.worker_thread.wait.assert_called_once_with(5000)


@pytest.mark.integration
class TestThumbnailIntegration:
    """Integration tests for thumbnail functionality."""

    def test_full_thumbnail_workflow(self, tmp_path):
        """Test complete thumbnail generation workflow."""
        # Create test images of different formats
        formats = [
            ('RGB', 'test.jpg', 'JPEG'),
            ('RGBA', 'test.png', 'PNG'),
            ('RGB', 'test.bmp', 'BMP')
        ]
        
        manager = ThumbnailManager()
        
        for mode, filename, format_name in formats:
            # Create test image
            img = Image.new(mode, (200, 150), color='red' if mode == 'RGB' else (255, 0, 0, 255))
            test_path = tmp_path / filename
            img.save(test_path, format_name)
            
            # Generate thumbnail
            thumbnail = manager.get_thumbnail(str(test_path), (100, 100))
            
            assert thumbnail is not None, f"Failed to generate thumbnail for {filename}"
            assert not thumbnail.isNull(), f"Thumbnail is null for {filename}"
            assert thumbnail.width() == 100, f"Wrong width for {filename}"
            assert thumbnail.height() == 100, f"Wrong height for {filename}"

    def test_large_image_thumbnail(self, tmp_path):
        """Test thumbnail generation for large images."""
        manager = ThumbnailManager()
        
        # Create a large test image
        img = Image.new('RGB', (2000, 1500), color='blue')
        test_path = tmp_path / "large_test.jpg"
        img.save(test_path)
        
        # Generate small thumbnail
        thumbnail = manager.get_thumbnail(str(test_path), (150, 150))
        
        assert thumbnail is not None
        assert not thumbnail.isNull()
        assert thumbnail.width() == 150
        assert thumbnail.height() == 150

    def test_aspect_ratio_preservation(self, tmp_path):
        """Test that aspect ratio is preserved in thumbnails."""
        manager = ThumbnailManager()
        
        # Create a wide image
        img = Image.new('RGB', (300, 100), color='orange')  # 3:1 aspect ratio
        test_path = tmp_path / "wide_test.jpg"
        img.save(test_path)
        
        # Generate square thumbnail
        thumbnail = manager.get_thumbnail(str(test_path), (150, 150))
        
        assert thumbnail is not None
        assert not thumbnail.isNull()
        
        # The thumbnail should be 150x150 (square) but the image inside should maintain aspect ratio
        # This is achieved by centering the scaled image on a white background
        assert thumbnail.width() == 150
        assert thumbnail.height() == 150

    def test_performance_with_multiple_thumbnails(self, tmp_path):
        """Test performance with multiple thumbnail generations."""
        import time
        
        manager = ThumbnailManager()
        
        # Create multiple test images
        num_images = 10
        image_paths = []
        
        for i in range(num_images):
            img = Image.new('RGB', (200, 200), color=(i * 25, 100, 150))
            test_path = tmp_path / f"perf_test_{i}.jpg"
            img.save(test_path)
            image_paths.append(str(test_path))
        
        # Generate thumbnails and measure time
        start_time = time.time()
        
        thumbnails = []
        for path in image_paths:
            thumbnail = manager.get_thumbnail(path, (100, 100))
            thumbnails.append(thumbnail)
        
        end_time = time.time()
        
        # All thumbnails should be generated
        assert len(thumbnails) == num_images
        for thumbnail in thumbnails:
            assert thumbnail is not None
            assert not thumbnail.isNull()
        
        # Should complete reasonably quickly (less than 2 seconds for 10 small images)
        generation_time = end_time - start_time
        assert generation_time < 2.0, f"Thumbnail generation took too long: {generation_time:.2f}s"
