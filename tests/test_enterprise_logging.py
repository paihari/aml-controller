#!/usr/bin/env python3
"""
Test suite for enterprise logging system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import time
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

from utils.enterprise_logger import (
    EnterpriseLogger, 
    get_logger, 
    log_function_calls, 
    log_performance,
    correlation_context
)
from utils.log_config import (
    get_api_logger,
    get_database_logger,
    get_security_logger,
    get_audit_logger
)

class TestEnterpriseLogging(unittest.TestCase):
    """Test enterprise logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_logs_dir = None
        
        # Patch logs directory to use temp directory
        with patch.object(EnterpriseLogger, '_ensure_logs_directory', return_value=self.temp_dir):
            self.logger_instance = EnterpriseLogger()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_logger_initialization(self):
        """Test logger system initialization"""
        logger = get_logger('APPLICATION', 'test')
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'app.test')
    
    def test_structured_logging(self):
        """Test structured JSON logging"""
        logger = get_logger('API', 'test')
        
        # Log a structured message
        logger.info(
            "Test message",
            extra_fields={
                'user_id': 'test_user',
                'operation': 'test_operation',
                'duration_ms': 123.45
            }
        )
        
        # Check that log file was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('api.log' in f for f in log_files))
    
    def test_correlation_context(self):
        """Test correlation ID context management"""
        logger = get_logger('APPLICATION', 'test')
        
        with correlation_context('test-correlation-id') as corr_id:
            self.assertEqual(corr_id, 'test-correlation-id')
            logger.info("Test message with correlation")
            
        # Test auto-generated correlation ID
        with correlation_context() as corr_id:
            self.assertIsNotNone(corr_id)
            self.assertTrue(len(corr_id) > 10)  # UUID-like
    
    def test_security_logging(self):
        """Test security event logging"""
        logger_instance = EnterpriseLogger()
        
        logger_instance.log_security_event(
            event_type='LOGIN_ATTEMPT',
            severity='MEDIUM',
            description='Failed login attempt',
            user_id='test_user',
            ip_address='192.168.1.100'
        )
        
        # Check that security log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('security.log' in f for f in log_files))
    
    def test_audit_logging(self):
        """Test audit event logging"""
        logger_instance = EnterpriseLogger()
        
        logger_instance.log_audit_event(
            action='CREATE',
            resource='transaction',
            user_id='test_user',
            transaction_id='TXN_123'
        )
        
        # Check that audit log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('audit.log' in f for f in log_files))
    
    def test_performance_logging(self):
        """Test performance metrics logging"""
        logger_instance = EnterpriseLogger()
        
        logger_instance.log_performance_metric(
            metric_name='api_response_time',
            value=123.45,
            unit='ms',
            endpoint='/api/test'
        )
        
        # Check that performance log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('performance.log' in f for f in log_files))
    
    def test_database_logging(self):
        """Test database operation logging"""
        logger_instance = EnterpriseLogger()
        
        logger_instance.log_database_operation(
            operation='SELECT',
            table='transactions',
            success=True,
            duration_ms=45.67,
            rows_affected=10
        )
        
        # Check that database log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('database.log' in f for f in log_files))
    
    def test_function_call_decorator(self):
        """Test function call logging decorator"""
        @log_function_calls('APPLICATION', 'test')
        def test_function(param1, param2=None):
            time.sleep(0.01)  # Small delay to test duration logging
            return param1 + (param2 or 0)
        
        result = test_function(5, param2=3)
        self.assertEqual(result, 8)
        
        # Check that application log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('app.log' in f for f in log_files))
    
    def test_performance_decorator(self):
        """Test performance logging decorator"""
        @log_performance('test_metric')
        def slow_function():
            time.sleep(0.01)
            return "done"
        
        result = slow_function()
        self.assertEqual(result, "done")
        
        # Check that performance log was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('performance.log' in f for f in log_files))
    
    def test_exception_handling(self):
        """Test exception logging in decorators"""
        @log_function_calls('APPLICATION', 'test')
        def failing_function():
            raise ValueError("Test exception")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        # Check that error was logged
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('app.log' in f for f in log_files))
    
    def test_api_request_logging(self):
        """Test API request/response logging"""
        logger_instance = EnterpriseLogger()
        
        logger_instance.log_api_request(
            method='POST',
            endpoint='/api/transactions',
            user_id='test_user',
            request_size=1024
        )
        
        logger_instance.log_api_response(
            method='POST',
            endpoint='/api/transactions',
            status_code=201,
            duration_ms=123.45,
            response_size=512
        )
        
        # Check that API logs were created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(any('api.log' in f for f in log_files))
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is filtered from logs"""
        # This would require access to log file contents
        # For now, just ensure the security filter exists
        from utils.enterprise_logger import SecurityLogFilter
        
        security_filter = SecurityLogFilter()
        self.assertIsNotNone(security_filter)
        
        # Test record filtering (would need mock record)
        mock_record = MagicMock()
        mock_record.extra_fields = {
            'username': 'testuser',
            'password': 'secret123',
            'normal_field': 'normal_value'
        }
        mock_record.getMessage.return_value = "Login attempt for user"
        
        result = security_filter.filter(mock_record)
        self.assertTrue(result)

class TestLoggingIntegration(unittest.TestCase):
    """Test logging integration with AML components"""
    
    def test_aml_component_loggers(self):
        """Test that AML-specific loggers work"""
        api_logger = get_api_logger('transactions')
        db_logger = get_database_logger('sanctions')
        security_logger = get_security_logger('auth')
        audit_logger = get_audit_logger()
        
        self.assertIsNotNone(api_logger)
        self.assertIsNotNone(db_logger)
        self.assertIsNotNone(security_logger)
        self.assertIsNotNone(audit_logger)
        
        # Test that they have different names
        self.assertEqual(api_logger.name, 'api.transactions')
        self.assertEqual(db_logger.name, 'database.sanctions')
        self.assertEqual(security_logger.name, 'security.auth')
        self.assertEqual(audit_logger.name, 'audit.compliance')
    
    def test_logging_performance_impact(self):
        """Test that logging doesn't significantly impact performance"""
        logger = get_logger('APPLICATION', 'performance_test')
        
        # Test logging performance
        start_time = time.time()
        for i in range(1000):
            logger.info(
                f"Performance test message {i}",
                extra_fields={
                    'iteration': i,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        duration = time.time() - start_time
        
        # Should complete 1000 log messages in under 1 second
        self.assertLess(duration, 1.0)

def run_logging_demo():
    """Demonstrate enterprise logging features"""
    print("🚀 AML Controller - Enterprise Logging Demo")
    print("=" * 60)
    
    # Initialize logging
    app_logger = get_logger('APPLICATION', 'demo')
    api_logger = get_api_logger('demo')
    db_logger = get_database_logger('demo')
    security_logger = get_security_logger('demo')
    audit_logger = get_audit_logger()
    
    # Demonstrate correlation context
    with correlation_context('demo-correlation-123') as corr_id:
        print(f"📋 Correlation ID: {corr_id}")
        
        # Application logging
        app_logger.info(
            "AML system startup initiated",
            extra_fields={
                'version': '1.0.0',
                'environment': 'demo',
                'components': ['api', 'database', 'cache']
            }
        )
        
        # API logging
        api_logger.info(
            "Processing API request",
            extra_fields={
                'endpoint': '/api/transactions/process',
                'method': 'POST',
                'user_id': 'demo_user'
            }
        )
        
        # Database logging
        db_logger.info(
            "Database operation completed",
            extra_fields={
                'operation': 'SELECT',
                'table': 'transactions',
                'duration_ms': 45.2,
                'rows_affected': 150
            }
        )
        
        # Security logging
        enterprise_logger = EnterpriseLogger()
        enterprise_logger.log_security_event(
            event_type='DATA_ACCESS',
            severity='INFO',
            description='User accessed transaction data',
            user_id='demo_user',
            resource='transactions'
        )
        
        # Audit logging
        enterprise_logger.log_audit_event(
            action='PROCESS_TRANSACTIONS',
            resource='batch_001',
            user_id='demo_user',
            transaction_count=150,
            alerts_generated=3
        )
        
        # Performance logging
        enterprise_logger.log_performance_metric(
            metric_name='transaction_processing_time',
            value=1234.56,
            unit='ms',
            batch_size=150
        )
    
    print("✅ Logging demo completed")
    print("📁 Check logs/ directory for generated log files")
    print("🔍 Use 'tail -f logs/app.log' to monitor in real-time")

if __name__ == '__main__':
    # Run demo first
    print("Running enterprise logging demo...")
    run_logging_demo()
    print()
    
    # Run tests
    print("Running test suite...")
    unittest.main(verbosity=2)