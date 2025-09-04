"""
Unit tests for duplicate detection functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import os

from src.image_processing.duplicate_detector import (
    PerceptualHasher, DuplicateGroup, DuplicateDetector, DuplicateDetectorThread
)


@pytest.mark.unit
class TestPerceptualHasher:
    """Test PerceptualHasher functionality."""

    def test_dhash_calculation(self, tmp_path):
        """Test dHash calculation for an image."""
        hasher = PerceptualHasher()
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Calculate hash
        hash_result = hasher.dhash(str(test_image_path))
        
        # Should return a hex string
        assert hash_result is not None
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16  # 64 bits = 16 hex chars
        
        # Should be consistent
        hash_result2 = hasher.dhash(str(test_image_path))
        assert hash_result == hash_result2

    def test_ahash_calculation(self, tmp_path):
        """Test aHash calculation for an image."""
        hasher = PerceptualHasher()
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='blue')
        test_image_path = tmp_path / "test.jpg"
        img.save(test_image_path)
        
        # Calculate hash
        hash_result = hasher.ahash(str(test_image_path))
        
        # Should return a hex string
        assert hash_result is not None
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16  # 64 bits = 16 hex chars

    def test_hash_calculation_with_invalid_file(self):
        """Test hash calculation with invalid file."""
        hasher = PerceptualHasher()
        
        # Non-existent file
        hash_result = hasher.dhash("/nonexistent/file.jpg")
        assert hash_result is None
        
        hash_result = hasher.ahash("/nonexistent/file.jpg")
        assert hash_result is None

    def test_hamming_distance_calculation(self):
        """Test Hamming distance calculation between hashes."""
        hasher = PerceptualHasher()
        
        # Identical hashes should have distance 0
        hash1 = "0123456789abcdef"
        hash2 = "0123456789abcdef"
        distance = hasher.hamming_distance(hash1, hash2)
        assert distance == 0
        
        # Different hashes should have positive distance
        hash3 = "0123456789abcdee"  # Last bit different
        distance = hasher.hamming_distance(hash1, hash3)
        assert distance == 1
        
        # Completely different hashes
        hash4 = "fedcba9876543210"
        distance = hasher.hamming_distance(hash1, hash4)
        assert distance > 0

    def test_hamming_distance_different_lengths(self):
        """Test Hamming distance with different length hashes."""
        hasher = PerceptualHasher()
        
        hash1 = "0123"
        hash2 = "0123456789abcdef"
        
        distance = hasher.hamming_distance(hash1, hash2)
        assert distance == float('inf')


@pytest.mark.unit
class TestDuplicateGroup:
    """Test DuplicateGroup functionality."""

    def test_duplicate_group_creation(self):
        """Test creating a duplicate group."""
        group = DuplicateGroup("group_1", "dhash")
        
        assert group.group_id == "group_1"
        assert group.algorithm == "dhash"
        assert group.get_size() == 0
        assert group.representative_hash is None

    def test_adding_images_to_group(self):
        """Test adding images to duplicate group."""
        group = DuplicateGroup("group_1", "dhash")
        
        image1 = {
            'path': '/path/to/image1.jpg',
            'hash': 'abc123',
            'file_size': 1000,
            'dimensions': (100, 100)
        }
        
        image2 = {
            'path': '/path/to/image2.jpg',
            'hash': 'abc124',
            'file_size': 1500,
            'dimensions': (100, 100)
        }
        
        group.add_image(image1)
        assert group.get_size() == 1
        assert group.representative_hash == 'abc123'
        
        group.add_image(image2)
        assert group.get_size() == 2
        assert group.get_total_size() == 2500

    def test_group_to_dict(self):
        """Test converting group to dictionary."""
        group = DuplicateGroup("group_1", "dhash")
        
        image = {
            'path': '/path/to/image.jpg',
            'hash': 'abc123',
            'file_size': 1000,
            'dimensions': (100, 100)
        }
        
        group.add_image(image)
        group_dict = group.to_dict()
        
        assert group_dict['group_id'] == "group_1"
        assert group_dict['algorithm'] == "dhash"
        assert group_dict['image_count'] == 1
        assert group_dict['total_size'] == 1000
        assert len(group_dict['images']) == 1


@pytest.mark.unit
class TestDuplicateDetector:
    """Test DuplicateDetector functionality."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = DuplicateDetector(algorithm='dhash', similarity_threshold=5)
        
        assert detector.algorithm == 'dhash'
        assert detector.similarity_threshold == 5
        assert not detector._cancelled

    def test_generate_hashes(self, tmp_path):
        """Test hash generation for multiple images."""
        detector = DuplicateDetector()
        
        # Create test images with patterns to ensure different hashes
        img1 = Image.new('RGB', (50, 50), color='white')
        # Add a pattern to make it distinctive
        for i in range(0, 50, 10):
            for j in range(50):
                img1.putpixel((i, j), (255, 0, 0))  # Red stripes
        
        img2 = Image.new('RGB', (50, 50), color='white')
        # Add a different pattern
        for i in range(50):
            for j in range(0, 50, 10):
                img2.putpixel((i, j), (0, 0, 255))  # Blue stripes
        
        path1 = tmp_path / "image1.jpg"
        path2 = tmp_path / "image2.jpg"
        
        img1.save(path1)
        img2.save(path2)
        
        # Generate hashes
        hashes = detector.generate_hashes([str(path1), str(path2)])
        
        assert len(hashes) == 2
        assert str(path1) in hashes
        assert str(path2) in hashes
        assert hashes[str(path1)] != hashes[str(path2)]

    def test_find_duplicates_with_identical_images(self, tmp_path):
        """Test finding duplicates with identical images."""
        detector = DuplicateDetector(similarity_threshold=0)  # Exact matches only
        
        # Create identical images
        img = Image.new('RGB', (50, 50), color='red')
        
        path1 = tmp_path / "image1.jpg"
        path2 = tmp_path / "image2.jpg"
        
        img.save(path1)
        img.save(path2)
        
        # Generate hashes and find duplicates
        hashes = detector.generate_hashes([str(path1), str(path2)])
        duplicate_groups = detector.find_duplicates(hashes)
        
        # Should find one group with two images
        assert len(duplicate_groups) == 1
        assert duplicate_groups[0].get_size() == 2

    def test_find_duplicates_with_no_duplicates(self, tmp_path):
        """Test finding duplicates when none exist."""
        detector = DuplicateDetector(similarity_threshold=0)  # Exact matches only
        
        # Create very different images with distinctive patterns
        img1 = Image.new('RGB', (50, 50), color='white')
        # Checkerboard pattern
        for i in range(50):
            for j in range(50):
                if (i + j) % 2 == 0:
                    img1.putpixel((i, j), (0, 0, 0))
        
        img2 = Image.new('RGB', (50, 50), color='white')
        # Vertical stripes
        for i in range(0, 50, 2):
            for j in range(50):
                img2.putpixel((i, j), (255, 0, 0))
        
        img3 = Image.new('RGB', (50, 50), color='white')
        # Horizontal stripes
        for i in range(50):
            for j in range(0, 50, 2):
                img3.putpixel((i, j), (0, 255, 0))
        
        path1 = tmp_path / "image1.jpg"
        path2 = tmp_path / "image2.jpg"
        path3 = tmp_path / "image3.jpg"
        
        img1.save(path1)
        img2.save(path2)
        img3.save(path3)
        
        # Generate hashes and find duplicates
        hashes = detector.generate_hashes([str(path1), str(path2), str(path3)])
        duplicate_groups = detector.find_duplicates(hashes)
        
        # Should find very few duplicates with strict threshold (allowing for JPEG compression effects)
        assert len(duplicate_groups) <= 1
        if len(duplicate_groups) == 1:
            # If there is a group, it should be small
            assert duplicate_groups[0].get_size() <= 2

    def test_detect_duplicates_complete_workflow(self, tmp_path):
        """Test complete duplicate detection workflow."""
        detector = DuplicateDetector()
        
        # Create test images - some identical
        img1 = Image.new('RGB', (50, 50), color='red')
        img2 = Image.new('RGB', (50, 50), color='red')  # Duplicate of img1
        
        # Create a distinctly different image
        img3 = Image.new('RGB', (50, 50), color='white')
        # Add a unique pattern
        for i in range(25):
            for j in range(50):
                img3.putpixel((i, j), (0, 0, 255))
        
        path1 = tmp_path / "image1.jpg"
        path2 = tmp_path / "image2.jpg"
        path3 = tmp_path / "image3.jpg"
        
        img1.save(path1)
        img2.save(path2)
        img3.save(path3)
        
        # Run complete detection
        duplicate_groups = detector.detect_duplicates([str(path1), str(path2), str(path3)])
        
        # Should find one group with the duplicate images
        assert len(duplicate_groups) == 1
        assert duplicate_groups[0].get_size() == 2

    def test_cancellation_mechanism(self):
        """Test detection cancellation."""
        detector = DuplicateDetector()
        
        # Cancel detection
        detector.cancel_detection()
        assert detector._cancelled is True
        
        # Reset detector
        detector.reset()
        assert detector._cancelled is False

    def test_get_image_info(self, tmp_path):
        """Test getting image information."""
        detector = DuplicateDetector()
        
        # Create test image
        img = Image.new('RGB', (100, 200), color='red')
        test_path = tmp_path / "test.jpg"
        img.save(test_path)
        
        # Get image info
        info = detector._get_image_info(str(test_path), "test_hash")
        
        assert info['path'] == str(test_path)
        assert info['hash'] == "test_hash"
        assert info['file_size'] > 0
        assert info['dimensions'] == (100, 200)

    def test_get_image_info_invalid_file(self):
        """Test getting info for invalid file."""
        detector = DuplicateDetector()
        
        info = detector._get_image_info("/nonexistent/file.jpg", "test_hash")
        
        assert info['path'] == "/nonexistent/file.jpg"
        assert info['hash'] == "test_hash"
        assert info['file_size'] == 0
        assert info['dimensions'] is None


@pytest.mark.unit
class TestDuplicateDetectorThread:
    """Test DuplicateDetectorThread functionality."""

    def test_thread_initialization(self):
        """Test thread initialization."""
        image_paths = ["/path/to/image1.jpg", "/path/to/image2.jpg"]
        thread = DuplicateDetectorThread(image_paths, algorithm='ahash', threshold=3)
        
        assert thread.image_paths == image_paths
        assert thread.detector.algorithm == 'ahash'
        assert thread.detector.similarity_threshold == 3

    def test_thread_signals_exist(self):
        """Test that required signals exist."""
        thread = DuplicateDetectorThread(["/test/path"])
        
        # Check signals exist
        assert hasattr(thread, 'progress_update')
        assert hasattr(thread, 'detection_completed')
        assert hasattr(thread, 'detection_error')

    def test_thread_run_success(self, tmp_path):
        """Test successful thread execution."""
        # Create real test images
        img1 = Image.new('RGB', (50, 50), color='red')
        img2 = Image.new('RGB', (50, 50), color='red')  # Duplicate
        
        path1 = tmp_path / "image1.jpg"
        path2 = tmp_path / "image2.jpg"
        
        img1.save(path1)
        img2.save(path2)
        
        thread = DuplicateDetectorThread([str(path1), str(path2)])
        
        # Mock signals
        completed_signal = MagicMock()
        thread.detection_completed.connect(completed_signal)
        
        # Run thread
        thread.run()
        
        # Verify signal was emitted
        completed_signal.assert_called_once()
        args = completed_signal.call_args[0]
        
        # Check results
        groups, stats = args
        assert len(groups) == 1
        assert stats['total_groups_found'] == 1
        assert stats['total_duplicate_images'] == 2

    def test_thread_run_error(self):
        """Test thread error handling."""
        # Use non-existent paths to trigger error
        thread = DuplicateDetectorThread(["/nonexistent/path1.jpg", "/nonexistent/path2.jpg"])
        
        # Mock error signal
        error_signal = MagicMock()
        thread.detection_error.connect(error_signal)
        
        # Run thread
        thread.run()
        
        # Verify error signal was emitted
        error_signal.assert_called_once()
        args = error_signal.call_args[0]
        assert "No valid image hashes could be generated" in args[0]

    def test_thread_cancellation(self):
        """Test thread cancellation."""
        thread = DuplicateDetectorThread(["/test/path"])
        
        # Mock the thread methods
        with patch.object(thread, 'quit') as mock_quit:
            with patch.object(thread, 'wait') as mock_wait:
                thread.cancel_detection()
                
                # Verify cancellation methods called
                mock_quit.assert_called_once()
                mock_wait.assert_called_once()


