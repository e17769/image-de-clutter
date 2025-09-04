"""
Pytest configuration and fixtures for Photo Archivist tests.
"""

import pytest
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it might be used by other tests


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary directory for logging tests."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir
