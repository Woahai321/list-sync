"""Generate sample API response from actual logs."""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.sync_log_parser_prototype import SyncLogParser

def main():
    parser = SyncLogParser()
    
    # Parse log file
    log_paths = [
        "logs/listsync-core.log",
        "../../logs/listsync-core.log",
        "../logs/listsync-core.log"
    ]
    
    sessions = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            sessions = parser.parse_log_file(log_path)
            print(f"Found {len(sessions)} sessions in {log_path}")
            break
    
    if not sessions:
        print("No log file found")
        return
    
    # Get last 2 sessions for sample
    sample_sessions = sessions[-2:] if len(sessions) >= 2 else sessions
    
    # Convert to dict
    output = {
        "sessions": [s.to_dict() for s in sample_sessions],
        "total": len(sessions),
        "limit": 50,
        "offset": 0
    }
    
    # Write to file
    output_file = "development-files/analysis/sample_api_response.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSample API response written to: {output_file}")
    print(f"Total sessions: {len(sessions)}")
    print(f"Sample includes: {len(sample_sessions)} sessions")

if __name__ == "__main__":
    main()

