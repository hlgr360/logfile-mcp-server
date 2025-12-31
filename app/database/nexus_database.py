"""
AI: Nexus-specific database operations.

This module handles all database operations specific to Nexus repository logs,
including batch insertion, previews, and nexus-specific queries.
"""

from typing import List, Dict, Any
from datetime import datetime

from app.database.base import BaseLogDatabase
from app.database.models import NexusLog


class NexusLogDatabase(BaseLogDatabase):
    """AI: Database operations specifically for Nexus repository logs."""
    
    def get_model_class(self):
        """AI: Return the NexusLog SQLAlchemy model."""
        return NexusLog
    
    def batch_insert(self, log_data: List[Dict]) -> int:
        """
        AI: Insert a batch of nexus log entries into the database.
        
        Args:
            log_data: List of dictionaries containing parsed nexus log data
            
        Returns:
            Number of entries successfully inserted
        """
        if not log_data:
            return 0
        
        try:
            with self.get_session() as session:
                nexus_logs = []
                for entry in log_data:
                    try:
                        # Create NexusLog object with required fields
                        nexus_log = NexusLog(
                            ip_address=entry.get('ip_address', ''),
                            remote_user=entry.get('remote_user'),
                            timestamp=entry.get('timestamp'),
                            method=entry.get('method', ''),
                            path=entry.get('path', ''),
                            http_version=entry.get('http_version', ''),
                            status_code=entry.get('status_code', 0),
                            response_size=entry.get('response_size'),
                            request_size=entry.get('request_size'),
                            processing_time_ms=entry.get('processing_time_ms'),
                            user_agent=entry.get('user_agent'),
                            thread_info=entry.get('thread_info'),
                            raw_log=entry.get('raw_log', ''),
                            file_source=entry.get('file_source', '')
                        )
                        nexus_logs.append(nexus_log)
                    except Exception as e:
                        print(f"NEXUS_INSERT_ERROR: Skipping invalid entry - {e}")
                        continue
                
                if nexus_logs:
                    session.add_all(nexus_logs)
                    session.flush()  # Force assignment of IDs
                    return len(nexus_logs)
                else:
                    return 0
                    
        except Exception as e:
            print(f"NEXUS_BATCH_INSERT_ERROR: Failed to insert nexus logs - {e}")
            raise
    
    def get_preview(self, limit: int = 10) -> List[Dict]:
        """
        AI: Get a preview of nexus log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of dictionaries containing nexus log data
        """
        try:
            with self.get_session() as session:
                logs = session.query(NexusLog).order_by(NexusLog.id.desc()).limit(limit).all()
                
                result = []
                for log in logs:
                    result.append({
                        'id': log.id,
                        'ip_address': log.ip_address,
                        'remote_user': log.remote_user,
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                        'method': log.method,
                        'path': log.path,
                        'http_version': log.http_version,
                        'status_code': log.status_code,
                        'response_size': log.response_size,
                        'request_size': log.request_size,
                        'processing_time_ms': log.processing_time_ms,
                        'user_agent': log.user_agent,
                        'thread_info': log.thread_info,
                        'file_source': log.file_source,
                        'created_at': log.created_at.isoformat() if log.created_at else None
                    })
                
                return result
                
        except Exception as e:
            print(f"NEXUS_PREVIEW_ERROR: Failed to get nexus preview - {e}")
            return []
    
    def get_top_repositories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most active repositories from nexus logs."""
        try:
            with self.get_session() as session:
                query = """
                SELECT repository, COUNT(*) as activity_count
                FROM nexus_logs 
                WHERE repository IS NOT NULL
                GROUP BY repository 
                ORDER BY activity_count DESC 
                LIMIT :limit
                """
                result = session.execute(query, {'limit': limit})
                return [{'repository': row[0], 'activity_count': row[1]} for row in result.fetchall()]
        except Exception as e:
            print(f"NEXUS_TOP_REPOS_ERROR: Failed to get top repositories - {e}")
            return []
    
    def get_user_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most active users from nexus logs."""
        try:
            with self.get_session() as session:
                query = """
                SELECT username, COUNT(*) as activity_count
                FROM nexus_logs 
                WHERE username IS NOT NULL AND username != ''
                GROUP BY username 
                ORDER BY activity_count DESC 
                LIMIT :limit
                """
                result = session.execute(query, {'limit': limit})
                return [{'username': row[0], 'activity_count': row[1]} for row in result.fetchall()]
        except Exception as e:
            print(f"NEXUS_USER_ACTIVITY_ERROR: Failed to get user activity - {e}")
            return []
    
    def get_action_distribution(self) -> List[Dict[str, Any]]:
        """AI: Get distribution of actions from nexus logs."""
        try:
            with self.get_session() as session:
                query = """
                SELECT action, COUNT(*) as count
                FROM nexus_logs 
                WHERE action IS NOT NULL
                GROUP BY action 
                ORDER BY count DESC
                """
                result = session.execute(query)
                return [{'action': row[0], 'count': row[1]} for row in result.fetchall()]
        except Exception as e:
            print(f"NEXUS_ACTION_DIST_ERROR: Failed to get action distribution - {e}")
            return []
    
    def get_logs_by_timerange(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """AI: Get nexus logs within a specific time range."""
        try:
            with self.get_session() as session:
                logs = session.query(NexusLog).filter(
                    NexusLog.timestamp >= start_time,
                    NexusLog.timestamp <= end_time
                ).order_by(NexusLog.timestamp.desc()).limit(limit).all()
                
                result = []
                for log in logs:
                    result.append({
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                        'level': log.level,
                        'logger': log.logger,
                        'message': log.message,
                        'username': log.username,
                        'repository': log.repository,
                        'action': log.action
                    })
                
                return result
                
        except Exception as e:
            print(f"NEXUS_TIMERANGE_ERROR: Failed to get logs by timerange - {e}")
            return []
