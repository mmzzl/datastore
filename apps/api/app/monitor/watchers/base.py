from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging


class BaseWatcher(ABC):
    def __init__(self, data_manager=None):
        from app.data_source import DataSourceManager

        self.data_manager = data_manager or DataSourceManager()
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def collect(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    def run_once(self) -> List[Dict[str, Any]]:
        data = self.collect()
        if not data:
            return []
        return self.evaluate(data)

    def get_name(self) -> str:
        return self.__class__.__name__.replace("Watcher", "")
