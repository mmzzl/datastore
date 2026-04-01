"""
Monitoring Configuration Module

Provides health check endpoints and job execution status monitoring.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    status: HealthStatus
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
        }


@dataclass
class AlertConfig:
    enabled: bool = True
    dingtalk_webhook: Optional[str] = None
    dingtalk_secret: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    alert_on_failure: bool = True
    alert_on_recovery: bool = True
    failure_threshold: int = 3
    recovery_threshold: int = 1
    cooldown_minutes: int = 5


class HealthChecker:
    """Health check manager for system components."""

    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        self._results: Dict[str, HealthCheckResult] = {}
        self._failure_counts: Dict[str, int] = {}
        self._alert_config: AlertConfig = AlertConfig()
        self._last_alert_time: Dict[str, datetime] = {}

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self._checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check."""
        if name not in self._checks:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component=name,
                message="Check not registered",
            )

        start_time = datetime.now()
        try:
            if asyncio.iscoroutinefunction(self._checks[name]):
                result = await self._checks[name]()
            else:
                result = await asyncio.to_thread(self._checks[name])

            if isinstance(result, HealthCheckResult):
                return result

            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                return HealthCheckResult(
                    status=status,
                    component=name,
                    message=f"Check {'passed' if result else 'failed'}",
                    latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
                )

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component=name,
                message="Check passed",
                details=result if isinstance(result, dict) else {},
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            logger.error(f"Health check {name} failed: {e}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=name,
                message=f"Check error: {str(e)}",
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        tasks = {name: self.run_check(name) for name in self._checks}

        for name, task in tasks.items():
            results[name] = await task
            self._results[name] = results[name]
            self._update_failure_count(name, results[name])

        return results

    def _update_failure_count(self, name: str, result: HealthCheckResult):
        """Track failure counts for alerting."""
        if result.status == HealthStatus.UNHEALTHY:
            self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
        elif result.status == HealthStatus.HEALTHY:
            self._failure_counts[name] = 0

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self._results:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in self._results.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def get_failure_count(self, name: str) -> int:
        """Get failure count for a component."""
        return self._failure_counts.get(name, 0)

    def should_alert(self, name: str, is_failure: bool) -> bool:
        """Check if we should send an alert."""
        if not self._alert_config.enabled:
            return False

        now = datetime.now()
        last_alert = self._last_alert_time.get(name)

        if last_alert:
            cooldown = timedelta(minutes=self._alert_config.cooldown_minutes)
            if now - last_alert < cooldown:
                return False

        count = self.get_failure_count(name)

        if is_failure:
            return count >= self._alert_config.failure_threshold
        else:
            return self._alert_config.alert_on_recovery

    def record_alert_sent(self, name: str):
        """Record that an alert was sent."""
        self._last_alert_time[name] = datetime.now()


class JobExecutionMonitor:
    """Monitor scheduled job execution status."""

    def __init__(self, storage_client=None):
        self.storage = storage_client
        self._job_status: Dict[str, Dict[str, Any]] = {}

    async def check_job_status(
        self,
        job_id: str,
        expected_interval_minutes: int = 1440,
    ) -> HealthCheckResult:
        """Check if a job has been running as expected."""
        try:
            if not self.storage:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    component=f"job_{job_id}",
                    message="Storage not configured",
                )

            db = self.storage.db
            collection = db["job_executions"]

            latest = await asyncio.to_thread(
                lambda: collection.find_one(
                    {"job_id": job_id},
                    sort=[("started_at", -1)],
                )
            )

            if not latest:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    component=f"job_{job_id}",
                    message="No execution history found",
                )

            status = latest.get("status")
            started_at = latest.get("started_at")
            error = latest.get("error")

            if status == "failed":
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    component=f"job_{job_id}",
                    message=f"Last execution failed: {error}",
                    details={"execution_id": latest.get("execution_id")},
                )

            now = datetime.now()
            if started_at:
                time_since = (now - started_at).total_seconds() / 60

                if time_since > expected_interval_minutes * 1.5:
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        component=f"job_{job_id}",
                        message=f"Job may be delayed: {time_since:.0f} minutes since last run",
                        details={"expected_interval": expected_interval_minutes},
                    )

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component=f"job_{job_id}",
                message="Job running normally",
                details={
                    "last_status": status,
                    "last_run": started_at.isoformat() if started_at else None,
                },
            )

        except Exception as e:
            logger.error(f"Failed to check job status: {e}")
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component=f"job_{job_id}",
                message=f"Check error: {str(e)}",
            )

    async def get_recent_failures(
        self,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get recent job failures."""
        if not self.storage:
            return []

        db = self.storage.db
        collection = db["job_executions"]

        cutoff = datetime.now() - timedelta(hours=hours)

        cursor = collection.find({
            "status": "failed",
            "started_at": {"$gte": cutoff},
        }).sort("started_at", -1)

        return await asyncio.to_thread(lambda: list(cursor))


class MonitoringService:
    """Central monitoring service."""

    def __init__(
        self,
        storage_client=None,
        alert_config: Optional[AlertConfig] = None,
    ):
        self.health_checker = HealthChecker()
        self.job_monitor = JobExecutionMonitor(storage_client)
        self.storage = storage_client

        if alert_config:
            self.health_checker._alert_config = alert_config

        self._register_default_checks()

    def _register_default_checks(self):
        """Register default health checks."""
        self.health_checker.register_check(
            "mongodb",
            self._check_mongodb,
        )
        self.health_checker.register_check(
            "disk_space",
            self._check_disk_space,
        )
        self.health_checker.register_check(
            "model_directory",
            self._check_model_directory,
        )

    async def _check_mongodb(self) -> HealthCheckResult:
        """Check MongoDB connectivity."""
        if not self.storage:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component="mongodb",
                message="Storage not configured",
            )

        start_time = datetime.now()
        try:
            await asyncio.to_thread(self.storage.client.admin.command, "ping")
            latency = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="mongodb",
                message="Connected",
                latency_ms=latency,
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component="mongodb",
                message=f"Connection failed: {str(e)}",
            )

    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        import shutil

        try:
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100

            if free_percent < 10:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: only {free_percent:.1f}% disk space remaining"
            elif free_percent < 20:
                status = HealthStatus.DEGRADED
                message = f"Warning: {free_percent:.1f}% disk space remaining"
            else:
                status = HealthStatus.HEALTHY
                message = f"OK: {free_percent:.1f}% disk space available"

            return HealthCheckResult(
                status=status,
                component="disk_space",
                message=message,
                details={
                    "total_gb": total / (1024**3),
                    "used_gb": used / (1024**3),
                    "free_gb": free / (1024**3),
                    "free_percent": free_percent,
                },
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component="disk_space",
                message=f"Check error: {str(e)}",
            )

    async def _check_model_directory(self) -> HealthCheckResult:
        """Check model storage directory."""
        from pathlib import Path

        model_dir = Path("./models")

        try:
            if not model_dir.exists():
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    component="model_directory",
                    message="Model directory does not exist",
                )

            models = list(model_dir.glob("*.pkl"))
            latest = max(models, key=lambda p: p.stat().st_mtime) if models else None

            details = {
                "model_count": len(models),
                "directory": str(model_dir.absolute()),
            }

            if latest:
                from datetime import datetime
                mtime = datetime.fromtimestamp(latest.stat().st_mtime)
                details["latest_model"] = latest.name
                details["latest_model_time"] = mtime.isoformat()

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="model_directory",
                message=f"{len(models)} models stored",
                details=details,
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component="model_directory",
                message=f"Check error: {str(e)}",
            )

    async def get_full_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        checks = await self.health_checker.run_all_checks()

        return {
            "overall_status": self.health_checker.get_overall_status().value,
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in checks.items()},
        }


def create_health_endpoint_handler(monitoring_service: MonitoringService):
    """Create FastAPI health endpoint handler."""
    from fastapi import Response
    import json

    async def health_endpoint():
        report = await monitoring_service.get_full_health_report()

        status_code = 200
        if report["overall_status"] == "unhealthy":
            status_code = 503
        elif report["overall_status"] == "degraded":
            status_code = 200

        return Response(
            content=json.dumps(report, indent=2),
            status_code=status_code,
            media_type="application/json",
        )

    return health_endpoint


def create_ready_endpoint_handler(monitoring_service: MonitoringService):
    """Create FastAPI readiness endpoint handler."""
    from fastapi import Response
    import json

    async def ready_endpoint():
        checks = await monitoring_service.health_checker.run_all_checks()

        essential = ["mongodb"]
        all_healthy = all(
            checks.get(c, HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                component=c,
                message="Not checked"
            )).status == HealthStatus.HEALTHY
            for c in essential
        )

        if all_healthy:
            return Response(
                content=json.dumps({"status": "ready"}),
                status_code=200,
                media_type="application/json",
            )
        else:
            return Response(
                content=json.dumps({
                    "status": "not_ready",
                    "checks": {c: checks[c].to_dict() for c in essential if c in checks}
                }),
                status_code=503,
                media_type="application/json",
            )

    return ready_endpoint
