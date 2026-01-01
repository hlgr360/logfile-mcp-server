"""
AI: Nginx-specific database operations.

This module handles all database operations specific to nginx access logs,
including batch insertion, previews, and nginx-specific queries.
"""

from typing import List, Dict, Any
from datetime import datetime

from app.database.base import BaseLogDatabase
from app.database.models import NginxLog
from ..utils.logger import logger


class NginxLogDatabase(BaseLogDatabase):
    """AI: Database operations specifically for nginx access logs."""
    
    def get_model_class(self):
        """AI: Return the NginxLog SQLAlchemy model."""
        return NginxLog
    
    def batch_insert(self, log_data: List[Dict]) -> int:
        """
        AI: Insert a batch of nginx log entries into the database.
        
        Args:
            log_data: List of dictionaries containing parsed nginx log data
            
        Returns:
            Number of entries successfully inserted
        """
        if not log_data:
            return 0
        
        try:
            with self.get_session() as session:
                nginx_logs = []
                for entry in log_data:
                    try:
                        # Create NginxLog object with required fields
                        nginx_log = NginxLog(
                            ip_address=entry.get('ip_address', ''),
                            remote_user=entry.get('remote_user'),
                            timestamp=entry.get('timestamp'),
                            method=entry.get('method', ''),
                            path=entry.get('path', ''),
                            http_version=entry.get('http_version', ''),
                            status_code=entry.get('status_code', 0),
                            response_size=entry.get('response_size'),
                            referer=entry.get('referer'),
                            user_agent=entry.get('user_agent'),
                            raw_log=entry.get('raw_log', ''),
                            file_source=entry.get('file_source', '')
                        )
                        nginx_logs.append(nginx_log)
                    except Exception as e:
                        logger.error("NGINX_INSERT_ERROR: Skipping invalid entry - %s", e)
                        continue
                
                if nginx_logs:
                    session.add_all(nginx_logs)
                    session.flush()  # Force assignment of IDs
                    return len(nginx_logs)
                else:
                    return 0
                    
        except Exception as e:
            logger.error("NGINX_BATCH_INSERT_ERROR: Failed to insert nginx logs - %s", e)
            raise
    
    def get_preview(self, limit: int = 10) -> List[Dict]:
        """
        AI: Get a preview of nginx log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of dictionaries containing nginx log data
        """
        try:
            with self.get_session() as session:
                logs = session.query(NginxLog).order_by(NginxLog.id.desc()).limit(limit).all()
                
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
                        'referer': log.referer,
                        'user_agent': log.user_agent,
                        'file_source': log.file_source,
                        'created_at': log.created_at.isoformat() if log.created_at else None
                    })
                
                return result
                
        except Exception as e:
            logger.error("NGINX_PREVIEW_ERROR: Failed to get nginx preview - %s", e)
            return []
    
    def get_top_paths(self, limit: int = 10) -> List[Dict[str, Any]]:
        """AI: Get most frequently accessed paths from nginx logs."""
        try:
            with self.get_session() as session:
                query = """
                SELECT path, COUNT(*) as hits
                FROM nginx_logs 
                GROUP BY path 
                ORDER BY hits DESC 
                LIMIT :limit
                """
                result = session.execute(query, {'limit': limit})
                return [{'path': row[0], 'hits': row[1]} for row in result.fetchall()]
        except Exception as e:
            logger.error("NGINX_TOP_PATHS_ERROR: Failed to get top paths - %s", e)
            return []
    
    def get_status_code_distribution(self) -> List[Dict[str, Any]]:
        """AI: Get distribution of HTTP status codes from nginx logs."""
        try:
            with self.get_session() as session:
                query = """
                SELECT status_code, COUNT(*) as count
                FROM nginx_logs 
                GROUP BY status_code 
                ORDER BY count DESC
                """
                result = session.execute(query)
                return [{'status_code': row[0], 'count': row[1]} for row in result.fetchall()]
        except Exception as e:
            logger.error("NGINX_STATUS_DIST_ERROR: Failed to get status distribution - %s", e)
            return []
    
    def get_logs_by_timerange(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """AI: Get nginx logs within a specific time range."""
        try:
            with self.get_session() as session:
                logs = session.query(NginxLog).filter(
                    NginxLog.timestamp >= start_time,
                    NginxLog.timestamp <= end_time
                ).order_by(NginxLog.timestamp.desc()).limit(limit).all()
                
                result = []
                for log in logs:
                    result.append({
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                        'method': log.method,
                        'path': log.path,
                        'status_code': log.status_code,
                        'ip_address': log.ip_address,
                        'user_agent': log.user_agent
                    })
                
                return result
                
        except Exception as e:
            logger.error("NGINX_TIMERANGE_ERROR: Failed to get logs by timerange - %s", e)
            return []
