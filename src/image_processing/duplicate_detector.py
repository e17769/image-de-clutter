"""
Duplicate image detection using perceptual hashing.

Provides hash-based duplicate detection functionality using Pillow for image processing.
Since imagededup has compatibility issues with Python 3.13, we implement our own
perceptual hash algorithms.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
from PIL import Image, ImageOps
from PyQt6.QtCore import QThread, pyqtSignal
import time

from ..utils.logger import get_logger


class PerceptualHasher:
    """Implements perceptual hashing algorithms for duplicate detection."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def dhash(self, image_path: str, hash_size: int = 8) -> Optional[str]:
        """
        Calculate difference hash (dHash) for an image.

        dHash compares adjacent pixels to create a hash that's resistant to
        minor modifications like resizing and compression.

        Args:
            image_path: Path to the image file
            hash_size: Size of the hash (default 8 gives 64-bit hash)

        Returns:
            Hexadecimal string representation of the hash, or None if error
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale
                img = ImageOps.grayscale(img)

                # Resize to hash_size+1 x hash_size to get hash_size^2 comparisons
                img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)

                # Convert to list of pixel values
                pixels = list(img.getdata())

                # Calculate differences between adjacent pixels
                hash_bits = []
                for row in range(hash_size):
                    for col in range(hash_size):
                        pixel_left = pixels[row * (hash_size + 1) + col]
                        pixel_right = pixels[row * (hash_size + 1) + col + 1]
                        hash_bits.append(pixel_left > pixel_right)

                # Convert boolean list to hex string
                hash_int = 0
                for i, bit in enumerate(hash_bits):
                    if bit:
                        hash_int |= 1 << i

                return format(hash_int, f"0{len(hash_bits)//4}x")

        except Exception as e:
            self.logger.warning(f"Error calculating dHash for {image_path}: {e}")
            return None

    def ahash(self, image_path: str, hash_size: int = 8) -> Optional[str]:
        """
        Calculate average hash (aHash) for an image.

        aHash compares each pixel to the average pixel value to create a hash.

        Args:
            image_path: Path to the image file
            hash_size: Size of the hash (default 8 gives 64-bit hash)

        Returns:
            Hexadecimal string representation of the hash, or None if error
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale and resize
                img = ImageOps.grayscale(img)
                img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

                # Get pixel values and calculate average
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)

                # Create hash based on whether each pixel is above average
                hash_bits = [pixel > avg for pixel in pixels]

                # Convert boolean list to hex string
                hash_int = 0
                for i, bit in enumerate(hash_bits):
                    if bit:
                        hash_int |= 1 << i

                return format(hash_int, f"0{len(hash_bits)//4}x")

        except Exception as e:
            self.logger.warning(f"Error calculating aHash for {image_path}: {e}")
            return None

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash as hex string
            hash2: Second hash as hex string

        Returns:
            Number of different bits between the hashes
        """
        if len(hash1) != len(hash2):
            return float("inf")

        # Convert hex to int and XOR to find different bits
        xor = int(hash1, 16) ^ int(hash2, 16)

        # Count number of 1s in binary representation
        return bin(xor).count("1")


class DuplicateGroup:
    """Represents a group of duplicate images."""

    def __init__(self, group_id: str, algorithm: str):
        self.group_id = group_id
        self.algorithm = algorithm
        self.images: List[Dict] = []
        self.representative_hash: Optional[str] = None

    def add_image(self, image_info: Dict):
        """Add an image to this duplicate group."""
        self.images.append(image_info)
        if self.representative_hash is None:
            self.representative_hash = image_info.get("hash")

    def get_size(self) -> int:
        """Get the number of images in this group."""
        return len(self.images)

    def get_total_size(self) -> int:
        """Get the total file size of all images in this group."""
        return sum(img.get("file_size", 0) for img in self.images)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "group_id": self.group_id,
            "algorithm": self.algorithm,
            "representative_hash": self.representative_hash,
            "image_count": self.get_size(),
            "total_size": self.get_total_size(),
            "images": self.images,
        }


class DuplicateDetector:
    """Main duplicate detection service."""

    def __init__(self, algorithm: str = "dhash", similarity_threshold: int = 5):
        """
        Initialize duplicate detector.

        Args:
            algorithm: Hash algorithm to use ('dhash' or 'ahash')
            similarity_threshold: Maximum hamming distance for duplicates (0-64)
        """
        self.algorithm = algorithm
        self.similarity_threshold = similarity_threshold
        self.hasher = PerceptualHasher()
        self.logger = get_logger(__name__)
        self._cancelled = False

        # Supported image extensions
        self.supported_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",
        }

    def generate_hashes(self, image_paths: List[str]) -> Dict[str, str]:
        """
        Generate hashes for a list of image paths.

        Args:
            image_paths: List of image file paths

        Returns:
            Dictionary mapping file paths to their hashes
        """
        hashes = {}
        hash_func = self.hasher.dhash if self.algorithm == "dhash" else self.hasher.ahash

        self.logger.info(f"Generating {self.algorithm} hashes for {len(image_paths)} images")

        for i, image_path in enumerate(image_paths):
            if self._cancelled:
                self.logger.info("Hash generation cancelled")
                break

            try:
                image_hash = hash_func(image_path)
                if image_hash:
                    hashes[image_path] = image_hash
                else:
                    self.logger.warning(f"Could not generate hash for {image_path}")

            except Exception as e:
                self.logger.error(f"Error processing {image_path}: {e}")
                continue

        self.logger.info(f"Generated {len(hashes)} hashes successfully")
        return hashes

    def find_duplicates(self, hashes: Dict[str, str]) -> List[DuplicateGroup]:
        """
        Find duplicate groups based on hash similarity.

        Args:
            hashes: Dictionary mapping file paths to their hashes

        Returns:
            List of DuplicateGroup objects
        """
        self.logger.info(f"Finding duplicates with threshold {self.similarity_threshold}")

        # Track which images have been assigned to groups
        assigned_images: Set[str] = set()
        duplicate_groups: List[DuplicateGroup] = []

        image_paths = list(hashes.keys())

        for i, path1 in enumerate(image_paths):
            if self._cancelled:
                break

            if path1 in assigned_images:
                continue

            hash1 = hashes[path1]
            current_group = None

            # Compare with remaining images
            for j in range(i + 1, len(image_paths)):
                if self._cancelled:
                    break

                path2 = image_paths[j]
                if path2 in assigned_images:
                    continue

                hash2 = hashes[path2]
                distance = self.hasher.hamming_distance(hash1, hash2)

                if distance <= self.similarity_threshold:
                    # Found a duplicate
                    if current_group is None:
                        # Create new group with the first image
                        group_id = f"group_{len(duplicate_groups)}"
                        current_group = DuplicateGroup(group_id, self.algorithm)

                        # Add first image to group
                        img1_info = self._get_image_info(path1, hash1)
                        current_group.add_image(img1_info)
                        assigned_images.add(path1)

                    # Add duplicate image to group
                    img2_info = self._get_image_info(path2, hash2)
                    current_group.add_image(img2_info)
                    assigned_images.add(path2)

            # Add group if it has duplicates
            if current_group and current_group.get_size() > 1:
                duplicate_groups.append(current_group)

        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def _get_image_info(self, image_path: str, image_hash: str) -> Dict:
        """Get detailed information about an image file."""
        try:
            stat = Path(image_path).stat()

            # Try to get image dimensions
            dimensions = None
            try:
                with Image.open(image_path) as img:
                    dimensions = img.size
            except Exception:
                pass

            return {
                "path": image_path,
                "hash": image_hash,
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "dimensions": dimensions,
            }
        except Exception as e:
            self.logger.warning(f"Could not get info for {image_path}: {e}")
            return {
                "path": image_path,
                "hash": image_hash,
                "file_size": 0,
                "modified_time": 0,
                "dimensions": None,
            }

    def detect_duplicates(self, image_paths: List[str]) -> List[DuplicateGroup]:
        """
        Complete duplicate detection workflow.

        Args:
            image_paths: List of image file paths to analyze

        Returns:
            List of duplicate groups found
        """
        self.logger.info(f"Starting duplicate detection for {len(image_paths)} images")
        start_time = time.time()

        # Generate hashes
        hashes = self.generate_hashes(image_paths)

        if not hashes:
            self.logger.warning("No valid hashes generated")
            return []

        # Find duplicates
        duplicate_groups = self.find_duplicates(hashes)

        detection_time = time.time() - start_time
        self.logger.info(f"Duplicate detection completed in {detection_time:.2f}s")

        return duplicate_groups

    def cancel_detection(self):
        """Cancel the current detection operation."""
        self.logger.info("Duplicate detection cancellation requested")
        self._cancelled = True

    def reset(self):
        """Reset detector state for new detection."""
        self._cancelled = False


class DuplicateDetectorThread(QThread):
    """Threaded wrapper for DuplicateDetector with Qt signals."""

    # Signals for UI updates
    progress_update = pyqtSignal(int, str)  # progress_percent, current_status
    detection_completed = pyqtSignal(list, dict)  # duplicate_groups, statistics
    detection_error = pyqtSignal(str)  # error_message

    def __init__(self, image_paths: List[str], algorithm: str = "dhash", threshold: int = 5):
        super().__init__()
        self.image_paths = image_paths
        self.detector = DuplicateDetector(algorithm, threshold)
        self.logger = get_logger(__name__)

    def run(self):
        """Run the duplicate detection in background thread."""
        try:
            self.logger.info(
                f"Starting threaded duplicate detection for {len(self.image_paths)} images"
            )
            self.progress_update.emit(0, "Initializing duplicate detection...")

            start_time = time.time()

            # Generate hashes with progress updates
            self.progress_update.emit(10, "Generating image hashes...")
            hashes = self.detector.generate_hashes(self.image_paths)

            if not hashes:
                self.detection_error.emit("No valid image hashes could be generated")
                return

            self.progress_update.emit(60, "Comparing images for duplicates...")

            # Find duplicates
            duplicate_groups = self.detector.find_duplicates(hashes)

            self.progress_update.emit(90, "Finalizing results...")

            # Calculate statistics
            detection_time = time.time() - start_time
            total_duplicates = sum(group.get_size() for group in duplicate_groups)

            statistics = {
                "total_images_processed": len(hashes),
                "total_groups_found": len(duplicate_groups),
                "total_duplicate_images": total_duplicates,
                "detection_time": detection_time,
                "algorithm_used": self.detector.algorithm,
                "similarity_threshold": self.detector.similarity_threshold,
            }

            self.progress_update.emit(100, "Detection completed")
            self.logger.info(
                f"Threaded duplicate detection completed: {len(duplicate_groups)} groups found"
            )

            self.detection_completed.emit(duplicate_groups, statistics)

        except Exception as e:
            error_msg = f"Duplicate detection failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.detection_error.emit(error_msg)

    def cancel_detection(self):
        """Cancel the detection operation."""
        self.detector.cancel_detection()
        self.quit()
        self.wait()
