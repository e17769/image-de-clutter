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
import numpy as np
from sklearn.feature_extraction import image as sk_image
from sklearn.metrics.pairwise import cosine_similarity

from ..utils.logger import get_logger


class CNNFeatureExtractor:
    """Implements CNN-based feature extraction for advanced similarity detection."""

    def __init__(self, patch_size: int = 8):
        """
        Initialize CNN feature extractor.

        Args:
            patch_size: Size of patches for feature extraction (default 8x8)
        """
        self.patch_size = patch_size
        self.logger = get_logger(__name__)

    def extract_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract CNN-based features from an image using patch-based approach.

        Args:
            image_path: Path to the image file

        Returns:
            Feature vector as numpy array, or None if error
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale and resize for consistency
                img = ImageOps.grayscale(img)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)

                # Convert to numpy array
                img_array = np.array(img, dtype=np.float32) / 255.0

                # Extract patches using sklearn
                patches = sk_image.extract_patches_2d(
                    img_array,
                    (self.patch_size, self.patch_size),
                    max_patches=100,  # Limit patches for performance
                    random_state=42,
                )

                # Flatten patches and compute statistics
                patches_flat = patches.reshape(patches.shape[0], -1)

                # Compute feature statistics
                features = np.array(
                    [
                        np.mean(patches_flat, axis=0),  # Mean of patches
                        np.std(patches_flat, axis=0),  # Standard deviation
                        np.min(patches_flat, axis=0),  # Minimum values
                        np.max(patches_flat, axis=0),  # Maximum values
                    ]
                ).flatten()

                return features

        except Exception as e:
            self.logger.warning(f"Error extracting CNN features for {image_path}: {e}")
            return None

    def compute_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compute similarity between two feature vectors using cosine similarity.

        Args:
            features1: First feature vector
            features2: Second feature vector

        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Reshape for sklearn
            features1 = features1.reshape(1, -1)
            features2 = features2.reshape(1, -1)

            # Compute cosine similarity
            similarity = cosine_similarity(features1, features2)[0, 0]

            # Convert to 0-1 range (cosine similarity is -1 to 1)
            return (similarity + 1.0) / 2.0

        except Exception as e:
            self.logger.warning(f"Error computing similarity: {e}")
            return 0.0


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

    def __init__(self, group_id: str, algorithm: str, similarity_score: float = 1.0):
        self.group_id = group_id
        self.algorithm = algorithm
        self.similarity_score = similarity_score
        self.images: List[Dict] = []
        self.representative_hash: Optional[str] = None
        self.confidence_level = self._get_confidence_level(similarity_score)

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

    def _get_confidence_level(self, similarity_score: float) -> str:
        """Get confidence level based on similarity score."""
        if similarity_score >= 0.95:
            return "high"
        elif similarity_score >= 0.85:
            return "medium"
        else:
            return "low"

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "group_id": self.group_id,
            "algorithm": self.algorithm,
            "similarity_score": self.similarity_score,
            "confidence_level": self.confidence_level,
            "representative_hash": self.representative_hash,
            "image_count": self.get_size(),
            "total_size": self.get_total_size(),
            "images": self.images,
        }


