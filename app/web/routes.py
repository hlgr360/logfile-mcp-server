"""
AI: FastAPI web routes for log analysis application.

Provides endpoints for:
- Serving HTML interface
- Table data previews
- SQL query execution
- Database schema information
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from ..database.operations import DatabaseOperations
from ..database.connection import DatabaseConnection
from ..config import Settings

logger = logging.getLogger(__name__)

# Get paths relative to this file
CURRENT_DIR = Path(__file__).parent
TEMPLATE_DIR = CURRENT_DIR / "templates"
STATIC_DIR = CURRENT_DIR.parent / "static"

# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    """AI: Request model for SQL query execution."""
    query: str = Field(..., description="SQL SELECT query to execute")
    limit: Optional[int] = Field(100, description="Maximum rows to return", le=1000)


class QueryResponse(BaseModel):
    """AI: Response model for query results."""
    results: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time: float


class TableInfo(BaseModel):
    """AI: Response model for database table information."""
    table_name: str
    columns: List[Dict[str, str]]
    row_count: int


class SchemaResponse(BaseModel):
    """AI: Response model for database schema information."""
    tables: List[TableInfo]


def create_web_app(settings: Settings) -> FastAPI:
    """
    AI: Create FastAPI web application with all routes and middleware.

    Args:
        settings: Application configuration settings

    Returns:
        Configured FastAPI application instance
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        AI: Lifespan context manager for database connection management.

        Ensures database connections are properly closed when app shuts down,
        preventing ResourceWarnings per best-practices/PYTHON.md.
        """
        # Startup: Create database connection
        db_connection = DatabaseConnection(settings.db_name, fresh_start=False)
        db_operations = DatabaseOperations(db_connection)
        app.state.db_operations = db_operations
        app.state.db_connection = db_connection

        yield  # Application runs

        # Shutdown: Close database connection
        db_connection.close()

    app = FastAPI(
        title="Log Analysis Application",
        description="Nexus and nginx log correlation and analysis",
        version="1.0.0",
        lifespan=lifespan
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Setup templates
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    # Dependency injection for database
    def get_database(request: Request) -> DatabaseOperations:
        """AI: Dependency injection for database connections."""
        return request.app.state.db_operations
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_index(request: Request):
        """
        AI: Serve main HTML page.
        
        Returns rendered template with request context for static file URLs.
        """
        try:
            return templates.TemplateResponse(request, "index.html")
        except Exception as e:
            logger.error(f"Failed to render index template: {e}")
            raise HTTPException(status_code=500, detail="Failed to load page")
    
    @app.get("/api/nginx-preview")
    async def get_nginx_preview(
        limit: int = 10,
        db: DatabaseOperations = Depends(get_database)
    ) -> List[Dict[str, Any]]:
        """
        AI: Get preview of nginx log entries.
        
        Returns first 10 nginx log entries for table preview display.
        """
        try:
            results = db.get_nginx_preview(limit)
            logger.info(f"Retrieved {len(results)} nginx preview entries")
            return results
        except Exception as e:
            logger.error(f"Failed to get nginx preview: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @app.get("/api/nexus-preview")
    async def get_nexus_preview(
        limit: int = 10,
        db: DatabaseOperations = Depends(get_database)
    ) -> List[Dict[str, Any]]:
        """
        AI: Get preview of nexus log entries.
        
        Returns first 10 nexus log entries for table preview display.
        """
        try:
            results = db.get_nexus_preview(limit)
            logger.info(f"Retrieved {len(results)} nexus preview entries")
            return results
        except Exception as e:
            logger.error(f"Failed to get nexus preview: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @app.post("/api/execute-query")
    async def execute_query(
        query_request: QueryRequest,
        db: DatabaseOperations = Depends(get_database)
    ) -> QueryResponse:
        """
        AI: Execute SQL query with security validation.
        
        Only SELECT statements allowed for security.
        Results limited to prevent memory issues.
        """
        import time
        start_time = time.time()
        
        try:
            # Validate query is SELECT only
            query_stripped = query_request.query.strip().upper()
            if not query_stripped.startswith("SELECT"):
                raise HTTPException(
                    status_code=400,
                    detail="Only SELECT queries are allowed"
                )
            
            # Additional security checks
            forbidden_keywords = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "CREATE"]
            for keyword in forbidden_keywords:
                if keyword in query_stripped:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Query contains forbidden keyword: {keyword}"
                    )
            
            # Execute query with limit
            limit = min(query_request.limit or 100, 1000)  # Enforce max limit
            results = db.execute_query(query_request.query, limit=limit)
            
            execution_time = time.time() - start_time
            
            # Extract column names from first row
            columns = list(results[0].keys()) if results else []
            
            logger.info(f"Executed query returning {len(results)} rows in {execution_time:.3f}s")
            
            return QueryResponse(
                results=results,
                row_count=len(results),
                columns=columns,
                execution_time=execution_time
            )
            
        except HTTPException:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
    
    @app.get("/api/table-info")
    async def get_table_info(
        db: DatabaseOperations = Depends(get_database)
    ) -> SchemaResponse:
        """
        AI: Get database schema information.
        
        Returns table schemas and row counts for database exploration.
        """
        try:
            tables = []
            
            # Get nginx table info
            nginx_schema = db.get_table_schema("nginx_logs")
            nginx_count = db.get_table_row_count("nginx_logs")
            tables.append(TableInfo(
                table_name="nginx_logs",
                columns=nginx_schema,
                row_count=nginx_count
            ))
            
            # Get nexus table info
            nexus_schema = db.get_table_schema("nexus_logs")
            nexus_count = db.get_table_row_count("nexus_logs")
            tables.append(TableInfo(
                table_name="nexus_logs",
                columns=nexus_schema,
                row_count=nexus_count
            ))
            
            logger.info(f"Retrieved schema info for {len(tables)} tables")
            return SchemaResponse(tables=tables)
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @app.get("/health")
    async def health_check(
        db: DatabaseOperations = Depends(get_database)
    ) -> Dict[str, Any]:
        """
        AI: Health check endpoint for monitoring.
        
        Returns application status and basic database statistics.
        """
        try:
            nginx_count = db.get_table_row_count("nginx_logs")
            nexus_count = db.get_table_row_count("nexus_logs")
            
            return {
                "status": "healthy",
                "database": "connected",
                "nginx_logs_count": nginx_count,
                "nexus_logs_count": nexus_count,
                "total_entries": nginx_count + nexus_count
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return app
