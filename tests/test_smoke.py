"""
Smoke tests for Photo Archivist application.

These tests verify basic functionality and that the application can start.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.mark.integration
class TestApplicationSmoke:
    """Smoke tests for basic application functionality."""
    
    def test_imports_work(self):
        """Test that all main modules can be imported."""
        # Test main application components
        from src.ui.main_window import MainWindow
        from src.utils.logger import setup_logging, get_logger
        
        assert MainWindow is not None
        assert setup_logging is not None
        assert get_logger is not None
    
    def test_logger_setup_works(self, tmp_path):
        """Test that logging setup works without errors."""
        with patch('src.utils.logger.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            
            from src.utils.logger import setup_logging, get_logger
            
            # Should not raise any exceptions
            setup_logging()
            logger = get_logger("test")
            logger.info("Test message")
    
    def test_main_window_can_be_created(self, qapp):
        """Test that main window can be created without errors."""
        with patch('src.utils.logger.get_logger') as mock_get_logger:
            mock_get_logger.return_value = MagicMock()
            
            from src.ui.main_window import MainWindow
            
            # Should not raise any exceptions
            window = MainWindow()
            assert window is not None
            assert window.windowTitle() == "Photo Archivist"
    
    def test_application_structure_exists(self):
        """Test that required application structure exists."""
        base_path = Path(__file__).parent.parent
        
        # Check main directories exist
        assert (base_path / "src").exists()
        assert (base_path / "src" / "ui").exists()
        assert (base_path / "src" / "image_processing").exists()
        assert (base_path / "src" / "file_operations").exists()
        assert (base_path / "src" / "utils").exists()
        assert (base_path / "tests").exists()
        
        # Check main files exist
        assert (base_path / "main.py").exists()
        assert (base_path / "requirements.txt").exists()
        assert (base_path / "pytest.ini").exists()
        
        # Check __init__.py files exist
        assert (base_path / "src" / "__init__.py").exists()
        assert (base_path / "src" / "ui" / "__init__.py").exists()
        assert (base_path / "src" / "utils" / "__init__.py").exists()
