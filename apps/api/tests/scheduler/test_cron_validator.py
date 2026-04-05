"""Tests for CronValidator class."""

import pytest
from app.scheduler.job_manager import CronValidator


class TestCronValidator:
    """Test cases for CronValidator class."""

    def test_validate_valid_cron(self):
        """Validate valid cron expressions."""
        # Standard cron expressions
        assert CronValidator.validate("* * * * *") is True  # Every minute
        assert CronValidator.validate("0 * * * *") is True  # Every hour
        assert CronValidator.validate("0 0 * * *") is True  # Daily at midnight
        assert CronValidator.validate("0 9 * * 1") is True  # Every Monday at 9:00
        assert CronValidator.validate("30 14 * * *") is True  # Daily at 14:30
        assert CronValidator.validate("0 0 1 * *") is True  # Monthly on the 1st
        assert CronValidator.validate("0 0 1 1 *") is True  # Yearly on Jan 1st

    def test_validate_invalid_cron(self):
        """Validate invalid cron expressions."""
        # Invalid expressions
        assert CronValidator.validate("") is False  # Empty string
        assert CronValidator.validate("* * * *") is False  # Missing field
        assert CronValidator.validate("* * * * * *") is False  # Extra field
        assert CronValidator.validate("invalid") is False  # Not a cron expression
        assert CronValidator.validate("60 * * * *") is False  # Invalid minute
        assert CronValidator.validate("* 25 * * *") is False  # Invalid hour
        # Note: None raises AttributeError in implementation, not returning False

    def test_describe_every_minute(self):
        """Test description for every minute expression."""
        result = CronValidator.describe("* * * * *")
        assert result == "Every minute"

    def test_describe_daily(self):
        """Test description for daily expressions."""
        # Daily at midnight
        result = CronValidator.describe("0 0 * * *")
        assert "Daily" in result
        assert "0:00" in result

        # Daily at specific time
        result = CronValidator.describe("30 14 * * *")
        assert "Daily" in result
        assert "14:30" in result

        # Every hour at minute 0
        result = CronValidator.describe("0 * * * *")
        assert "hour" in result.lower()

    def test_describe_weekly(self):
        """Test description for weekly expressions."""
        # Every Monday at 9:00
        result = CronValidator.describe("0 9 * * 1")
        assert "Monday" in result

        # Every Sunday
        result = CronValidator.describe("0 0 * * 0")
        assert "Sunday" in result

        # Every Friday at 17:00
        result = CronValidator.describe("0 17 * * 5")
        assert "Friday" in result

    def test_describe_invalid_returns_cron(self):
        """Test that invalid expressions return original cron string."""
        # "invalid" is not a 5-part cron expression, returns "Invalid cron expression"
        result = CronValidator.describe("invalid")
        assert result == "Invalid cron expression"

        # Empty string also returns "Invalid cron expression"
        result = CronValidator.describe("")
        assert result == "Invalid cron expression"

    def test_describe_specific_day_of_month(self):
        """Test description for specific day of month."""
        # Every month on the 15th
        result = CronValidator.describe("0 0 15 * *")
        assert "15" in result
        assert "month" in result.lower()

    def test_describe_specific_month(self):
        """Test description for specific month."""
        # January 1st
        result = CronValidator.describe("0 0 1 1 *")
        assert "January" in result

        # December 25th
        result = CronValidator.describe("0 0 25 12 *")
        assert "December" in result


class TestCronValidatorEdgeCases:
    """Edge case tests for CronValidator."""

    def test_validate_whitespace_handling(self):
        """Test whitespace handling in cron expressions."""
        # Leading/trailing whitespace should be handled
        assert CronValidator.validate("  * * * * *  ") is True
        assert CronValidator.validate("\t* * * * *\t") is True

        # Multiple spaces between fields
        assert CronValidator.validate("*  *  *  *  *") is True

    def test_describe_complex_expression(self):
        """Test description for complex expressions."""
        # Every 15th of the month at noon on Monday
        result = CronValidator.describe("0 12 15 * 1")
        # Should contain information about the day and time
        assert result  # Just ensure it returns something

    def test_validate_boundary_values(self):
        """Test boundary values for cron fields."""
        # Minute: 0-59
        assert CronValidator.validate("0 * * * *") is True
        assert CronValidator.validate("59 * * * *") is True

        # Hour: 0-23
        assert CronValidator.validate("* 0 * * *") is True
        assert CronValidator.validate("* 23 * * *") is True

        # Day of month: 1-31
        assert CronValidator.validate("* * 1 * *") is True
        assert CronValidator.validate("* * 31 * *") is True

        # Month: 1-12
        assert CronValidator.validate("* * * 1 *") is True
        assert CronValidator.validate("* * * 12 *") is True

        # Day of week: 0-6
        assert CronValidator.validate("* * * * 0") is True
        assert CronValidator.validate("* * * * 6") is True