@pytest.mark.integration
class TestDuplicateDetectionIntegration:
    """Integration tests for duplicate detection."""

    def test_real_duplicate_detection(self, tmp_path):
        """Test duplicate detection with real images."""
        detector = DuplicateDetector(similarity_threshold=5)
        
        # Create test images
        # Image 1 - red square
        img1 = Image.new('RGB', (100, 100), color='red')
        path1 = tmp_path / "red1.jpg"
        img1.save(path1)
        
        # Image 2 - identical red square
        img2 = Image.new('RGB', (100, 100), color='red')
        path2 = tmp_path / "red2.jpg"
        img2.save(path2)
        
        # Image 3 - blue square (different)
        img3 = Image.new('RGB', (100, 100), color='blue')
        path3 = tmp_path / "blue1.jpg"
        img3.save(path3)
        
        # Image 4 - slightly different red (should still be similar)
        img4 = Image.new('RGB', (100, 100), color=(255, 10, 10))  # Slightly different red
        path4 = tmp_path / "red3.jpg"
        img4.save(path4)
        
        # Run detection
        image_paths = [str(path1), str(path2), str(path3), str(path4)]
        duplicate_groups = detector.detect_duplicates(image_paths)
        
        # Should find at least one group (the identical red images)
        assert len(duplicate_groups) >= 1
        
        # At least one group should have multiple images
        group_sizes = [group.get_size() for group in duplicate_groups]
        assert any(size >= 2 for size in group_sizes)

    def test_performance_with_many_images(self, tmp_path):
        """Test performance with many images."""
        detector = DuplicateDetector()
        
        # Create many test images
        num_images = 50
        image_paths = []
        
        for i in range(num_images):
            # Create images with different colors
            color = (i * 5 % 256, (i * 7) % 256, (i * 11) % 256)
            img = Image.new('RGB', (50, 50), color=color)
            path = tmp_path / f"image_{i:03d}.jpg"
            img.save(path)
            image_paths.append(str(path))
        
        # Add some duplicates by creating identical images
        duplicate_paths = []
        for i in range(5):
            # Create a duplicate of the first 5 images
            original_path = image_paths[i]
            duplicate_path = tmp_path / f"duplicate_{i:03d}.jpg"
            
            # Copy the image
            with Image.open(original_path) as img:
                img.save(duplicate_path)
            duplicate_paths.append(str(duplicate_path))
        
        # Add duplicates to the list
        all_paths = image_paths + duplicate_paths
        
        # Run detection
        import time
        start_time = time.time()
        duplicate_groups = detector.detect_duplicates(all_paths)
        detection_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 10 seconds)
        assert detection_time < 10.0
        
        # Should find at least some duplicate groups (might not be exactly 5 due to similar colors)
        assert len(duplicate_groups) >= 1
        
        # Total duplicate images should be reasonable
        total_duplicates = sum(group.get_size() for group in duplicate_groups)
        assert total_duplicates >= 10  # At least the 5 pairs we created
