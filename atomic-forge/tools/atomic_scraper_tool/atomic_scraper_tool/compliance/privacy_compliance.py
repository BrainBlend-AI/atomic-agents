"""
Privacy compliance checker for ethical web scraping.

This module provides functionality to ensure compliance with privacy laws,
data retention policies, and ethical data collection practices.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from atomic_scraper_tool.core.exceptions import ScrapingError


class DataCategory(str, Enum):
    """Categories of data that can be collected."""
    PUBLIC_CONTENT = "public_content"
    CONTACT_INFO = "contact_info"
    BUSINESS_INFO = "business_info"
    PERSONAL_INFO = "personal_info"
    SENSITIVE_INFO = "sensitive_info"


class RetentionPolicy(BaseModel):
    """Data retention policy configuration."""
    category: DataCategory
    retention_days: int
    auto_delete: bool = True
    archive_before_delete: bool = False
    description: str = ""


class DataCollectionRule(BaseModel):
    """Rules for data collection compliance."""
    allowed_categories: Set[DataCategory] = Field(default_factory=set)
    prohibited_patterns: List[str] = Field(default_factory=list)  # Regex patterns
    required_consent_indicators: List[str] = Field(default_factory=list)
    max_personal_records: int = 1000
    respect_do_not_track: bool = True


class AuditLogEntry(BaseModel):
    """Audit log entry for tracking scraping activities."""
    timestamp: datetime = Field(default_factory=datetime.now)
    url: str
    domain: str
    data_categories: Set[DataCategory] = Field(default_factory=set)
    records_collected: int = 0
    user_agent: str = ""
    compliance_status: str = "compliant"
    issues: List[str] = Field(default_factory=list)
    retention_applied: bool = False


class PrivacyComplianceConfig(BaseModel):
    """Configuration for privacy compliance checking."""
    enabled: bool = True
    audit_logging: bool = True
    audit_log_path: str = "scraping_audit.log"
    data_retention_enabled: bool = True
    retention_policies: List[RetentionPolicy] = Field(default_factory=list)
    collection_rules: DataCollectionRule = Field(default_factory=DataCollectionRule)
    auto_cleanup_interval_hours: int = 24
    max_audit_log_size_mb: int = 100


class PrivacyComplianceChecker:
    """
    Privacy compliance checker for ethical web scraping.
    
    This class provides functionality to:
    - Check data collection compliance
    - Enforce data retention policies
    - Maintain audit trails
    - Automatically clean up expired data
    - Detect potentially sensitive information
    """
    
    def __init__(self, config: PrivacyComplianceConfig = None):
        """
        Initialize the privacy compliance checker.
        
        Args:
            config: Privacy compliance configuration
        """
        self.config = config or PrivacyComplianceConfig()
        self._setup_logging()
        self._setup_default_policies()
        self._last_cleanup = time.time()
        
    def _setup_logging(self):
        """Set up audit logging."""
        if not self.config.audit_logging:
            return
            
        # Create audit logger
        self.audit_logger = logging.getLogger('scraping_audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.audit_logger.handlers[:]:
            self.audit_logger.removeHandler(handler)
        
        # Create file handler
        handler = logging.FileHandler(self.config.audit_log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.audit_logger.propagate = False
    
    def _setup_default_policies(self):
        """Set up default retention policies if none are configured."""
        if not self.config.retention_policies:
            default_policies = [
                RetentionPolicy(
                    category=DataCategory.PUBLIC_CONTENT,
                    retention_days=365,
                    description="Public content like articles, product listings"
                ),
                RetentionPolicy(
                    category=DataCategory.BUSINESS_INFO,
                    retention_days=180,
                    description="Business information like addresses, hours"
                ),
                RetentionPolicy(
                    category=DataCategory.CONTACT_INFO,
                    retention_days=90,
                    description="Contact information like emails, phones"
                ),
                RetentionPolicy(
                    category=DataCategory.PERSONAL_INFO,
                    retention_days=30,
                    description="Personal information requiring careful handling"
                ),
                RetentionPolicy(
                    category=DataCategory.SENSITIVE_INFO,
                    retention_days=7,
                    description="Sensitive information requiring immediate attention"
                )
            ]
            self.config.retention_policies = default_policies
    
    def classify_data(self, data: Dict[str, Any]) -> Set[DataCategory]:
        """
        Classify scraped data into privacy categories.
        
        Args:
            data: Dictionary of scraped data
            
        Returns:
            Set of data categories found in the data
        """
        categories = set()
        
        # Convert data to string for pattern matching
        data_str = json.dumps(data, default=str).lower()
        
        # Check for contact information patterns
        contact_patterns = [
            r'email', r'@\w+\.\w+', r'phone', r'tel:', r'contact',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Phone patterns
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email patterns
        ]
        
        if any(pattern in data_str for pattern in contact_patterns):
            categories.add(DataCategory.CONTACT_INFO)
        
        # Check for personal information patterns (more specific)
        personal_patterns = [
            r'\bfirst.?name\b', r'\blast.?name\b', r'\bfull.?name\b',
            r'\bpersonal.?name\b', r'\buser.?name\b', r'\bowner.?name\b',
            r'\baddress\b', r'\bbirthday\b', r'\bage\b', r'\bgender\b',
            r'social security', r'ssn', r'driver license', r'passport'
        ]
        
        if any(re.search(pattern, data_str, re.IGNORECASE) for pattern in personal_patterns):
            categories.add(DataCategory.PERSONAL_INFO)
        
        # Check for sensitive information patterns
        sensitive_patterns = [
            r'password', r'credit card', r'bank account', r'ssn',
            r'medical', r'health', r'financial', r'income', r'salary'
        ]
        
        if any(pattern in data_str for pattern in sensitive_patterns):
            categories.add(DataCategory.SENSITIVE_INFO)
        
        # Check for business information patterns
        business_patterns = [
            r'business', r'company', r'hours', r'location', r'address',
            r'service', r'product', r'price', r'description'
        ]
        
        if any(pattern in data_str for pattern in business_patterns):
            categories.add(DataCategory.BUSINESS_INFO)
        
        # Default to public content if no specific categories found
        if not categories:
            categories.add(DataCategory.PUBLIC_CONTENT)
        
        # Always include public content for general data
        if any(pattern in data_str for pattern in ['title', 'description', 'content']):
            categories.add(DataCategory.PUBLIC_CONTENT)
        
        return categories
    
    def check_collection_compliance(self, url: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check if data collection complies with privacy rules.
        
        Args:
            url: URL where data was collected
            data: Scraped data to check
            
        Returns:
            Tuple of (is_compliant, list_of_issues)
        """
        if not self.config.enabled:
            return True, []
        
        issues = []
        data_categories = self.classify_data(data)
        
        # Check if data categories are allowed
        disallowed_categories = data_categories - self.config.collection_rules.allowed_categories
        if disallowed_categories:
            issues.append(f"Disallowed data categories found: {disallowed_categories}")
        
        # Check for prohibited patterns
        data_str = json.dumps(data, default=str)
        for pattern in self.config.collection_rules.prohibited_patterns:
            import re
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Prohibited pattern found: {pattern}")
        
        # Check personal data limits
        if DataCategory.PERSONAL_INFO in data_categories:
            # This is a simplified check - in practice, you'd track across sessions
            if len(data) > self.config.collection_rules.max_personal_records:
                issues.append("Personal data collection limit exceeded")
        
        # Check for Do Not Track indicators (simplified)
        if self.config.collection_rules.respect_do_not_track:
            if 'do-not-track' in data_str.lower() or 'opt-out' in data_str.lower():
                issues.append("Do Not Track indicator found")
        
        is_compliant = len(issues) == 0
        return is_compliant, issues
    
    def log_scraping_activity(self, url: str, data: Dict[str, Any], user_agent: str = ""):
        """
        Log scraping activity for audit purposes.
        
        Args:
            url: URL that was scraped
            data: Data that was collected
            user_agent: User agent used for scraping
        """
        if not self.config.audit_logging:
            return
        
        domain = urlparse(url).netloc
        data_categories = self.classify_data(data)
        is_compliant, issues = self.check_collection_compliance(url, data)
        
        audit_entry = AuditLogEntry(
            url=url,
            domain=domain,
            data_categories=data_categories,
            records_collected=len(data) if isinstance(data, (list, dict)) else 1,
            user_agent=user_agent,
            compliance_status="compliant" if is_compliant else "non_compliant",
            issues=issues
        )
        
        # Log to audit file
        log_message = json.dumps(audit_entry.model_dump(), default=str)
        self.audit_logger.info(log_message)
        
        # Check if cleanup is needed
        self._check_and_run_cleanup()
    
    def apply_retention_policy(self, data_path: str, data_categories: Set[DataCategory]) -> bool:
        """
        Apply retention policy to data files.
        
        Args:
            data_path: Path to data file
            data_categories: Categories of data in the file
            
        Returns:
            True if data should be retained, False if it should be deleted
        """
        if not self.config.data_retention_enabled:
            return True
        
        if not os.path.exists(data_path):
            return False
        
        file_age_days = (time.time() - os.path.getmtime(data_path)) / (24 * 3600)
        
        # Find the most restrictive retention policy
        min_retention_days = float('inf')
        applicable_policy = None
        
        for policy in self.config.retention_policies:
            if policy.category in data_categories:
                if policy.retention_days < min_retention_days:
                    min_retention_days = policy.retention_days
                    applicable_policy = policy
        
        # If no specific policy found, use default for public content
        if applicable_policy is None:
            for policy in self.config.retention_policies:
                if policy.category == DataCategory.PUBLIC_CONTENT:
                    applicable_policy = policy
                    min_retention_days = policy.retention_days
                    break
        
        # Check if data should be deleted
        if file_age_days > min_retention_days:
            if applicable_policy and applicable_policy.archive_before_delete:
                self._archive_data(data_path)
            
            if applicable_policy and applicable_policy.auto_delete:
                try:
                    os.remove(data_path)
                    self.audit_logger.info(f"Auto-deleted expired data: {data_path}")
                    return False
                except OSError as e:
                    self.audit_logger.error(f"Failed to delete expired data {data_path}: {e}")
        
        return True
    
    def _archive_data(self, data_path: str):
        """Archive data before deletion."""
        try:
            archive_dir = Path(data_path).parent / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            archive_path = archive_dir / f"{Path(data_path).name}.archived"
            
            # Move file to archive
            os.rename(data_path, archive_path)
            self.audit_logger.info(f"Archived data: {data_path} -> {archive_path}")
            
        except OSError as e:
            self.audit_logger.error(f"Failed to archive data {data_path}: {e}")
    
    def _check_and_run_cleanup(self):
        """Check if cleanup should be run and run it if needed."""
        current_time = time.time()
        hours_since_cleanup = (current_time - self._last_cleanup) / 3600
        
        if hours_since_cleanup >= self.config.auto_cleanup_interval_hours:
            self.cleanup_expired_data()
            self._last_cleanup = current_time
    
    def cleanup_expired_data(self, data_directory: str = None):
        """
        Clean up expired data based on retention policies.
        
        Args:
            data_directory: Directory to clean up (optional)
        """
        if not self.config.data_retention_enabled:
            return
        
        if data_directory is None:
            data_directory = "."
        
        data_dir = Path(data_directory)
        if not data_dir.exists():
            return
        
        cleaned_count = 0
        
        # Find all JSON data files
        for file_path in data_dir.rglob("*.json"):
            try:
                # Try to load and classify the data
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                data_categories = self.classify_data(data)
                
                # Apply retention policy
                if not self.apply_retention_policy(str(file_path), data_categories):
                    cleaned_count += 1
                    
            except (json.JSONDecodeError, OSError) as e:
                self.audit_logger.warning(f"Could not process file {file_path}: {e}")
        
        if cleaned_count > 0:
            self.audit_logger.info(f"Cleanup completed: {cleaned_count} files processed")
    
    def rotate_audit_log(self):
        """Rotate audit log if it gets too large."""
        if not self.config.audit_logging:
            return
        
        log_path = Path(self.config.audit_log_path)
        if not log_path.exists():
            return
        
        # Check file size
        file_size_mb = log_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb > self.config.max_audit_log_size_mb:
            # Rotate log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = log_path.with_suffix(f".{timestamp}.log")
            
            try:
                log_path.rename(rotated_path)
                self.audit_logger.info(f"Audit log rotated: {rotated_path}")
                
                # Recreate the handler for the new file
                self._setup_logging()
                
            except OSError as e:
                self.audit_logger.error(f"Failed to rotate audit log: {e}")
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate a compliance report for the specified period.
        
        Args:
            days: Number of days to include in the report
            
        Returns:
            Dictionary containing compliance statistics
        """
        if not self.config.audit_logging:
            return {"error": "Audit logging is disabled"}
        
        log_path = Path(self.config.audit_log_path)
        if not log_path.exists():
            return {"error": "No audit log found"}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stats = {
            "period_days": days,
            "total_requests": 0,
            "compliant_requests": 0,
            "non_compliant_requests": 0,
            "domains_accessed": set(),
            "data_categories_collected": set(),
            "common_issues": {},
            "compliance_rate": 0.0
        }
        
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    try:
                        # Handle different log formats
                        if ' - INFO - ' in line:
                            entry_json = line.split(' - INFO - ')[1]
                        else:
                            # If no standard log format, try to parse the whole line as JSON
                            entry_json = line.strip()
                        
                        entry = json.loads(entry_json)
                        
                        # Handle timestamp parsing
                        timestamp_str = entry['timestamp']
                        if 'T' in timestamp_str:
                            # ISO format
                            entry_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            # Try other formats
                            entry_date = datetime.fromisoformat(timestamp_str)
                        
                        if entry_date >= cutoff_date:
                            stats["total_requests"] += 1
                            stats["domains_accessed"].add(entry["domain"])
                            stats["data_categories_collected"].update(entry["data_categories"])
                            
                            if entry["compliance_status"] == "compliant":
                                stats["compliant_requests"] += 1
                            else:
                                stats["non_compliant_requests"] += 1
                                
                                # Count issues
                                for issue in entry["issues"]:
                                    stats["common_issues"][issue] = stats["common_issues"].get(issue, 0) + 1
                    
                    except (json.JSONDecodeError, KeyError, ValueError, IndexError):
                        continue
        
        except OSError:
            return {"error": "Could not read audit log"}
        
        # Calculate compliance rate
        if stats["total_requests"] > 0:
            stats["compliance_rate"] = stats["compliant_requests"] / stats["total_requests"]
        
        # Convert sets to lists for JSON serialization
        stats["domains_accessed"] = list(stats["domains_accessed"])
        stats["data_categories_collected"] = list(stats["data_categories_collected"])
        
        return stats
    
    def validate_data_collection(self, url: str, data: Dict[str, Any], user_agent: str = "") -> bool:
        """
        Validate data collection and log the activity.
        
        Args:
            url: URL where data was collected
            data: Scraped data
            user_agent: User agent used
            
        Returns:
            True if collection is compliant, False otherwise
        """
        is_compliant, issues = self.check_collection_compliance(url, data)
        
        # Log the activity
        self.log_scraping_activity(url, data, user_agent)
        
        # If not compliant, you might want to raise an exception or take other action
        if not is_compliant and self.config.enabled:
            self.audit_logger.warning(f"Non-compliant data collection from {url}: {issues}")
        
        return is_compliant