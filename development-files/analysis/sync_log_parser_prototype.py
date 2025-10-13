"""
Prototype: Sync Log Parser
This module demonstrates how to parse sync sessions from logs.
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class SyncType(Enum):
    FULL = "full"
    SINGLE = "single"


class ItemStatus(Enum):
    REQUESTED = "requested"
    ALREADY_AVAILABLE = "already_available"
    ALREADY_REQUESTED = "already_requested"
    SKIPPED = "skipped"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class SyncList:
    """Represents a list that was synced."""
    type: str
    id: str
    url: Optional[str] = None
    item_count: int = 0


@dataclass
class SyncItem:
    """Represents an individual item processed during sync."""
    title: str
    status: str
    progress_number: int
    progress_total: int
    timestamp: str
    year: Optional[int] = None
    media_type: str = "movie"
    error_details: Optional[str] = None


@dataclass
class SyncResults:
    """Results summary for a sync session."""
    requested: int = 0
    already_available: int = 0
    already_requested: int = 0
    skipped: int = 0
    not_found: int = 0
    error: int = 0


@dataclass
class SyncSession:
    """Complete sync session data."""
    id: str
    type: SyncType
    start_timestamp: str
    end_timestamp: Optional[str] = None
    duration: Optional[float] = None
    version: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    lists: List[SyncList] = field(default_factory=list)
    results: SyncResults = field(default_factory=SyncResults)
    items: List[SyncItem] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    not_found_items: List[str] = field(default_factory=list)
    average_time_ms: Optional[float] = None
    total_time_seconds: Optional[float] = None
    status: str = "in_progress"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['type'] = self.type.value
        return data


class SyncLogParser:
    """Parser for sync log files."""
    
    # Patterns for detecting log elements
    TIMESTAMP_PATTERN = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
    
    # Session markers
    FULL_SYNC_START = r'📊\s+Total unique media items ready for sync:\s*(\d+)'
    SINGLE_SYNC_START = r'🎯\s+Single List Sync:\s+(\w+):(.+)'
    SYNC_SUMMARY_START = r'Soluify - List Sync Summary'
    SYNC_SUMMARY_DASHES = r'^[-─]{50,}$'
    SINGLE_SYNC_COMPLETE = r'✅\s+Single list sync completed:\s*(\d+)\s*requested,\s*(\d+)\s*errors'
    
    # List fetching
    LIST_FETCH_START = r'🔍\s+Fetching items from (\w+) list:\s+(.+?)\.\.\.?$'
    LIST_FETCH_SUCCESS = r'✅\s+Found (\d+) items in (\w+) list:\s+(.+?)$'
    
    # Processing
    PROCESSING_START = r'🎬\s+Processing (\d+) media items'
    
    # Item status patterns with emojis
    ITEM_PATTERNS = [
        (r'✅\s+(.+?):\s*(?:Successfully\s+)?Requested\s*\((\d+)/(\d+)\)', ItemStatus.REQUESTED.value),
        (r'☑️\s+(.+?):\s*Already Available\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_AVAILABLE.value),
        (r'📌\s+(.+?):\s*Already Requested\s*\((\d+)/(\d+)\)', ItemStatus.ALREADY_REQUESTED.value),
        (r'⏭️\s+(.+?):\s*Skipped\s*\((\d+)/(\d+)\)', ItemStatus.SKIPPED.value),
        (r'❓\s+(.+?):\s*Not Found\s*\((\d+)/(\d+)\)', ItemStatus.NOT_FOUND.value),
        (r'❌\s+(.+?):\s*(?:Error|Failed)\s*\((\d+)/(\d+)\)', ItemStatus.ERROR.value),
    ]
    
    # Summary patterns
    TOTAL_TIME_PATTERN = r'Total Time:\s*(\d+)m\s*(\d+)s'
    AVG_TIME_PATTERN = r'Avg Time:\s*([\d.]+)ms/item'
    RESULT_PATTERN = r'[✅☑️📌⏭️❌]\s*(\w+(?:\s+\w+)?):\s*(\d+)'
    MEDIA_TYPE_PATTERN = r'(Movies|TV Shows):\s*(\d+)\s*\(([\d.]+)%\)'
    SYNCED_LIST_PATTERN = r'📋\s+(\w+):\s+(https?://\S+)'
    NOT_FOUND_ITEM_PATTERN = r'•\s+(.+?)\s*\((Error:|Not Found)'
    
    # Version
    VERSION_PATTERN = r'Soluify\s*-\s*\{(.+?)\}'
    
    def __init__(self):
        self.sessions: List[SyncSession] = []
    
    def extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        match = re.match(self.TIMESTAMP_PATTERN, line)
        if match:
            try:
                dt = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                return dt.isoformat()
            except:
                return None
        return None
    
    def detect_session_start(self, line: str) -> Optional[tuple]:
        """
        Detect if line marks start of a sync session.
        Returns: (session_type, metadata) or None
        """
        # Check for full sync start
        full_match = re.search(self.FULL_SYNC_START, line)
        if full_match:
            return (SyncType.FULL, {'total_items': int(full_match.group(1))})
        
        # Check for single list sync start
        single_match = re.search(self.SINGLE_SYNC_START, line)
        if single_match:
            list_type = single_match.group(1)
            list_id = single_match.group(2).strip()
            return (SyncType.SINGLE, {'list_type': list_type, 'list_id': list_id})
        
        return None
    
    def detect_session_end(self, line: str, session_type: SyncType) -> bool:
        """Detect if line marks end of a sync session."""
        if session_type == SyncType.FULL:
            return bool(re.search(self.SYNC_SUMMARY_START, line) or 
                       re.search(self.SYNC_SUMMARY_DASHES, line))
        else:  # SINGLE
            return bool(re.search(self.SINGLE_SYNC_COMPLETE, line))
    
    def parse_list_fetch(self, line: str) -> Optional[tuple]:
        """
        Parse list fetching line.
        Returns: (list_type, list_id, item_count) or None
        """
        # Check for fetch start
        fetch_match = re.search(self.LIST_FETCH_START, line)
        if fetch_match:
            return (fetch_match.group(1), fetch_match.group(2), None)
        
        # Check for fetch success (with count)
        success_match = re.search(self.LIST_FETCH_SUCCESS, line)
        if success_match:
            return (success_match.group(2), success_match.group(3), int(success_match.group(1)))
        
        return None
    
    def parse_item_status(self, line: str, timestamp: str) -> Optional[SyncItem]:
        """Parse an item processing line."""
        for pattern, status in self.ITEM_PATTERNS:
            match = re.search(pattern, line)
            if match:
                title = match.group(1).strip()
                progress_num = int(match.group(2))
                progress_total = int(match.group(3))
                
                # Extract year from title
                year = None
                year_match = re.search(r'\((\d{4})\)|\s(\d{4})$', title)
                if year_match:
                    year = int(year_match.group(1) or year_match.group(2))
                    title = re.sub(r'\s*\(?\d{4}\)?$', '', title).strip()
                
                # Extract error details for error status
                error_details = None
                if status == ItemStatus.ERROR.value:
                    error_match = re.search(r'Error:\s*(.+)$', line)
                    if error_match:
                        error_details = error_match.group(1).strip()
                
                return SyncItem(
                    title=title,
                    status=status,
                    progress_number=progress_num,
                    progress_total=progress_total,
                    timestamp=timestamp,
                    year=year,
                    error_details=error_details
                )
        
        return None
    
    def parse_summary_section(self, lines: List[str], session: SyncSession):
        """Parse the summary section of a full sync."""
        in_results = False
        in_media_types = False
        in_synced_lists = False
        in_not_found = False
        
        for line in lines:
            # Total Time
            time_match = re.search(self.TOTAL_TIME_PATTERN, line)
            if time_match:
                minutes = int(time_match.group(1))
                seconds = int(time_match.group(2))
                session.total_time_seconds = minutes * 60 + seconds
            
            # Average Time
            avg_match = re.search(self.AVG_TIME_PATTERN, line)
            if avg_match:
                session.average_time_ms = float(avg_match.group(1))
            
            # Results section
            if 'Results' in line and '─' in lines[lines.index(line) - 1] if lines.index(line) > 0 else False:
                in_results = True
                in_media_types = False
                in_synced_lists = False
                in_not_found = False
                continue
            
            if in_results:
                result_match = re.search(self.RESULT_PATTERN, line)
                if result_match:
                    status_name = result_match.group(1).lower().replace(' ', '_')
                    count = int(result_match.group(2))
                    
                    if 'requested' in status_name and 'already' not in status_name:
                        session.results.requested = count
                    elif 'available' in status_name:
                        session.results.already_available = count
                    elif 'already' in status_name and 'requested' in status_name:
                        session.results.already_requested = count
                    elif 'skipped' in status_name:
                        session.results.skipped = count
            
            # Media Types section
            if 'Media Types' in line:
                in_media_types = True
                in_results = False
                continue
            
            # Synced Lists section
            if 'Synced Lists' in line:
                in_synced_lists = True
                in_media_types = False
                continue
            
            if in_synced_lists:
                list_match = re.search(self.SYNCED_LIST_PATTERN, line)
                if list_match:
                    # Update existing list with URL
                    list_type = list_match.group(1)
                    list_url = list_match.group(2)
                    
                    for sync_list in session.lists:
                        if sync_list.type.upper() == list_type.upper():
                            sync_list.url = list_url
                            break
            
            # Not Found section
            if 'Not Found Items' in line:
                in_not_found = True
                in_synced_lists = False
                continue
            
            if in_not_found:
                not_found_match = re.search(self.NOT_FOUND_ITEM_PATTERN, line)
                if not_found_match:
                    item_name = not_found_match.group(1).strip()
                    session.not_found_items.append(item_name)
    
    def parse_log_file(self, log_path: str) -> List[SyncSession]:
        """
        Parse entire log file and extract all sync sessions.
        
        Args:
            log_path: Path to log file
            
        Returns:
            List of parsed sync sessions
        """
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []
        
        sessions = []
        current_session: Optional[SyncSession] = None
        current_lists: Dict[str, SyncList] = {}  # Track lists being fetched
        summary_lines: List[str] = []
        in_summary = False
        last_timestamp_in_session: Optional[str] = None  # Track last timestamp
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            timestamp = self.extract_timestamp(line)
            
            # Update last timestamp for current session
            if current_session and timestamp:
                last_timestamp_in_session = timestamp
                # Continuously update end_timestamp so we always have the latest
                current_session.end_timestamp = timestamp
            
            # Detect session start
            session_start = self.detect_session_start(line)
            if session_start:
                # Save previous session if exists
                if current_session:
                    # Calculate duration before saving
                    if current_session.start_timestamp and current_session.end_timestamp:
                        try:
                            start = datetime.fromisoformat(current_session.start_timestamp)
                            end = datetime.fromisoformat(current_session.end_timestamp)
                            current_session.duration = (end - start).total_seconds()
                        except:
                            pass
                    
                    current_session.status = "completed"
                    current_session.processed_items = len(current_session.items)
                    sessions.append(current_session)
                
                # Start new session
                session_type, metadata = session_start
                session_id = f"sync_{timestamp}_{session_type.value}"
                
                current_session = SyncSession(
                    id=session_id,
                    type=session_type,
                    start_timestamp=timestamp or datetime.now().isoformat(),
                    total_items=metadata.get('total_items', 0)
                )
                
                current_lists = {}
                in_summary = False
                summary_lines = []
                last_timestamp_in_session = timestamp  # Reset for new session
                continue
            
            if not current_session:
                continue
            
            # Extract version
            if not current_session.version:
                version_match = re.search(self.VERSION_PATTERN, line)
                if version_match:
                    current_session.version = version_match.group(1)
            
            # Parse list fetching
            list_info = self.parse_list_fetch(line)
            if list_info:
                list_type, list_id, item_count = list_info
                
                # Create or update list
                list_key = f"{list_type}:{list_id}"
                if list_key not in current_lists:
                    current_lists[list_key] = SyncList(
                        type=list_type,
                        id=list_id,
                        item_count=0
                    )
                
                if item_count is not None:
                    current_lists[list_key].item_count = item_count
                    # Add to session lists if not already there
                    if current_lists[list_key] not in current_session.lists:
                        current_session.lists.append(current_lists[list_key])
            
            # Parse item status
            item = self.parse_item_status(line, timestamp or datetime.now().isoformat())
            if item:
                current_session.items.append(item)
                
                # Update results
                if item.status == ItemStatus.REQUESTED.value:
                    current_session.results.requested += 1
                elif item.status == ItemStatus.ALREADY_AVAILABLE.value:
                    current_session.results.already_available += 1
                elif item.status == ItemStatus.ALREADY_REQUESTED.value:
                    current_session.results.already_requested += 1
                elif item.status == ItemStatus.SKIPPED.value:
                    current_session.results.skipped += 1
                elif item.status == ItemStatus.NOT_FOUND.value:
                    current_session.results.not_found += 1
                elif item.status == ItemStatus.ERROR.value:
                    current_session.results.error += 1
                    current_session.errors.append({
                        'title': item.title,
                        'error': item.error_details or 'Unknown error',
                        'timestamp': item.timestamp
                    })
            
            # Detect summary section start
            if re.search(self.SYNC_SUMMARY_START, line) or re.search(self.SYNC_SUMMARY_DASHES, line):
                in_summary = True
                summary_lines = []
                continue
            
            if in_summary:
                summary_lines.append(line)
            
            # Detect session end
            if self.detect_session_end(line, current_session.type):
                # end_timestamp is already set by the continuous update above
                # But make sure it's set if we somehow missed it
                if not current_session.end_timestamp:
                    current_session.end_timestamp = timestamp or last_timestamp_in_session or datetime.now().isoformat()
                
                # Parse summary if we have one
                if summary_lines and current_session.type == SyncType.FULL:
                    self.parse_summary_section(summary_lines, current_session)
                
                # Calculate duration if both timestamps exist
                if current_session.start_timestamp and current_session.end_timestamp:
                    try:
                        start = datetime.fromisoformat(current_session.start_timestamp)
                        end = datetime.fromisoformat(current_session.end_timestamp)
                        current_session.duration = (end - start).total_seconds()
                    except:
                        pass
                
                current_session.status = "completed"
                current_session.processed_items = len(current_session.items)
                sessions.append(current_session)
                current_session = None
                in_summary = False
        
        # Handle unclosed session (sync still in progress or no end marker)
        if current_session:
            # end_timestamp should already be set from continuous updates
            # Calculate duration if both timestamps exist
            if current_session.start_timestamp and current_session.end_timestamp:
                try:
                    start = datetime.fromisoformat(current_session.start_timestamp)
                    end = datetime.fromisoformat(current_session.end_timestamp)
                    current_session.duration = (end - start).total_seconds()
                except:
                    pass
            
            current_session.status = "in_progress"
            current_session.processed_items = len(current_session.items)
            sessions.append(current_session)
        
        return sessions


# Example usage
if __name__ == "__main__":
    parser = SyncLogParser()
    
    # Parse log file
    sessions = parser.parse_log_file("logs/listsync-core.log")
    
    print(f"Found {len(sessions)} sync sessions:")
    for session in sessions:
        print(f"\n{'='*60}")
        print(f"Session ID: {session.id}")
        print(f"Type: {session.type.value}")
        print(f"Start: {session.start_timestamp}")
        print(f"End: {session.end_timestamp}")
        print(f"Duration: {session.duration}s" if session.duration is not None else "Duration: N/A")
        print(f"Status: {session.status}")
        print(f"Total Items: {session.total_items}")
        print(f"Processed Items: {session.processed_items}")
        print(f"\nLists ({len(session.lists)}):")
        for lst in session.lists:
            print(f"  - {lst.type}: {lst.id} ({lst.item_count} items)")
        print(f"\nResults:")
        print(f"  Requested: {session.results.requested}")
        print(f"  Available: {session.results.already_available}")
        print(f"  Already Requested: {session.results.already_requested}")
        print(f"  Skipped: {session.results.skipped}")
        print(f"  Not Found: {session.results.not_found}")
        print(f"  Errors: {session.results.error}")
        
        if session.errors:
            print(f"\nErrors ({len(session.errors)}):")
            for error in session.errors[:5]:  # Show first 5
                print(f"  - {error['title']}: {error['error']}")
        
        if session.average_time_ms:
            print(f"\nPerformance:")
            print(f"  Avg Time: {session.average_time_ms:.1f}ms/item")
            print(f"  Total Time: {session.total_time_seconds}s" if session.total_time_seconds else "")

