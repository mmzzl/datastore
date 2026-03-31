from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError, DuplicateKeyError
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)


class JobStore:
    """MongoDB persistence for scheduler jobs and executions."""

    def __init__(self, mongo_client: MongoClient, db_name: str):
        self.db = mongo_client[db_name]
        self.jobs_collection = self.db["scheduler_jobs"]
        self.executions_collection = self.db["job_executions"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure required indexes exist."""
        try:
            self.executions_collection.create_index(
                [("job_id", 1), ("status", 1)],
                unique=True,
                partialFilterExpression={"status": "running"}
            )
            logger.info("Created unique index on job_executions for running status")
        except PyMongoError as e:
            logger.warning(f"Could not create index: {e}")

    async def create_job_async(self, job_data: Dict[str, Any]) -> str:
        """Create a new scheduled job."""
        job_id = job_data.get("job_id") or str(uuid.uuid4())
        job_data["job_id"] = job_id
        job_data["created_at"] = datetime.now()
        job_data["updated_at"] = datetime.now()

        try:
            await asyncio.to_thread(self.jobs_collection.insert_one, job_data)
            logger.info(f"Created job: {job_id}")
            return job_id
        except PyMongoError as e:
            logger.error(f"Failed to create job: {e}")
            raise

    async def get_job_async(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        try:
            job = await asyncio.to_thread(
                self.jobs_collection.find_one,
                {"job_id": job_id}
            )
            if job:
                job["_id"] = str(job["_id"])
            return job
        except PyMongoError as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise

    async def list_jobs_async(
        self,
        job_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List jobs with optional filtering and pagination."""
        query = {}
        if job_type:
            query["job_type"] = job_type
        if enabled is not None:
            query["enabled"] = enabled

        try:
            total = await asyncio.to_thread(
                self.jobs_collection.count_documents,
                query
            )
            cursor = self.jobs_collection.find(query).skip(skip).limit(limit)
            jobs = await asyncio.to_thread(list, cursor)
            for job in jobs:
                job["_id"] = str(job["_id"])
            return jobs, total
        except PyMongoError as e:
            logger.error(f"Failed to list jobs: {e}")
            raise

    async def update_job_async(self, job_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a job."""
        update_data["updated_at"] = datetime.now()

        try:
            result = await asyncio.to_thread(
                self.jobs_collection.update_one,
                {"job_id": job_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise

    async def delete_job_async(self, job_id: str) -> bool:
        """Delete a job."""
        try:
            result = await asyncio.to_thread(
                self.jobs_collection.delete_one,
                {"job_id": job_id}
            )
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise

    async def update_job_run_times_async(
        self,
        job_id: str,
        last_run: Optional[datetime],
        next_run: Optional[datetime]
    ) -> bool:
        """Update job last_run and next_run times."""
        try:
            update_data = {"updated_at": datetime.now()}
            if last_run is not None:
                update_data["last_run"] = last_run
            if next_run is not None:
                update_data["next_run"] = next_run

            result = await asyncio.to_thread(
                self.jobs_collection.update_one,
                {"job_id": job_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update run times for {job_id}: {e}")
            raise

    async def try_acquire_execution_lock(
        self,
        job_id: str,
        job_type: str
    ) -> Tuple[bool, Optional[str]]:
        """Atomically try to acquire execution lock for a job.

        Uses find_one_and_update with upsert to atomically check and create
        a running execution. Returns (acquired, execution_id).

        If another execution is already running, returns (False, None).
        """
        execution_id = str(uuid.uuid4())
        now = datetime.now()

        try:
            result = await asyncio.to_thread(
                self.executions_collection.find_one_and_update,
                {"job_id": job_id, "status": "running"},
                {"$setOnInsert": {
                    "execution_id": execution_id,
                    "job_type": job_type,
                    "status": "running",
                    "started_at": now
                }},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )

            if result.get("execution_id") == execution_id:
                logger.info(f"Acquired execution lock: {execution_id}")
                return True, execution_id
            else:
                existing_exec_id = result.get("execution_id")
                logger.warning(f"Job {job_id} already running with execution {existing_exec_id}")
                return False, None

        except DuplicateKeyError:
            logger.warning(f"Job {job_id} already running (duplicate key)")
            return False, None
        except PyMongoError as e:
            logger.error(f"Failed to acquire execution lock: {e}")
            raise

    async def create_execution_async(self, execution_data: Dict[str, Any]) -> str:
        """Create an execution record."""
        execution_id = str(uuid.uuid4())
        execution_data["execution_id"] = execution_id
        execution_data["started_at"] = datetime.now()

        try:
            await asyncio.to_thread(self.executions_collection.insert_one, execution_data)
            logger.info(f"Created execution: {execution_id}")
            return execution_id
        except PyMongoError as e:
            logger.error(f"Failed to create execution: {e}")
            raise

    async def update_execution_async(
        self,
        execution_id: str,
        status: str,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update execution status and result."""
        update_data = {
            "status": status,
            "completed_at": datetime.now()
        }
        if result is not None:
            update_data["result"] = result
        if error_message is not None:
            update_data["error_message"] = error_message

        try:
            exec_result = await asyncio.to_thread(
                self.executions_collection.update_one,
                {"execution_id": execution_id},
                {"$set": update_data}
            )
            return exec_result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update execution {execution_id}: {e}")
            raise

    async def get_executions_async(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get execution history for a job with pagination."""
        try:
            query = {"job_id": job_id}
            total = await asyncio.to_thread(
                self.executions_collection.count_documents,
                query
            )
            cursor = self.executions_collection.find(query).sort("started_at", -1).skip(skip).limit(limit)
            executions = await asyncio.to_thread(list, cursor)
            for exec_doc in executions:
                exec_doc["_id"] = str(exec_doc["_id"])
            return executions, total
        except PyMongoError as e:
            logger.error(f"Failed to get executions for {job_id}: {e}")
            raise

    async def get_running_execution_async(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Check if a job is currently running."""
        try:
            exec_doc = await asyncio.to_thread(
                self.executions_collection.find_one,
                {"job_id": job_id, "status": "running"}
            )
            if exec_doc:
                exec_doc["_id"] = str(exec_doc["_id"])
            return exec_doc
        except PyMongoError as e:
            logger.error(f"Failed to check running execution: {e}")
            raise
