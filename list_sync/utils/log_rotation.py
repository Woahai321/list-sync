#!/usr/bin/env python3
"""
Log Rotation Utility for ListSync
Handles automatic log rotation when files reach 20MB
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional

class LogRotator:
    """Handles log file rotation when files exceed size limits"""
    
    def __init__(self, log_file_path: str, max_size_mb: int = 20, max_backups: int = 5):
        """
        Initialize log rotator
        
        Args:
            log_file_path: Path to the main log file
            max_size_mb: Maximum size in MB before rotation (default: 20MB)
            max_backups: Maximum number of backup files to keep (default: 5)
        """
        self.log_file_path = Path(log_file_path)
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.max_backups = max_backups
        self.logger = logging.getLogger(__name__)
    
    def should_rotate(self) -> bool:
        """Check if the log file should be rotated"""
        if not self.log_file_path.exists():
            return False
        
        try:
            file_size = self.log_file_path.stat().st_size
            return file_size >= self.max_size_bytes
        except OSError as e:
            self.logger.error(f"Error checking log file size: {e}")
            return False
    
    def rotate_log(self) -> bool:
        """
        Rotate the log file if it exceeds the size limit
        
        Returns:
            bool: True if rotation was performed, False otherwise
        """
        if not self.should_rotate():
            return False
        
        try:
            # Remove the oldest backup if we're at the limit
            oldest_backup = self.log_file_path.with_suffix(f'.{self.max_backups}.log')
            if oldest_backup.exists():
                oldest_backup.unlink()
                self.logger.info(f"Removed oldest backup: {oldest_backup}")
            
            # Shift existing backups
            for i in range(self.max_backups - 1, 0, -1):
                old_backup = self.log_file_path.with_suffix(f'.{i}.log')
                new_backup = self.log_file_path.with_suffix(f'.{i + 1}.log')
                
                if old_backup.exists():
                    shutil.move(str(old_backup), str(new_backup))
                    self.logger.debug(f"Moved {old_backup} to {new_backup}")
            
            # Move current log to backup.1
            backup_1 = self.log_file_path.with_suffix('.1.log')
            shutil.move(str(self.log_file_path), str(backup_1))
            self.logger.info(f"Rotated log file: {self.log_file_path} -> {backup_1}")
            
            # Create new empty log file
            self.log_file_path.touch()
            self.logger.info(f"Created new log file: {self.log_file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during log rotation: {e}")
            return False
    
    def get_available_log_files(self) -> list:
        """
        Get list of available log files (main + backups)
        
        Returns:
            list: List of log file paths in order (newest first)
        """
        log_files = []
        
        # Add main log file if it exists
        if self.log_file_path.exists():
            log_files.append(self.log_file_path)
        
        # Add backup files
        for i in range(1, self.max_backups + 1):
            backup_file = self.log_file_path.with_suffix(f'.{i}.log')
            if backup_file.exists():
                log_files.append(backup_file)
        
        return log_files
    
    def get_log_file_info(self) -> dict:
        """
        Get information about log files
        
        Returns:
            dict: Information about log files
        """
        info = {
            'main_file': str(self.log_file_path),
            'main_exists': self.log_file_path.exists(),
            'main_size_mb': 0,
            'backup_files': [],
            'total_size_mb': 0,
            'should_rotate': self.should_rotate()
        }
        
        if self.log_file_path.exists():
            info['main_size_mb'] = self.log_file_path.stat().st_size / (1024 * 1024)
            info['total_size_mb'] += info['main_size_mb']
        
        # Get backup file info
        for i in range(1, self.max_backups + 1):
            backup_file = self.log_file_path.with_suffix(f'.{i}.log')
            if backup_file.exists():
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                backup_info = {
                    'path': str(backup_file),
                    'size_mb': size_mb,
                    'backup_number': i
                }
                info['backup_files'].append(backup_info)
                info['total_size_mb'] += size_mb
        
        return info

def setup_log_rotation(log_file_path: str = "data/list_sync.log") -> LogRotator:
    """
    Set up log rotation for the main log file
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        LogRotator: Configured log rotator instance
    """
    rotator = LogRotator(log_file_path)
    
    # Check if rotation is needed on startup
    if rotator.should_rotate():
        logging.info("Log file exceeds size limit, performing rotation...")
        rotator.rotate_log()
    
    return rotator

# Global rotator instance
_log_rotator: Optional[LogRotator] = None

def get_log_rotator() -> LogRotator:
    """Get the global log rotator instance"""
    global _log_rotator
    if _log_rotator is None:
        _log_rotator = setup_log_rotation()
    return _log_rotator

def check_and_rotate_logs():
    """Check if logs need rotation and rotate if necessary"""
    rotator = get_log_rotator()
    return rotator.rotate_log()

if __name__ == "__main__":
    # Test the log rotator
    rotator = LogRotator("data/list_sync.log")
    
    print("Log Rotation Test")
    print("=" * 50)
    
    info = rotator.get_log_file_info()
    print(f"Main file: {info['main_file']}")
    print(f"Main file exists: {info['main_exists']}")
    print(f"Main file size: {info['main_size_mb']:.2f} MB")
    print(f"Should rotate: {info['should_rotate']}")
    print(f"Backup files: {len(info['backup_files'])}")
    print(f"Total size: {info['total_size_mb']:.2f} MB")
    
    if info['should_rotate']:
        print("\nPerforming log rotation...")
        success = rotator.rotate_log()
        print(f"Rotation successful: {success}")
    else:
        print("\nNo rotation needed")
