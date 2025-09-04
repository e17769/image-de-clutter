"""
Unit tests for file scanner functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import time

from src.file_operations.file_scanner import ImageFileScanner, ImageFileScannerThread


@pytest.mark.unit
class TestImageFileScanner:
    """Test ImageFileScanner functionality."""

    def test_supported_extensions_includes_all_formats(self):
        """Test that scanner supports all required image formats."""
        scanner = ImageFileScanner()
        
        # Common formats
        assert '.jpg' in scanner.SUPPORTED_EXTENSIONS
        assert '.jpeg' in scanner.SUPPORTED_EXTENSIONS
        assert '.png' in scanner.SUPPORTED_EXTENSIONS
        assert '.gif' in scanner.SUPPORTED_EXTENSIONS
        assert '.tiff' in scanner.SUPPORTED_EXTENSIONS
        assert '.webp' in scanner.SUPPORTED_EXTENSIONS
        assert '.heic' in scanner.SUPPORTED_EXTENSIONS
        assert '.bmp' in scanner.SUPPORTED_EXTENSIONS
        
        # RAW formats
        assert '.cr2' in scanner.SUPPORTED_EXTENSIONS
        assert '.nef' in scanner.SUPPORTED_EXTENSIONS
        assert '.arw' in scanner.SUPPORTED_EXTENSIONS
        assert '.dng' in scanner.SUPPORTED_EXTENSIONS

    def test_is_image_file_detection(self):
        """Test image file detection logic."""
        scanner = ImageFileScanner()
        
        # Test supported formats
        assert scanner._is_image_file(Path("photo.jpg"))
        assert scanner._is_image_file(Path("photo.JPEG"))  # Case insensitive
        assert scanner._is_image_file(Path("photo.png"))
        assert scanner._is_image_file(Path("photo.CR2"))  # RAW format
        
        # Test unsupported formats
        assert not scanner._is_image_file(Path("document.txt"))
        assert not scanner._is_image_file(Path("video.mp4"))
        assert not scanner._is_image_file(Path("archive.zip"))

    def test_should_skip_file_logic(self):
        """Test file skipping logic."""
        scanner = ImageFileScanner()
        
        # Should skip hidden files
        assert scanner._should_skip_file(Path(".hidden_file.jpg"))
        assert scanner._should_skip_file(Path(".DS_Store"))
        
        # Should skip system files
        assert scanner._should_skip_file(Path("Thumbs.db"))
        assert scanner._should_skip_file(Path("desktop.ini"))
        
        # Should not skip regular files
        assert not scanner._should_skip_file(Path("photo.jpg"))
        assert not scanner._should_skip_file(Path("image.png"))

    def test_should_skip_directory_logic(self):
        """Test directory skipping logic."""
        scanner = ImageFileScanner()
        
        # Should skip system directories
        assert scanner._should_skip_directory(Path("/System/Library"))
        assert scanner._should_skip_directory(Path("/Library/Caches"))
        assert scanner._should_skip_directory(Path("/usr/bin"))
        
        # Should skip hidden directories
        assert scanner._should_skip_directory(Path("/home/user/.hidden"))
        assert scanner._should_skip_directory(Path("/path/.git"))
        
        # Should skip development directories
        assert scanner._should_skip_directory(Path("/project/__pycache__"))
        assert scanner._should_skip_directory(Path("/project/node_modules"))
        
        # Should not skip regular directories
        assert not scanner._should_skip_directory(Path("/Users/photos"))
        assert not scanner._should_skip_directory(Path("/home/documents"))

    def test_scan_directory_with_images(self, tmp_path):
        """Test scanning directory containing image files."""
        scanner = ImageFileScanner()
        
        # Create test image files
        (tmp_path / "photo1.jpg").write_text("fake image content")
        (tmp_path / "photo2.png").write_text("fake image content")
        (tmp_path / "document.txt").write_text("not an image")
        
        # Create subdirectory with images
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "photo3.gif").write_text("fake image content")
        
        # Scan directory
        results = list(scanner.scan_directory(str(tmp_path)))
        
        # Should find 3 image files
        assert len(results) == 3
        
        # Check that all results are image files
        found_files = {Path(file_path).name for file_path, _ in results}
        assert "photo1.jpg" in found_files
        assert "photo2.png" in found_files
        assert "photo3.gif" in found_files
        assert "document.txt" not in found_files

    def test_scan_directory_with_metadata(self, tmp_path):
        """Test that scan returns proper metadata."""
        scanner = ImageFileScanner()
        
        # Create test image file
        test_file = tmp_path / "test.jpg"
        test_content = "fake image content"
        test_file.write_text(test_content)
        
        # Scan directory
        results = list(scanner.scan_directory(str(tmp_path)))
        
        assert len(results) == 1
        file_path, metadata = results[0]
        
        # Check metadata
        assert metadata['size'] == len(test_content)
        assert metadata['extension'] == '.jpg'
        assert 'modified' in metadata
        assert isinstance(metadata['modified'], float)

    def test_scan_directory_handles_permission_errors(self, tmp_path):
        """Test graceful handling of permission errors."""
        scanner = ImageFileScanner()
        
        with patch('pathlib.Path.iterdir') as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Access denied")
            
            # Should not raise exception
            results = list(scanner.scan_directory(str(tmp_path)))
            assert len(results) == 0

    def test_scan_directory_handles_nonexistent_path(self):
        """Test handling of non-existent directory."""
        scanner = ImageFileScanner()
        
        # Should not raise exception
        results = list(scanner.scan_directory("/nonexistent/path"))
        assert len(results) == 0

    def test_scan_directory_skips_system_files(self, tmp_path):
        """Test that system files are properly skipped."""
        scanner = ImageFileScanner()
        
        # Create system files that would match image extensions
        (tmp_path / ".DS_Store").write_text("system file")
        (tmp_path / ".hidden.jpg").write_text("hidden image")
        (tmp_path / "Thumbs.db").write_text("system file")
        (tmp_path / "regular.jpg").write_text("regular image")
        
        # Scan directory
        results = list(scanner.scan_directory(str(tmp_path)))
        
        # Should only find the regular image
        assert len(results) == 1
        assert Path(results[0][0]).name == "regular.jpg"

    def test_cancellation_mechanism(self, tmp_path):
        """Test scan cancellation mechanism."""
        scanner = ImageFileScanner()
        
        # Create many files to scan
        for i in range(100):
            (tmp_path / f"photo{i}.jpg").write_text("content")
        
        # Start scan and cancel immediately
        scanner.cancel_scan()
        
        # Should find fewer files due to cancellation
        results = list(scanner.scan_directory(str(tmp_path)))
        assert len(results) < 100  # Should be cancelled early

    def test_reset_functionality(self):
        """Test scanner reset functionality."""
        scanner = ImageFileScanner()
        
        # Cancel scan
        scanner.cancel_scan()
        assert scanner._cancelled is True
        
        # Reset scanner
        scanner.reset()
        assert scanner._cancelled is False


@pytest.mark.unit
class TestImageFileScannerThread:
    """Test ImageFileScannerThread functionality."""

    def test_thread_initialization(self):
        """Test thread initialization."""
        thread = ImageFileScannerThread("/test/path")
        
        assert thread.directory_path == "/test/path"
        assert isinstance(thread.scanner, ImageFileScanner)

    def test_thread_signals_exist(self):
        """Test that required signals exist."""
        thread = ImageFileScannerThread("/test/path")
        
        # Check signals exist
        assert hasattr(thread, 'progress_update')
        assert hasattr(thread, 'scan_completed')
        assert hasattr(thread, 'scan_error')

    @patch('src.file_operations.file_scanner.ImageFileScanner.scan_directory')
    def test_thread_run_success(self, mock_scan):
        """Test successful thread execution."""
        # Mock scan results
        mock_scan.return_value = [
            ("/path/photo1.jpg", {'size': 1000, 'modified': 1234567890, 'extension': '.jpg'}),
            ("/path/photo2.png", {'size': 2000, 'modified': 1234567891, 'extension': '.png'})
        ]
        
        thread = ImageFileScannerThread("/test/path")
        
        # Mock signals
        completed_signal = MagicMock()
        thread.scan_completed.connect(completed_signal)
        
        # Run thread
        thread.run()
        
        # Verify signal was emitted
        completed_signal.assert_called_once()
        args = completed_signal.call_args[0]
        
        # Check results
        files, stats = args
        assert len(files) == 2
        assert stats['total_files'] == 2
        assert stats['total_size'] == 3000

    @patch('src.file_operations.file_scanner.ImageFileScanner.scan_directory')
    def test_thread_run_error(self, mock_scan):
        """Test thread error handling."""
        # Mock scan to raise exception
        mock_scan.side_effect = Exception("Test error")
        
        thread = ImageFileScannerThread("/test/path")
        
        # Mock error signal
        error_signal = MagicMock()
        thread.scan_error.connect(error_signal)
        
        # Run thread
        thread.run()
        
        # Verify error signal was emitted
        error_signal.assert_called_once()
        args = error_signal.call_args[0]
        assert "Test error" in args[0]

    def test_thread_cancellation(self):
        """Test thread cancellation."""
        thread = ImageFileScannerThread("/test/path")
        
        # Mock the thread methods
        with patch.object(thread, 'quit') as mock_quit:
            with patch.object(thread, 'wait') as mock_wait:
                thread.cancel_scan()
                
                # Verify cancellation methods called
                mock_quit.assert_called_once()
                mock_wait.assert_called_once()


@pytest.mark.integration
class TestFileSystemIntegration:
    """Integration tests with real file system."""

    def test_real_directory_scan(self, tmp_path):
        """Test scanning a real directory structure."""
        scanner = ImageFileScanner()
        
        # Create realistic directory structure
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        
        vacation_dir = photos_dir / "vacation"
        vacation_dir.mkdir()
        
        family_dir = photos_dir / "family"
        family_dir.mkdir()
        
        # Create various image files
        (photos_dir / "IMG_001.jpg").write_bytes(b"fake jpeg content")
        (photos_dir / "screenshot.png").write_bytes(b"fake png content")
        (vacation_dir / "beach.JPG").write_bytes(b"fake jpeg content")  # Different case
        (vacation_dir / "sunset.tiff").write_bytes(b"fake tiff content")
        (family_dir / "portrait.cr2").write_bytes(b"fake raw content")
        
        # Create non-image files
        (photos_dir / "readme.txt").write_text("not an image")
        (vacation_dir / "video.mp4").write_bytes(b"fake video content")
        
        # Create system files to be skipped
        (photos_dir / ".DS_Store").write_bytes(b"system file")
        
        # Scan the directory
        results = list(scanner.scan_directory(str(photos_dir)))
        
        # Should find 5 image files
        assert len(results) == 5
        
        # Verify all found files are images
        for file_path, metadata in results:
            path = Path(file_path)
            assert path.suffix.lower() in scanner.SUPPORTED_EXTENSIONS
            assert metadata['size'] > 0
            assert metadata['extension'] in scanner.SUPPORTED_EXTENSIONS

    def test_performance_with_many_files(self, tmp_path):
        """Test performance with many files."""
        scanner = ImageFileScanner()
        
        # Create many image files
        num_files = 1000
        for i in range(num_files):
            (tmp_path / f"image_{i:04d}.jpg").write_text(f"content {i}")
        
        # Time the scan
        start_time = time.time()
        results = list(scanner.scan_directory(str(tmp_path)))
        scan_time = time.time() - start_time
        
        # Should find all files
        assert len(results) == num_files
        
        # Should be reasonably fast (less than 5 seconds for 1000 files)
        assert scan_time < 5.0
        
        # Should process at least 200 files per second
        files_per_second = num_files / scan_time
        assert files_per_second > 200
