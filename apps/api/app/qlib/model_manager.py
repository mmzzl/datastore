"""
Qlib Model Manager

This module manages trained model lifecycle including:
- Model storage and retrieval
- Model versioning
- Model metadata management in MongoDB
"""

import os
import pickle
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages Qlib model lifecycle and storage.
    
    Handles:
    - Model storage (filesystem + MongoDB metadata)
    - Model versioning and retrieval
    - Model listing and filtering
    
    Example:
        >>> manager = ModelManager()
        >>> model_id = manager.save_model(model, config, metrics)
        >>> model = manager.load_model(model_id)
        >>> models = manager.list_models(limit=10)
    """
    
    def __init__(
        self,
        model_dir: str = "./models",
        mongo_client = None,
        collection_name: str = "qlib_models",
    ):
        """
        Initialize the model manager.
        
        Args:
            model_dir: Directory to store model files
            mongo_client: MongoDB client for metadata storage
            collection_name: MongoDB collection name for model metadata
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.mongo_client = mongo_client
        self.collection_name = collection_name
        self._collection = None
        
        self._init_collection()
    
    def _init_collection(self):
        """Initialize MongoDB collection."""
        if self.mongo_client is None:
            from ..storage import MongoStorage
            from ..core.config import settings
            
            try:
                self.mongo_client = MongoStorage(
                    host=settings.mongodb_host,
                    port=settings.mongodb_port,
                    db_name=settings.mongodb_database,
                    username=settings.mongodb_username,
                    password=settings.mongodb_password,
                )
                self.mongo_client.connect()
            except Exception as e:
                logger.warning(f"Could not initialize MongoDB client: {e}")
                self.mongo_client = None
    
    @property
    def collection(self):
        """Get MongoDB collection lazily."""
        if self._collection is None and self.mongo_client is not None:
            try:
                self._collection = self.mongo_client.db[self.collection_name]
            except Exception as e:
                logger.error(f"Failed to get collection: {e}")
        return self._collection
    
    def save_model(
        self,
        model: Any,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        model_id: Optional[str] = None,
        status: str = "approved",
    ) -> str:
        """
        Save a trained model.
        
        Args:
            model: The trained model object
            config: Training configuration used
            metrics: Training metrics (IC, Sharpe, etc.)
            model_id: Optional model ID (auto-generated if not provided)
            status: Model status ("approved", "rejected", "pending")
        
        Returns:
            Model ID
        """
        if model_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_id = f"model_{timestamp}"
        
        model_path = self.model_dir / f"{model_id}.pkl"
        
        model_data = {
            "model": model,
            "config": config,
            "metrics": metrics,
            "created_at": datetime.now(),
        }
        
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)
        
        metadata = {
            "model_id": model_id,
            "version": self._get_next_version(),
            "created_at": datetime.now(),
            "config": config,
            "metrics": metrics,
            "file_path": str(model_path),
            "status": status,
        }
        
        if self.collection is not None:
            try:
                self.collection.insert_one(metadata)
                logger.info(f"Model metadata saved to MongoDB: {model_id}")
            except Exception as e:
                logger.error(f"Failed to save model metadata: {e}")
        
        logger.info(f"Model saved: {model_id}")
        return model_id
    
    def load_model(self, model_id: str) -> Optional[Any]:
        """
        Load a trained model by ID.
        
        Args:
            model_id: Model identifier
        
        Returns:
            The model object, or None if not found
        """
        model_path = self.model_dir / f"{model_id}.pkl"
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None
        
        try:
            with open(model_path, "rb") as f:
                model_data = pickle.load(f)
            
            logger.info(f"Model loaded: {model_id}")
            return model_data.get("model")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return None
    
    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get model metadata from MongoDB.
        
        Args:
            model_id: Model identifier
        
        Returns:
            Model metadata dictionary, or None if not found
        """
        if self.collection is None:
            return None
        
        try:
            metadata = self.collection.find_one({"model_id": model_id})
            if metadata:
                metadata.pop("_id", None)
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get model metadata: {e}")
            return None
    
    def list_models(
        self,
        limit: int = 50,
        skip: int = 0,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        ascending: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List all models with pagination.
        
        Args:
            limit: Maximum number of models to return
            skip: Number of models to skip
            status: Filter by status (optional)
            sort_by: Field to sort by
            ascending: Sort order
        
        Returns:
            List of model metadata dictionaries
        """
        if self.collection is None:
            return []
        
        try:
            query = {}
            if status:
                query["status"] = status
            
            cursor = self.collection.find(query)
            
            sort_direction = 1 if ascending else -1
            cursor = cursor.sort(sort_by, sort_direction)
            
            cursor = cursor.skip(skip).limit(limit)
            
            models = []
            for doc in cursor:
                doc.pop("_id", None)
                models.append(doc)
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_latest_model(self, status: str = "approved") -> Optional[Dict[str, Any]]:
        """
        Get the most recent model by status.
        
        Args:
            status: Model status to filter by
        
        Returns:
            Model metadata dictionary, or None if not found
        """
        if self.collection is None:
            return None
        
        try:
            doc = self.collection.find_one(
                {"status": status},
                sort=[("created_at", -1)],
            )
            if doc:
                doc.pop("_id", None)
            return doc
            
        except Exception as e:
            logger.error(f"Failed to get latest model: {e}")
            return None
    
    def update_model_status(self, model_id: str, status: str) -> bool:
        """
        Update model status.
        
        Args:
            model_id: Model identifier
            status: New status value
        
        Returns:
            True if update was successful
        """
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"model_id": model_id},
                {"$set": {"status": status, "updated_at": datetime.now()}},
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update model status: {e}")
            return False
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model (soft delete by marking as deleted).
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if deletion was successful
        """
        model_path = self.model_dir / f"{model_id}.pkl"
        
        if model_path.exists():
            try:
                os.remove(model_path)
                logger.info(f"Model file deleted: {model_path}")
            except Exception as e:
                logger.error(f"Failed to delete model file: {e}")
        
        if self.collection is not None:
            try:
                self.collection.update_one(
                    {"model_id": model_id},
                    {"$set": {"status": "deleted", "deleted_at": datetime.now()}},
                )
            except Exception as e:
                logger.error(f"Failed to mark model as deleted: {e}")
        
        return True
    
    def _get_next_version(self) -> int:
        """Get next version number."""
        if self.collection is None:
            return 1
        
        try:
            latest = self.collection.find_one(
                sort=[("version", -1)],
                projection={"version": 1},
            )
            if latest and "version" in latest:
                return latest["version"] + 1
            return 1
            
        except Exception:
            return 1
    
    def get_model_count(self, status: Optional[str] = None) -> int:
        """
        Get total count of models.
        
        Args:
            status: Filter by status (optional)
        
        Returns:
            Total model count
        """
        if self.collection is None:
            return 0
        
        try:
            query = {}
            if status:
                query["status"] = status
            return self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Failed to get model count: {e}")
            return 0
    
    def compare_models(self, model_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple models by metrics.
        
        Args:
            model_ids: List of model IDs to compare
        
        Returns:
            Dictionary mapping model_id to metrics
        """
        comparison = {}
        
        for model_id in model_ids:
            metadata = self.get_model_metadata(model_id)
            if metadata:
                comparison[model_id] = {
                    "metrics": metadata.get("metrics", {}),
                    "created_at": metadata.get("created_at"),
                    "status": metadata.get("status"),
                }
        
        return comparison
    
    def get_best_model(self, metric: str = "sharpe_ratio") -> Optional[Dict[str, Any]]:
        """
        Get the best model by a specific metric.
        
        Args:
            metric: Metric to compare (e.g., "sharpe_ratio")
        
        Returns:
            Best model metadata, or None if no models found
        """
        if self.collection is None:
            return None
        
        try:
            doc = self.collection.find_one(
                {"status": "approved", f"metrics.{metric}": {"$exists": True}},
                sort=[(f"metrics.{metric}", -1)],
            )
            if doc:
                doc.pop("_id", None)
            return doc
            
        except Exception as e:
            logger.error(f"Failed to get best model: {e}")
            return None
