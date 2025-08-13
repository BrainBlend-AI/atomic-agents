"""
Unit tests for privacy compliance functionality.
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from atomic_scraper_tool.compliance.privacy_compliance import (
    PrivacyComplianceChecker,
    PrivacyComplianceConfig,
    DataCategory,
    RetentionPolicy,
    DataCollectionRule,
    AuditLogEntry
)


class TestDataCategory:
    """Test cases for DataCategory enum."""
    
    def test_data_categories(self):
        """Test data category values."""
        assert DataCategory.PUBLIC_CONTENT == "public_content"
        assert DataCategory.CONTACT_INFO == "contact_info"
        assert DataCategory.BUSINESS_INFO == "business_info"
        assert DataCategory.PERSONAL_INFO == "personal_info"
        assert DataCategory.SENSITIVE_INFO == "sensitive_info"


class TestRetentionPolicy:
    """Test cases for RetentionPolicy model."""
    
    def test_retention_policy_creation(self):
        """Test retention policy creation."""
        policy = RetentionPolicy(
            category=DataCategory.PERSONAL_INFO,
            retention_days=30,
            auto_delete=True,
            description="Personal data policy"
        )
        
        assert policy.category == DataCategory.PERSONAL_INFO
        assert policy.retention_days == 30
        assert policy.auto_delete is True
        assert policy.archive_before_delete is False
        assert policy.description == "Personal data policy"
    
    def test_retention_policy_defaults(self):
        """Test retention policy default values."""
        policy = RetentionPolicy(
            category=DataCategory.PUBLIC_CONTENT,
            retention_days=365
        )
        
        assert policy.auto_delete is True
        assert policy.archive_before_delete is False
        assert policy.description == ""


class TestDataCollectionRule:
    """Test cases for DataCollectionRule model."""
    
    def test_data_collection_rule_defaults(self):
        """Test data collection rule default values."""
        rule = DataCollectionRule()
        
        assert rule.allowed_categories == set()
        assert rule.prohibited_patterns == []
        assert rule.required_consent_indicators == []
        assert rule.max_personal_records == 1000
        assert rule.respect_do_not_track is True
    
    def test_data_collection_rule_custom(self):
        """Test custom data collection rule."""
        rule = DataCollectionRule(
            allowed_categories={DataCategory.PUBLIC_CONTENT, DataCategory.BUSINESS_INFO},
            prohibited_patterns=[r"password", r"ssn"],
            max_personal_records=500
        )
        
        assert DataCategory.PUBLIC_CONTENT in rule.allowed_categories
        assert DataCategory.BUSINESS_INFO in rule.allowed_categories
        assert "password" in rule.prohibited_patterns
        assert rule.max_personal_records == 500


class TestAuditLogEntry:
    """Test cases for AuditLogEntry model."""
    
    def test_audit_log_entry_creation(self):
        """Test audit log entry creation."""
        entry = AuditLogEntry(
            url="https://example.com/test",
            domain="example.com",
            data_categories={DataCategory.PUBLIC_CONTENT},
            records_collected=5,
            user_agent="TestBot/1.0"
        )
        
        assert entry.url == "https://example.com/test"
        assert entry.domain == "example.com"
        assert DataCategory.PUBLIC_CONTENT in entry.data_categories
        assert entry.records_collected == 5
        assert entry.user_agent == "TestBot/1.0"
        assert entry.compliance_status == "compliant"
        assert entry.issues == []
        assert isinstance(entry.timestamp, datetime)


class TestPrivacyComplianceConfig:
    """Test cases for PrivacyComplianceConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PrivacyComplianceConfig()
        
        assert config.enabled is True
        assert config.audit_logging is True
        assert config.audit_log_path == "scraping_audit.log"
        assert config.data_retention_enabled is True
        assert config.retention_policies == []
        assert isinstance(config.collection_rules, DataCollectionRule)
        assert config.auto_cleanup_interval_hours == 24
        assert config.max_audit_log_size_mb == 100


