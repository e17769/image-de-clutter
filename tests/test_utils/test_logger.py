"""
Unit tests for logging utilities.
"""

import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.logger import setup_logging, get_logger, log_exception, log_performance, LoggerMixin


@pytest.mark.unit
class TestLoggingSetup:
    """Test logging setup functionality."""
    
    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test that setup_logging creates the log directory."""
        with patch('src.utils.logger.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            setup_logging()
            
            log_dir = tmp_path / ".photo_archivist" / "logs"
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_setup_logging_configures_handlers(self):
        """Test that setup_logging configures file and console handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.utils.logger.Path.home') as mock_home:
                mock_home.return_value = Path(temp_dir)
                setup_logging(log_level=logging.DEBUG)
                
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) >= 2  # File and console handlers
                assert root_logger.level == logging.DEBUG
    
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_log_exception_logs_with_traceback(self, caplog):
        """Test that log_exception logs with exception info."""
        logger = get_logger("test")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            log_exception(logger, "Custom error message")
        
        assert "Custom error message" in caplog.text
        assert "ValueError: Test exception" in caplog.text
    
    def test_log_performance_logs_metrics(self, caplog):
        """Test that log_performance logs performance metrics."""
        logger = get_logger("test")
        
        log_performance(
            logger, 
            "test_operation", 
            0.0, 
            1.5, 
            files_processed=100,
            memory_used="50MB"
        )
        
        record = caplog.records[0]
        assert "PERFORMANCE" in record.message
        assert "test_operation" in record.message
        assert "Duration: 1.50s" in record.message
        assert "files_processed: 100" in record.message
        assert "memory_used: 50MB" in record.message


@pytest.mark.unit
class TestLoggerMixin:
    """Test LoggerMixin functionality."""
    
    def test_logger_mixin_provides_logger(self):
        """Test that LoggerMixin provides logger property."""
        
        class TestClass(LoggerMixin):
            pass
        
        instance = TestClass()
        logger = instance.logger
        
        assert isinstance(logger, logging.Logger)
        assert logger.name.endswith("TestClass")
    
    def test_logger_mixin_caches_logger(self):
        """Test that LoggerMixin caches logger instance."""
        
        class TestClass(LoggerMixin):
            pass
        
        instance = TestClass()
        logger1 = instance.logger
        logger2 = instance.logger
        
        assert logger1 is logger2  # Same instance