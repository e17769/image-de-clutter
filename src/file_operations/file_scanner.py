"""
File scanner for discovering image files in directories.

Provides recursive directory scanning with support for various image formats
and proper handling of system files and permissions.
"""

import os
from pathlib import Path
from typing import Generator, Tuple
from PyQt6.QtCore import QThread, pyqtSignal
import time

from ..utils.logger import get_logger


class ImageFileScanner:
    """Scanner for discovering image files in directory structures."""

    # Enhanced file format support from PRD v1.1
    SUPPORTED_EXTENSIONS = {
        # Common formats
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".bmp",
        # Professional RAW formats
        ".cr2",
        ".nef",
        ".arw",
        ".dng",
        # Additional formats
        ".raw",
        ".orf",
        ".rw2",
        ".pef",
        ".sr2",
        ".crw",
    }

    # System files and directories to skip on macOS
    SKIP_PATTERNS = {
        ".DS_Store",
        "._.DS_Store",
        ".Spotlight-V100",
        ".Trashes",
        ".fseventsd",
        "Thumbs.db",
        "desktop.ini",
        ".localized",
    }

    SKIP_DIRECTORIES = {
        "/System",
        "/Library",
        "/usr",
        "/bin",
        "/sbin",
        "/var",
        "/tmp",
        "/.Spotlight-V100",
        "/.Trashes",
        "/.fseventsd",
    }

    def __init__(self):
        self.logger = get_logger(__name__)
        self._cancelled = False

    def scan_directory(self, directory_path: str) -> Generator[Tuple[str, dict], None, None]:
        """
        Recursively scan directory for image files.

        Args:
            directory_path: Path to directory to scan

        Yields:
            Tuple of (file_path, metadata) for each discovered image
        """
        self.logger.info(f"Starting directory scan: {directory_path}")
        start_time = time.time()

        try:
            directory = Path(directory_path)

            if not directory.exists():
                self.logger.error(f"Directory does not exist: {directory_path}")
                return

            if not directory.is_dir():
                self.logger.error(f"Path is not a directory: {directory_path}")
                return

            total_files = 0
            total_size = 0

            for file_path in self._walk_directory(directory):
                if self._cancelled:
                    self.logger.info("Scan cancelled by user")
                    break

                try:
                    file_stat = file_path.stat()
                    metadata = {
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime,
                        "extension": file_path.suffix.lower(),
                    }

                    total_files += 1
                    total_size += file_stat.st_size

                    yield str(file_path), metadata

                except (OSError, PermissionError) as e:
                    self.logger.warning(f"Cannot access file {file_path}: {e}")
                    continue

            scan_time = time.time() - start_time
            self.logger.info(
                f"Scan completed: {total_files} files, {total_size} bytes, {scan_time:.2f}s"
            )

        except Exception as e:
            self.logger.error(f"Error during directory scan: {e}", exc_info=True)

    def _walk_directory(self, directory: Path) -> Generator[Path, None, None]:
        """
        Walk directory tree, yielding image files while skipping system files.

        Args:
            directory: Directory path to walk

        Yields:
            Path objects for discovered image files
        """
        try:
            # Skip system directories
            if self._should_skip_directory(directory):
                self.logger.debug(f"Skipping system directory: {directory}")
                return

            # Check directory permissions
            if not os.access(directory, os.R_OK):
                self.logger.warning(f"No read permission for directory: {directory}")
                return

            # Scan current directory
            try:
                entries = list(directory.iterdir())
            except (OSError, PermissionError) as e:
                self.logger.warning(f"Cannot read directory {directory}: {e}")
                return

            # Process files first
            for entry in entries:
                if self._cancelled:
                    return

                if entry.is_file():
                    if self._is_image_file(entry) and not self._should_skip_file(entry):
                        yield entry

            # Then recurse into subdirectories
            for entry in entries:
                if self._cancelled:
                    return

                if entry.is_dir() and not self._should_skip_directory(entry):
                    yield from self._walk_directory(entry)

        except (OSError, PermissionError) as e:
            self.logger.warning(f"Error walking directory {directory}: {e}")

    def _is_image_file(self, file_path: Path) -> bool:
        """Check if file is a supported image format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        filename = file_path.name

        # Skip hidden files (starting with .)
        if filename.startswith("."):
            return True

        # Skip known system files
        if filename in self.SKIP_PATTERNS:
            return True

        return False

    def _should_skip_directory(self, directory: Path) -> bool:
        """Check if directory should be skipped."""
        dir_str = str(directory)
        dir_name = directory.name

        # Skip system directories by full path
        for skip_dir in self.SKIP_DIRECTORIES:
            if dir_str.startswith(skip_dir):
                return True

        # Skip hidden directories (starting with .)
        if dir_name.startswith("."):
            return True

        # Skip known problematic directories
        if dir_name in {"__pycache__", "node_modules", ".git", ".svn"}:
            return True

        return False

    def cancel_scan(self):
        """Cancel the current scan operation."""
        self.logger.info("Scan cancellation requested")
        self._cancelled = True

    def reset(self):
        """Reset scanner state for new scan."""
        self._cancelled = False


class ImageFileScannerThread(QThread):
    """Threaded wrapper for ImageFileScanner with Qt signals."""

    # Signals for UI updates
    progress_update = pyqtSignal(int, str)  # count, current_file
    scan_completed = pyqtSignal(list, dict)  # file_list, statistics
    scan_error = pyqtSignal(str)  # error_message

    def __init__(self, directory_path: str):
        super().__init__()
        self.directory_path = directory_path
        self.scanner = ImageFileScanner()
        self.logger = get_logger(__name__)

    def run(self):
        """Run the scanning operation in background thread."""
        try:
            self.logger.info(f"Starting threaded scan of: {self.directory_path}")

            discovered_files = []
            file_count = 0
            total_size = 0
            extensions_found = set()

            start_time = time.time()

            for file_path, metadata in self.scanner.scan_directory(self.directory_path):
                file_count += 1
                total_size += metadata["size"]
                extensions_found.add(metadata["extension"])

                discovered_files.append(
                    {
                        "path": file_path,
                        "size": metadata["size"],
                        "modified": metadata["modified"],
                        "extension": metadata["extension"],
                    }
                )

                # Emit progress update every 100 files
                if file_count % 100 == 0:
                    self.progress_update.emit(file_count, file_path)

            scan_time = time.time() - start_time

            # Prepare statistics
            statistics = {
                "total_files": file_count,
                "total_size": total_size,
                "scan_time": scan_time,
                "extensions_found": sorted(list(extensions_found)),
                "average_file_size": total_size / file_count if file_count > 0 else 0,
            }

            self.logger.info(f"Threaded scan completed: {file_count} files in {scan_time:.2f}s")
            self.scan_completed.emit(discovered_files, statistics)

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.scan_error.emit(error_msg)

    def cancel_scan(self):
        """Cancel the scanning operation."""
        self.scanner.cancel_scan()
        self.quit()
        self.wait()
