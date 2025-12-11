"""
In-memory sync status tracking for real-time sync state monitoring.
"""

import threading
import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class SyncState:
    """Current sync state information"""
    is_running: bool = False
    sync_type: Optional[str] = None  # 'full' or 'single'
    session_id: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    list_type: Optional[str] = None  # For single list syncs
    list_id: Optional[str] = None  # For single list syncs
    pid: Optional[int] = None  # Main process PID
    sync_subprocess_pid: Optional[int] = None  # PID of subprocess running sync (for immediate termination)
    cancellation_requested: bool = False


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
        list_id: Optional[str] = None,
        subprocess_pid: Optional[int] = None
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
            self._state.sync_subprocess_pid = subprocess_pid
            self._state.cancellation_requested = False
    
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
            self._state.sync_subprocess_pid = None
            self._state.cancellation_requested = False
    
    def set_subprocess_pid(self, pid: int) -> None:
        """Set the subprocess PID for the running sync (allows immediate termination)"""
        with self._state_lock:
            self._state.sync_subprocess_pid = pid
    
    def get_subprocess_pid(self) -> Optional[int]:
        """Get the subprocess PID if set"""
        with self._state_lock:
            return self._state.sync_subprocess_pid
    
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
                'sync_subprocess_pid': self._state.sync_subprocess_pid,
            }
            
            if self._state.sync_type == 'single':
                info['list_type'] = self._state.list_type
                info['list_id'] = self._state.list_id
            
            return info
    
    def request_cancellation(self) -> None:
        """Request cancellation of the current sync"""
        with self._state_lock:
            self._state.cancellation_requested = True
    
    def is_cancellation_requested(self) -> bool:
        """Check if cancellation has been requested"""
        with self._state_lock:
            return self._state.cancellation_requested
    
    def clear_cancellation(self) -> None:
        """Clear the cancellation request flag"""
        with self._state_lock:
            self._state.cancellation_requested = False


# Global instance for easy access
def get_sync_tracker() -> SyncStatusTracker:
    """Get the global sync status tracker instance"""
    return SyncStatusTracker()


# ---------------------------------------------
# Cross-process cancellation persistence
# ---------------------------------------------

_CANCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cancel_requests.json")
_PAUSE_KEY = "pause_until"


def _ensure_cancel_file_dir():
    os.makedirs(os.path.dirname(_CANCEL_FILE), exist_ok=True)


def _read_cancel_requests() -> dict:
    try:
        if not os.path.exists(_CANCEL_FILE):
            return {}
        with open(_CANCEL_FILE, "r") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _write_cancel_requests(data: dict):
    try:
        _ensure_cancel_file_dir()
        with open(_CANCEL_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        # Fail silently; the API still sets in-memory flag
        pass


def set_cancel_request(session_id: str):
    data = _read_cancel_requests()
    data[session_id] = {"cancel_requested": True}
    _write_cancel_requests(data)


def clear_cancel_request(session_id: str):
    data = _read_cancel_requests()
    if session_id in data:
        data.pop(session_id, None)
        _write_cancel_requests(data)


def is_cancel_requested_persisted(session_id: str) -> bool:
    data = _read_cancel_requests()
    entry = data.get(session_id)
    return bool(entry and entry.get("cancel_requested"))


# ---------------------------------------------
# Pause scheduling until a given timestamp
# ---------------------------------------------

def set_pause_until(timestamp_iso: str):
    data = _read_cancel_requests()
    data[_PAUSE_KEY] = timestamp_iso
    _write_cancel_requests(data)


def get_pause_until() -> Optional[str]:
    data = _read_cancel_requests()
    return data.get(_PAUSE_KEY)


def clear_pause_until():
    data = _read_cancel_requests()
    if _PAUSE_KEY in data:
        data.pop(_PAUSE_KEY, None)
        _write_cancel_requests(data)
