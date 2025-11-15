"""
In-memory sync status tracking for real-time sync state monitoring.
"""

import threading
import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class SyncState:
    """Current sync state information"""
    is_running: bool = False
    sync_type: Optional[str] = None  # 'full' or 'single'
    session_id: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    list_type: Optional[str] = None  # For single list syncs
    list_id: Optional[str] = None  # For single list syncs
    pid: Optional[int] = None


class SyncStatusTracker:
    """Thread-safe singleton for tracking sync status"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SyncStatusTracker, cls).__new__(cls)
                    cls._instance._state = SyncState()
                    cls._instance._state_lock = threading.Lock()
        return cls._instance
    
    def start_sync(
        self,
        sync_type: str,
        session_id: str,
        list_type: Optional[str] = None,
        list_id: Optional[str] = None
    ) -> None:
        """Mark sync as started"""
        import os
        with self._state_lock:
            self._state.is_running = True
            self._state.sync_type = sync_type
            self._state.session_id = session_id
            self._state.start_time = datetime.datetime.now()
            self._state.list_type = list_type
            self._state.list_id = list_id
            self._state.pid = os.getpid()
    
    def end_sync(self) -> None:
        """Mark sync as completed"""
        with self._state_lock:
            self._state.is_running = False
            self._state.sync_type = None
            self._state.session_id = None
            self._state.start_time = None
            self._state.list_type = None
            self._state.list_id = None
            self._state.pid = None
    
    def get_state(self) -> Dict[str, Any]:
        """Get current sync state as dictionary"""
        with self._state_lock:
            state_dict = asdict(self._state)
            # Convert datetime to ISO format string
            if state_dict.get('start_time'):
                state_dict['start_time'] = self._state.start_time.isoformat()
            return state_dict
    
    def is_sync_running(self) -> bool:
        """Check if sync is currently running"""
        with self._state_lock:
            return self._state.is_running
    
    def get_sync_info(self) -> Optional[Dict[str, Any]]:
        """Get sync information if running, None otherwise"""
        with self._state_lock:
            if not self._state.is_running:
                return None
            
            info = {
                'sync_type': self._state.sync_type,
                'session_id': self._state.session_id,
                'start_time': self._state.start_time.isoformat() if self._state.start_time else None,
                'pid': self._state.pid,
            }
            
            if self._state.sync_type == 'single':
                info['list_type'] = self._state.list_type
                info['list_id'] = self._state.list_id
            
            return info


# Global instance for easy access
def get_sync_tracker() -> SyncStatusTracker:
    """Get the global sync status tracker instance"""
    return SyncStatusTracker()