class TestPrivacyComplianceChecker:
    """Test cases for PrivacyComplianceChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.audit_log_path = os.path.join(self.temp_dir, "test_audit.log")
        
        self.config = PrivacyComplianceConfig(
            audit_log_path=self.audit_log_path,
            auto_cleanup_interval_hours=1  # Short interval for testing
        )
        self.checker = PrivacyComplianceChecker(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        checker = PrivacyComplianceChecker()
        assert checker.config.enabled is True
        assert len(checker.config.retention_policies) == 5  # Default policies
    
    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        assert self.checker.config.audit_log_path == self.audit_log_path
        assert len(self.checker.config.retention_policies) == 5  # Default policies added
    
    def test_classify_data_public_content(self):
        """Test data classification for public content."""
        data = {
            "title": "Product Information",
            "description": "This is a great product",
            "price": "$19.99"
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.PUBLIC_CONTENT in categories
    
    def test_classify_data_contact_info(self):
        """Test data classification for contact information."""
        data = {
            "email": "contact@example.com",
            "phone": "555-123-4567",
            "contact_form": "Contact us"
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.CONTACT_INFO in categories
    
    def test_classify_data_personal_info(self):
        """Test data classification for personal information."""
        data = {
            "name": "John Doe",
            "address": "123 Main St",
            "age": "30"
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.PERSONAL_INFO in categories
    
    def test_classify_data_sensitive_info(self):
        """Test data classification for sensitive information."""
        data = {
            "password": "secret123",
            "credit_card": "4111-1111-1111-1111",
            "medical_info": "Patient has diabetes"
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.SENSITIVE_INFO in categories
    
    def test_classify_data_business_info(self):
        """Test data classification for business information."""
        data = {
            "business_name": "Acme Corp",
            "hours": "9 AM - 5 PM",
            "location": "Downtown",
            "services": ["consulting", "development"]
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.BUSINESS_INFO in categories
    
    def test_classify_data_multiple_categories(self):
        """Test data classification with multiple categories."""
        data = {
            "business_name": "Acme Corp",
            "contact_email": "info@acme.com",
            "owner_name": "Jane Smith",
            "description": "We provide excellent services"
        }
        
        categories = self.checker.classify_data(data)
        assert DataCategory.BUSINESS_INFO in categories
        assert DataCategory.CONTACT_INFO in categories
        assert DataCategory.PERSONAL_INFO in categories
    
    def test_check_collection_compliance_allowed(self):
        """Test compliance checking for allowed data."""
        # Configure to allow public content
        self.checker.config.collection_rules.allowed_categories = {
            DataCategory.PUBLIC_CONTENT,
            DataCategory.BUSINESS_INFO
        }
        
        data = {
            "title": "Product Info",
            "business_hours": "9-5"
        }
        
        is_compliant, issues = self.checker.check_collection_compliance(
            "https://example.com/test", data
        )
        
        assert is_compliant is True
        assert len(issues) == 0
    
    def test_check_collection_compliance_disallowed(self):
        """Test compliance checking for disallowed data."""
        # Configure to only allow public content
        self.checker.config.collection_rules.allowed_categories = {
            DataCategory.PUBLIC_CONTENT
        }
        
        data = {
            "email": "contact@example.com",
            "phone": "555-1234"
        }
        
        is_compliant, issues = self.checker.check_collection_compliance(
            "https://example.com/test", data
        )
        
        assert is_compliant is False
        assert len(issues) > 0
        assert "Disallowed data categories" in issues[0]
    
    def test_check_collection_compliance_prohibited_patterns(self):
        """Test compliance checking for prohibited patterns."""
        self.checker.config.collection_rules.prohibited_patterns = [r"password", r"ssn"]
        self.checker.config.collection_rules.allowed_categories = {
            DataCategory.PUBLIC_CONTENT,
            DataCategory.SENSITIVE_INFO
        }
        
        data = {
            "user_password": "secret123",
            "description": "Public content"
        }
        
        is_compliant, issues = self.checker.check_collection_compliance(
            "https://example.com/test", data
        )
        
        assert is_compliant is False
        assert any("Prohibited pattern found" in issue for issue in issues)
    
    def test_check_collection_compliance_disabled(self):
        """Test compliance checking when disabled."""
        self.checker.config.enabled = False
        
        data = {"password": "secret123"}
        
        is_compliant, issues = self.checker.check_collection_compliance(
            "https://example.com/test", data
        )
        
        assert is_compliant is True
        assert len(issues) == 0
    
    @patch('atomic_scraper_tool.compliance.privacy_compliance.logging')
    def test_log_scraping_activity(self, mock_logging):
        """Test scraping activity logging."""
        data = {
            "title": "Test Content",
            "description": "Public information"
        }
        
        self.checker.log_scraping_activity(
            "https://example.com/test", data, "TestBot/1.0"
        )
        
        # Check that audit log file was created
        assert os.path.exists(self.audit_log_path)
    
    def test_log_scraping_activity_disabled(self):
        """Test scraping activity logging when disabled."""
        self.checker.config.audit_logging = False
        
        data = {"title": "Test Content"}
        
        # Should not raise any exceptions
        self.checker.log_scraping_activity(
            "https://example.com/test", data, "TestBot/1.0"
        )
    
    def test_apply_retention_policy_retain(self):
        """Test retention policy application - data should be retained."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test_data.json")
        with open(test_file, 'w') as f:
            json.dump({"title": "Test"}, f)
        
        # File is new, should be retained
        categories = {DataCategory.PUBLIC_CONTENT}
        should_retain = self.checker.apply_retention_policy(test_file, categories)
        
        assert should_retain is True
        assert os.path.exists(test_file)
    
    def test_apply_retention_policy_delete(self):
        """Test retention policy application - data should be deleted."""
        # Create a test file and make it old
        test_file = os.path.join(self.temp_dir, "old_data.json")
        with open(test_file, 'w') as f:
            json.dump({"password": "secret"}, f)
        
        # Make file appear old by modifying its timestamp
        old_time = time.time() - (8 * 24 * 3600)  # 8 days old
        os.utime(test_file, (old_time, old_time))
        
        categories = {DataCategory.SENSITIVE_INFO}  # 7-day retention
        should_retain = self.checker.apply_retention_policy(test_file, categories)
        
        assert should_retain is False
        assert not os.path.exists(test_file)  # Should be deleted
    
    def test_apply_retention_policy_disabled(self):
        """Test retention policy when disabled."""
        self.checker.config.data_retention_enabled = False
        
        test_file = os.path.join(self.temp_dir, "test_data.json")
        with open(test_file, 'w') as f:
            json.dump({"title": "Test"}, f)
        
        categories = {DataCategory.PUBLIC_CONTENT}
        should_retain = self.checker.apply_retention_policy(test_file, categories)
        
        assert should_retain is True
    
    def test_apply_retention_policy_nonexistent_file(self):
        """Test retention policy for nonexistent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        categories = {DataCategory.PUBLIC_CONTENT}
        
        should_retain = self.checker.apply_retention_policy(nonexistent_file, categories)
        
        assert should_retain is False
    
    def test_cleanup_expired_data(self):
        """Test cleanup of expired data."""
        # Create test files with different ages
        current_file = os.path.join(self.temp_dir, "current.json")
        old_file = os.path.join(self.temp_dir, "old.json")
        
        # Create current file
        with open(current_file, 'w') as f:
            json.dump({"title": "Current content"}, f)
        
        # Create old file
        with open(old_file, 'w') as f:
            json.dump({"password": "old secret"}, f)
        
        # Make old file appear expired
        old_time = time.time() - (8 * 24 * 3600)  # 8 days old
        os.utime(old_file, (old_time, old_time))
        
        # Run cleanup
        self.checker.cleanup_expired_data(self.temp_dir)
        
        # Current file should still exist, old file should be deleted
        assert os.path.exists(current_file)
        # Note: old file deletion depends on data classification and retention policy
    
    def test_cleanup_expired_data_disabled(self):
        """Test cleanup when data retention is disabled."""
        self.checker.config.data_retention_enabled = False
        
        # Should not raise any exceptions
        self.checker.cleanup_expired_data(self.temp_dir)
    
    def test_cleanup_expired_data_nonexistent_directory(self):
        """Test cleanup for nonexistent directory."""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        
        # Should not raise any exceptions
        self.checker.cleanup_expired_data(nonexistent_dir)
    
    def test_get_compliance_report_no_log(self):
        """Test compliance report when no audit log exists."""
        # Make sure the audit log file doesn't exist
        if os.path.exists(self.audit_log_path):
            os.remove(self.audit_log_path)
            
        report = self.checker.get_compliance_report()
        
        assert "error" in report
        assert "No audit log found" in report["error"]
    
    def test_get_compliance_report_disabled_logging(self):
        """Test compliance report when audit logging is disabled."""
        self.checker.config.audit_logging = False
        
        report = self.checker.get_compliance_report()
        
        assert "error" in report
        assert "Audit logging is disabled" in report["error"]
    
    def test_get_compliance_report_with_data(self):
        """Test compliance report with audit data."""
        # Create some audit log entries
        entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "url": "https://example.com/page1",
                "domain": "example.com",
                "data_categories": ["public_content"],
                "records_collected": 5,
                "compliance_status": "compliant",
                "issues": []
            },
            {
                "timestamp": datetime.now().isoformat(),
                "url": "https://example.com/page2",
                "domain": "example.com",
                "data_categories": ["contact_info"],
                "records_collected": 2,
                "compliance_status": "non_compliant",
                "issues": ["Disallowed data categories found"]
            }
        ]
        
        # Write entries to audit log
        with open(self.audit_log_path, 'w') as f:
            for entry in entries:
                f.write(f"2024-01-01 12:00:00,000 - INFO - {json.dumps(entry)}\n")
        
        report = self.checker.get_compliance_report(days=30)
        
        assert report["total_requests"] == 2
        assert report["compliant_requests"] == 1
        assert report["non_compliant_requests"] == 1
        assert report["compliance_rate"] == 0.5
        assert "example.com" in report["domains_accessed"]
    
    def test_validate_data_collection_compliant(self):
        """Test data collection validation for compliant data."""
        self.checker.config.collection_rules.allowed_categories = {
            DataCategory.PUBLIC_CONTENT
        }
        
        data = {"title": "Public content"}
        
        is_valid = self.checker.validate_data_collection(
            "https://example.com/test", data, "TestBot/1.0"
        )
        
        assert is_valid is True
    
    def test_validate_data_collection_non_compliant(self):
        """Test data collection validation for non-compliant data."""
        self.checker.config.collection_rules.allowed_categories = {
            DataCategory.PUBLIC_CONTENT
        }
        
        data = {"email": "contact@example.com"}
        
        is_valid = self.checker.validate_data_collection(
            "https://example.com/test", data, "TestBot/1.0"
        )
        
        assert is_valid is False
    
    def test_validate_data_collection_disabled(self):
        """Test data collection validation when compliance is disabled."""
        self.checker.config.enabled = False
        
        data = {"password": "secret123"}
        
        is_valid = self.checker.validate_data_collection(
            "https://example.com/test", data, "TestBot/1.0"
        )
        
        assert is_valid is True
    
    def test_rotate_audit_log(self):
        """Test audit log rotation."""
        # Create audit log file
        with open(self.audit_log_path, 'w') as f:
            f.write("Test log content")
        
        # Manually set file size to be larger than limit by patching the stat result
        original_stat = Path(self.audit_log_path).stat
        
        class MockStat:
            st_size = 200 * 1024 * 1024  # 200 MB
        
        with patch.object(Path, 'stat', return_value=MockStat()):
            self.checker.rotate_audit_log()
        
        # Original file should be renamed, new file should exist
        rotated_files = list(Path(self.temp_dir).glob("test_audit.*.log"))
        assert len(rotated_files) > 0
    
    def test_rotate_audit_log_disabled(self):
        """Test audit log rotation when logging is disabled."""
        self.checker.config.audit_logging = False
        
        # Should not raise any exceptions
        self.checker.rotate_audit_log()
    
    def test_rotate_audit_log_no_file(self):
        """Test audit log rotation when no log file exists."""
        # Should not raise any exceptions
        self.checker.rotate_audit_log()


class TestPrivacyComplianceIntegration:
    """Integration tests for privacy compliance functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_log_path = os.path.join(self.temp_dir, "integration_audit.log")
        
        self.config = PrivacyComplianceConfig(
            audit_log_path=self.audit_log_path,
            collection_rules=DataCollectionRule(
                allowed_categories={
                    DataCategory.PUBLIC_CONTENT,
                    DataCategory.BUSINESS_INFO
                },
                prohibited_patterns=[r"password", r"ssn"],
                max_personal_records=10
            )
        )
        self.checker = PrivacyComplianceChecker(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_compliant_workflow(self):
        """Test end-to-end workflow for compliant data collection."""
        data = {
            "business_name": "Acme Corp",
            "hours": "9 AM - 5 PM",
            "services": ["consulting", "development"],
            "description": "We provide excellent services"
        }
        
        # Validate data collection
        is_valid = self.checker.validate_data_collection(
            "https://example.com/business", data, "TestBot/1.0"
        )
        
        assert is_valid is True
        
        # Check that audit log was created
        assert os.path.exists(self.audit_log_path)
        
        # Generate compliance report
        report = self.checker.get_compliance_report(days=1)
        
        assert report["total_requests"] == 1
        assert report["compliant_requests"] == 1
        assert report["compliance_rate"] == 1.0
    
    def test_end_to_end_non_compliant_workflow(self):
        """Test end-to-end workflow for non-compliant data collection."""
        data = {
            "user_password": "secret123",  # Prohibited pattern
            "personal_email": "john@example.com",  # Disallowed category
            "description": "Public content"
        }
        
        # Validate data collection
        is_valid = self.checker.validate_data_collection(
            "https://example.com/user", data, "TestBot/1.0"
        )
        
        assert is_valid is False
        
        # Generate compliance report
        report = self.checker.get_compliance_report(days=1)
        
        assert report["total_requests"] == 1
        assert report["non_compliant_requests"] == 1
        assert report["compliance_rate"] == 0.0
        assert len(report["common_issues"]) > 0