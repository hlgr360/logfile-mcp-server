"""
AI: Main application entry point with CLI interface.

Implements Phase 1-3 requirements:
- CLI argument parsing with Click
-     Examples:
        # Basic data analysis mode
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx
        
        # Process logs and start web server
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx --process-logs
        
        # Enable MCP server for external tool integration
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx --enable-mcp-server
        
        # Full stack: process logs, start web server, and enable MCP
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx \\
                 --process-logs --enable-mcp-server
        
        # MCP stdio mode for VS Code integration
        logminer --db-name analysis.db --mcp-stdio

- Configuration validation and loading
- Database operations
- Log processing orchestration
- Web interface with FastAPI
"""

import sys
from pathlib import Path
import threading
import time

import click
import uvicorn

from .config import Settings, load_settings, validate_configuration
from .database.connection import DatabaseConnection
from .database.operations import DatabaseOperations
from .processing import LogProcessingOrchestrator
from .utils.logger import logger
from .web.routes import create_web_app


@click.command()
@click.option(
    '--nexus-dir',
    required=False,
    help='Path to directory containing Nexus logs (required for --process-logs)'
)
@click.option(
    '--nginx-dir', 
    required=False,
    help='Path to directory containing nginx logs (required for --process-logs)'
)
@click.option(
    '--db-name',
    default='log_analysis.db',
    help='SQLite database filename (default: log_analysis.db)'
)
@click.option(
    '--nexus-pattern',
    default='request*.log*,nexus_logs_*.tar,nexus_logs_*.tar.gz',
    help='Comma-separated patterns for Nexus log files'
)
@click.option(
    '--nginx-pattern',
    default='access.log*',
    help='Comma-separated patterns for nginx log files'
)
@click.option(
    '--enable-mcp-server',
    is_flag=True,
    default=False,
    help='Enable MCP server for LLM integration'
)
@click.option(
    '--mcp-stdio',
    is_flag=True,
    default=False,
    help='Run MCP server in stdio mode for VS Code Copilot (overrides other options)'
)
@click.option(
    '--mcp-port',
    default=8001,
    type=int,
    help='MCP server port (default: 8001)'
)
@click.option(
    '--web-port',
    default=8000,
    type=int,
    help='Web server port (default: 8000)'
)
@click.option(
    '--chunk-size',
    default=1000,
    type=int,
    help='Number of lines to read per chunk during log parsing (default: 1000)'
)
@click.option(
    '--line-buffer-size',
    default=1000,
    type=int,
    help='Line processing batch size (default: 1000)'
)
@click.option(
    '--max-archive-depth',
    default=3,
    type=int,
    help='Maximum nested archive depth (default: 3)'
)
@click.option(
    '--process-logs',
    is_flag=True,
    default=False,
    help='Process all discovered log files and populate database'
)
@click.option(
    '--process-only',
    is_flag=True,
    default=False,
    help='Process logs and exit'
)
def cli(
    nexus_dir: str,
    nginx_dir: str,
    db_name: str,
    nexus_pattern: str,
    nginx_pattern: str,
    enable_mcp_server: bool,
    mcp_stdio: bool,
    mcp_port: int,
    web_port: int,
    chunk_size: int,
    line_buffer_size: int,
    max_archive_depth: int,
    process_logs: bool,
    process_only: bool
) -> None:
    """
    AI: Log Analysis Application - Parse and analyze Nexus and nginx access logs.
    
    This application processes log files from configured directories, parses them
    into a SQLite database, and provides both web and MCP interfaces for analysis.
    
    \b
    Examples:
        # Basic usage
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx
        
        # Process logs and populate database
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx --process-logs
        
        # With MCP server enabled
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx --enable-mcp-server
        
        # Custom patterns and ports
        logminer --nexus-dir /logs/nexus --nginx-dir /logs/nginx \\
                   --nexus-pattern "*.log,*.tar.gz" --web-port 9000
    """
    try:
        # Phase 1: Configuration Loading and Validation
        logger.info("=== Log Analysis Application Startup ===")
        logger.info("Phase 1: Loading and validating configuration...")

        # Validate required directories for log processing
        if process_logs and (not nexus_dir or not nginx_dir):
            logger.error("❌ Error: --nexus-dir and --nginx-dir are required when using --process-logs")
            sys.exit(1)
        
        # For MCP-only mode, use dummy directories if not provided
        if mcp_stdio and not nexus_dir:
            nexus_dir = "/tmp"
        if mcp_stdio and not nginx_dir:
            nginx_dir = "/tmp"
        
        settings = load_settings(
            nexus_dir=nexus_dir,
            nginx_dir=nginx_dir,
            db_name=db_name,
            nexus_pattern=nexus_pattern,
            nginx_pattern=nginx_pattern,
            enable_mcp_server=enable_mcp_server,
            mcp_port=mcp_port,
            web_port=web_port,
            chunk_size=chunk_size,
            line_buffer_size=line_buffer_size,
            max_archive_depth=max_archive_depth,
            process_only=process_only
        )
        
        # Additional configuration validation
        validate_configuration(settings)
        logger.info("✓ Configuration validation successful")

        # Handle stdio mode for VS Code Copilot integration
        if mcp_stdio:
            logger.info("🚀 Starting MCP server in stdio mode for VS Code Copilot...")

            # Check if database exists
            if not Path(settings.db_name).exists():
                logger.error("❌ Database not found: %s", settings.db_name)
                logger.info("💡 Run with --process-logs first to create and populate the database")
                sys.exit(1)

            # Phase 2: Database Setup for stdio mode
            logger.info("📁 Setting up database connection...")
            db_connection = DatabaseConnection(settings.db_name, fresh_start=False)
            db_ops = DatabaseOperations(db_connection)
            logger.info("📁 Using database: %s", settings.db_name)

            # Import and start stdio server
            from .mcp.server import create_stdio_server
            logger.info("🔌 Starting MCP server for VS Code Copilot...")
            stdio_server = create_stdio_server(db_ops)
            stdio_server.start()
            return  # Exit after stdio server finishes
        
        # Phase 2: Database Setup
        logger.info("\n\nPhase 2: Setting up database...")
        db_connection = DatabaseConnection(settings.db_name)
        db_ops = DatabaseOperations(db_connection)
        logger.info("✓ Database initialized successfully")

        # Phase 3: Application Ready State
        logger.info("\n\nPhase 3: Application startup complete")
        logger.info("✓ Ready to process logs from:")
        logger.info("  - Nexus: %s (patterns: %s)", settings.nexus_dir, settings.nexus_patterns)
        logger.info("  - nginx: %s (patterns: %s)", settings.nginx_dir, settings.nginx_patterns)
        logger.info("✓ Database: %s", settings.db_name)
        logger.info("✓ Web server will start on port %d", settings.web_port)

        if settings.enable_mcp_server:
            logger.info("✓ MCP server will start on port %d", settings.mcp_port)

        # Phase 4: Server Startup (placeholder for future phases)
        logger.info("\n\n=== Phase 1 Complete: Foundation Ready ===")

        # Phase 2: Log Processing (if requested)
        if process_logs:
            logger.info("\n\n=== Starting Phase 2: Log Processing ===")
            orchestrator = LogProcessingOrchestrator(settings, db_ops)
            processing_stats = orchestrator.process_all_logs()
            logger.info("=== Phase 2 Complete: Log Processing Finished ===")
        else:
            logger.info("Skipping log processing (use --process-logs to process logs)")

        # Check if we should exit after processing
        if settings.process_only or process_only:
            logger.info("\n--process-only flag specified, exiting after log processing...")
            db_ops.close()
            return

        # Phase 3: Web Server Startup
        logger.info("\n\n=== Starting Phase 3: Web Interface ===")
        start_web_server(settings, db_ops)

        if settings.enable_mcp_server:
            logger.info("\n\n=== Starting Phase 4: MCP Server ===")
            start_mcp_server(settings, db_ops)

        # Keep application running for testing
        logger.info("\n✓ Application running:")
        logger.info("  - Web interface: http://localhost:%d", settings.web_port)
        if settings.enable_mcp_server:
            logger.info("  - MCP server: http://localhost:%d", settings.mcp_port)
        logger.info("\nPress Ctrl+C to exit...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            db_ops.close()

    except Exception as e:
        logger.error("ERROR: Application startup failed: %s", e)
        sys.exit(1)


def start_web_server(settings: Settings, db_ops: DatabaseOperations) -> None:
    """
    AI: Start FastAPI web server with background thread.

    Args:
        settings: Application configuration
        db_ops: Database operations instance
    """
    try:
        logger.info("Starting web server on port %d...", settings.web_port)

        # Create FastAPI app
        app = create_web_app(settings)

        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=settings.web_port,
            log_level="info",
            access_log=True
        )

        # Start server in background thread
        server = uvicorn.Server(config)

        def run_server():
            import asyncio
            asyncio.run(server.serve())

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(2)
        logger.info("✓ Web server started on http://localhost:%d", settings.web_port)

    except Exception as e:
        logger.error("ERROR: Failed to start web server: %s", e)
        raise


def start_mcp_server(settings: Settings, db_ops: DatabaseOperations) -> None:
    """
    AI: Start MCP server for LLM integration (Phase 4 implementation).

    Args:
        settings: Application configuration
        db_ops: Database operations instance
    """
    try:
        logger.info("Starting MCP server on port %d...", settings.mcp_port)

        # Import MCP server (avoiding circular imports)
        from .mcp.server import create_network_server

        # Create and start MCP server in network mode
        mcp_server = create_network_server(
            db_ops=db_ops,
            host="0.0.0.0",
            port=settings.mcp_port
        )

        mcp_server.start()

        # Store server reference for cleanup (in real implementation)
        # This would be managed by the application lifecycle
        settings._mcp_server = mcp_server

        logger.info("✓ MCP server started with tools: %s", mcp_server.get_status()['tools'])

    except Exception as e:
        logger.error("ERROR: Failed to start MCP server: %s", e)
        raise


if __name__ == "__main__":
    cli()