class DuplicateDetector:
    """Main duplicate detection service."""

    def __init__(
        self,
        algorithm: str = "dhash",
        similarity_threshold: int = 5,
        use_cnn: bool = False,
        cnn_similarity_threshold: float = 0.85,
    ):
        """
        Initialize duplicate detector.

        Args:
            algorithm: Hash algorithm to use ('dhash' or 'ahash')
            similarity_threshold: Maximum hamming distance for duplicates (0-64)
            use_cnn: Whether to use CNN-based similarity detection
            cnn_similarity_threshold: Minimum similarity score for CNN matches (0.0-1.0)
        """
        self.algorithm = algorithm
        self.similarity_threshold = similarity_threshold
        self.use_cnn = use_cnn
        self.cnn_similarity_threshold = cnn_similarity_threshold
        self.hasher = PerceptualHasher()
        self.cnn_extractor = CNNFeatureExtractor() if use_cnn else None
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

    def generate_cnn_features(self, image_paths: List[str]) -> Dict[str, np.ndarray]:
        """
        Generate CNN features for a list of image paths.

        Args:
            image_paths: List of image file paths

        Returns:
            Dictionary mapping file paths to their CNN features
        """
        if not self.use_cnn or self.cnn_extractor is None:
            return {}

        features = {}
        self.logger.info(f"Generating CNN features for {len(image_paths)} images")

        for i, image_path in enumerate(image_paths):
            if self._cancelled:
                self.logger.info("CNN feature generation cancelled")
                break

            try:
                feature_vector = self.cnn_extractor.extract_features(image_path)
                if feature_vector is not None:
                    features[image_path] = feature_vector
                else:
                    self.logger.warning(f"Could not generate CNN features for {image_path}")

            except Exception as e:
                self.logger.error(f"Error processing {image_path} for CNN features: {e}")
                continue

        self.logger.info(f"Generated {len(features)} CNN feature vectors successfully")
        return features

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

    def find_cnn_duplicates(self, cnn_features: Dict[str, np.ndarray]) -> List[DuplicateGroup]:
        """
        Find duplicate groups based on CNN feature similarity.

        Args:
            cnn_features: Dictionary mapping file paths to their CNN features

        Returns:
            List of DuplicateGroup objects
        """
        if not self.use_cnn or not cnn_features:
            return []

        self.logger.info(
            f"Finding CNN-based duplicates with threshold {self.cnn_similarity_threshold}"
        )

        # Track which images have been assigned to groups
        assigned_images: Set[str] = set()
        duplicate_groups: List[DuplicateGroup] = []

        image_paths = list(cnn_features.keys())

        for i, path1 in enumerate(image_paths):
            if self._cancelled:
                break

            if path1 in assigned_images:
                continue

            features1 = cnn_features[path1]
            current_group = None
            group_similarities = []

            # Compare with remaining images
            for j in range(i + 1, len(image_paths)):
                if self._cancelled:
                    break

                path2 = image_paths[j]
                if path2 in assigned_images:
                    continue

                features2 = cnn_features[path2]
                similarity = self.cnn_extractor.compute_similarity(features1, features2)

                if similarity >= self.cnn_similarity_threshold:
                    # Found a similar image
                    if current_group is None:
                        # Create new group with the first image
                        group_id = f"cnn_group_{len(duplicate_groups)}"
                        current_group = DuplicateGroup(group_id, "cnn", similarity)

                        # Add first image to group
                        img1_info = self._get_image_info(path1, None)
                        img1_info["cnn_features"] = features1
                        img1_info["similarity_to_group"] = 1.0
                        current_group.add_image(img1_info)
                        assigned_images.add(path1)

                    # Add similar image to group
                    img2_info = self._get_image_info(path2, None)
                    img2_info["cnn_features"] = features2
                    img2_info["similarity_to_group"] = similarity
                    current_group.add_image(img2_info)
                    assigned_images.add(path2)
                    group_similarities.append(similarity)

            # Add group if it has duplicates and update average similarity
            if current_group and current_group.get_size() > 1:
                if group_similarities:
                    avg_similarity = sum(group_similarities) / len(group_similarities)
                    current_group.similarity_score = avg_similarity
                    current_group.confidence_level = current_group._get_confidence_level(
                        avg_similarity
                    )
                duplicate_groups.append(current_group)

        self.logger.info(f"Found {len(duplicate_groups)} CNN-based duplicate groups")
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
        Complete duplicate detection workflow with both hash and CNN detection.

        Args:
            image_paths: List of image file paths to analyze

        Returns:
            List of duplicate groups found (hash-based and/or CNN-based)
        """
        self.logger.info(f"Starting duplicate detection for {len(image_paths)} images")
        start_time = time.time()

        all_duplicate_groups = []

        # Phase 1: Hash-based detection
        self.logger.info("Phase 1: Hash-based duplicate detection")
        hashes = self.generate_hashes(image_paths)

        if hashes:
            hash_groups = self.find_duplicates(hashes)
            all_duplicate_groups.extend(hash_groups)
            self.logger.info(f"Found {len(hash_groups)} hash-based duplicate groups")
        else:
            self.logger.warning("No valid hashes generated")

        # Phase 2: CNN-based detection (if enabled)
        if self.use_cnn:
            self.logger.info("Phase 2: CNN-based similarity detection")
            try:
                cnn_features = self.generate_cnn_features(image_paths)

                if cnn_features:
                    cnn_groups = self.find_cnn_duplicates(cnn_features)
                    all_duplicate_groups.extend(cnn_groups)
                    self.logger.info(f"Found {len(cnn_groups)} CNN-based duplicate groups")
                else:
                    self.logger.warning("No valid CNN features generated")

            except Exception as e:
                self.logger.error(f"CNN detection failed, falling back to hash-only: {e}")

        detection_time = time.time() - start_time
        total_groups = len(all_duplicate_groups)
        self.logger.info(
            f"Duplicate detection completed in {detection_time:.2f}s - {total_groups} total groups"
        )

        return all_duplicate_groups

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

    def __init__(
        self,
        image_paths: List[str],
        algorithm: str = "dhash",
        threshold: int = 5,
        use_cnn: bool = False,
        cnn_threshold: float = 0.85,
    ):
        super().__init__()
        self.image_paths = image_paths
        self.detector = DuplicateDetector(algorithm, threshold, use_cnn, cnn_threshold)
        self.logger = get_logger(__name__)

    def run(self):
        """Run the duplicate detection in background thread."""
        try:
            self.logger.info(
                f"Starting threaded duplicate detection for {len(self.image_paths)} images"
            )
            self.progress_update.emit(0, "Initializing duplicate detection...")

            start_time = time.time()

            # Use the enhanced detect_duplicates method
            duplicate_groups = self.detector.detect_duplicates(self.image_paths)

            self.progress_update.emit(90, "Finalizing results...")

            # Calculate statistics
            detection_time = time.time() - start_time
            total_duplicates = sum(group.get_size() for group in duplicate_groups)

            # Count groups by method
            hash_groups_count = sum(
                1 for g in duplicate_groups if g.algorithm in ["dhash", "ahash"]
            )
            cnn_groups_count = sum(1 for g in duplicate_groups if g.algorithm == "cnn")

            statistics = {
                "total_images_processed": len(self.image_paths),
                "total_groups_found": len(duplicate_groups),
                "total_duplicate_images": total_duplicates,
                "hash_groups_found": hash_groups_count,
                "cnn_groups_found": cnn_groups_count,
                "detection_time": detection_time,
                "algorithm_used": self.detector.algorithm,
                "similarity_threshold": self.detector.similarity_threshold,
                "cnn_enabled": self.detector.use_cnn,
                "cnn_threshold": (
                    self.detector.cnn_similarity_threshold if self.detector.use_cnn else None
                ),
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
