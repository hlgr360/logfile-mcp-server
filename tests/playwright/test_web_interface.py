"""
AI: Playwright E2E tests for the log analysis web interface.

Tests comprehensive functionality including:
- Homepage loading and navigation
- Table previews for nginx and nexus logs
- SQL query execution with sample data validation
- Database schema information display
- Application health checks
"""

import pytest
from playwright.sync_api import Page, expect


class TestWebInterface:
    """AI: Main test class for web interface E2E testing."""

    def test_homepage_loads_successfully(self, page: Page, web_server):
        """AI: Test that the homepage loads correctly with proper title and main elements."""
        page.goto(web_server)
        
        # Check page title
        expect(page).to_have_title("Log Analysis Application")
        
        # Check main heading
        heading = page.locator("h1")
        expect(heading).to_contain_text("Log Analysis Application")
        
        # Check that main navigation sections are present
        expect(page.locator("#table-previews")).to_be_visible()
        expect(page.locator("#query-section")).to_be_visible()
        expect(page.locator("#schema-info")).to_be_visible()
        
        print("✓ Homepage loaded successfully with all main sections")

    def test_nginx_table_preview_displays_data(self, page: Page, web_server):
        """AI: Test that nginx table preview loads and displays sample data."""
        page.goto(web_server)
        
        # Wait for nginx preview section to be visible
        nginx_section = page.locator("#nginx-preview-section")
        expect(nginx_section).to_be_visible()
        
        # Wait for table to load (check if data is present)
        nginx_table = page.locator("#nginx-table")
        expect(nginx_table).to_be_visible()
        
        # Check table headers are present 
        headers = page.locator("#nginx-table thead th")
        expect(headers).to_have_count(8)  # Based on template: IP, Timestamp, Method, Path, Status, Size, User Agent, Source
        
        # Wait for table body to have data
        page.wait_for_timeout(2000)  # Allow time for AJAX loading
        
        # Check that table body has rows (sample data should be loaded)
        table_rows = page.locator("#nginx-table-body tr")
        expect(table_rows.first).to_be_visible()  # At least one row should be visible
        
        print("✓ nginx table preview displays data correctly")

    def test_nexus_table_preview_displays_data(self, page: Page, web_server):
        """AI: Test that nexus table preview loads and displays sample data."""
        page.goto(web_server)
        
        # Wait for nexus preview section to be visible
        nexus_section = page.locator("#nexus-preview-section") 
        expect(nexus_section).to_be_visible()
        
        # Wait for table to load (check if data is present)
        nexus_table = page.locator("#nexus-table")
        expect(nexus_table).to_be_visible()
        
        # Check table headers are present
        headers = page.locator("#nexus-table thead th")
        expect(headers).to_have_count(9)  # Based on template: IP, Timestamp, Method, Path, Status, Size1, Size2, Thread, Source
        
        # Wait for table body to have data
        page.wait_for_timeout(2000)  # Allow time for AJAX loading
        
        # Check that table body has rows (sample data should be loaded)
        table_rows = page.locator("#nexus-table-body tr")
        expect(table_rows.first).to_be_visible()  # At least one row should be visible
        
        print("✓ nexus table preview displays data correctly")

    def test_sql_query_section_is_functional(self, page: Page, web_server):
        """AI: Test that SQL query section exists and basic elements are functional."""
        page.goto(web_server)
        
        # Check SQL query section is visible
        sql_section = page.locator("#query-section")
        expect(sql_section).to_be_visible()
        
        # Check that query textarea is present and editable
        query_textarea = page.locator("#sql-query")
        expect(query_textarea).to_be_visible()
        expect(query_textarea).to_be_editable()
        
        # Check execute button is present
        execute_button = page.locator("#execute-query")
        expect(execute_button).to_be_visible()
        expect(execute_button).to_be_enabled()
        
        # Check that example query buttons are present
        example_buttons = page.locator(".example-query")
        expect(example_buttons.first).to_be_visible()  # At least one example button should be visible
        
        print("✓ SQL query section is functional")

    def test_nginx_logs_count_query(self, page: Page, web_server):
        """AI: Test executing a count query for nginx logs."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter count query for nginx logs
        count_query = "SELECT COUNT(*) as nginx_count FROM nginx_logs"
        query_textarea.fill(count_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for results to appear
        page.wait_for_timeout(2000)
        
        # Check that results section becomes visible
        results_section = page.locator("#query-results-section")
        expect(results_section).to_be_visible()
        
        # Check that results area contains the count
        results_area = page.locator("#query-results")
        expect(results_area).to_be_visible()
        
        # Verify that results contain nginx_count (the column name)
        expect(results_area).to_contain_text("nginx_count")
        
        # Verify that we get a numeric result (5 logs from shared database factory)
        expect(results_area).to_contain_text("5")  # Expected count from shared test database
        
        print("✓ nginx logs count query executed successfully")

    def test_nexus_logs_count_query(self, page: Page, web_server):
        """AI: Test executing a count query for nexus logs."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter count query for nexus logs
        count_query = "SELECT COUNT(*) as nexus_count FROM nexus_logs"
        query_textarea.fill(count_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for results to appear
        page.wait_for_timeout(2000)
        
        # Check that results section becomes visible
        results_section = page.locator("#query-results-section")
        expect(results_section).to_be_visible()
        
        # Check that results area contains the count
        results_area = page.locator("#query-results")
        expect(results_area).to_be_visible()
        
        # Verify that results contain nexus_count (the column name)
        expect(results_area).to_contain_text("nexus_count")
        
        # Verify count from shared test database (3 logs from factory)
        expect(results_area).to_contain_text("3")  # Expected count from shared test database
        
        print("✓ nexus logs count query executed successfully")

    def test_combined_logs_count_query(self, page: Page, web_server):
        """AI: Test executing a combined count query across both log tables."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter combined count query
        combined_query = """
        SELECT 
            (SELECT COUNT(*) FROM nginx_logs) as nginx_count,
            (SELECT COUNT(*) FROM nexus_logs) as nexus_count
        """
        query_textarea.fill(combined_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for results to appear
        page.wait_for_timeout(2000)
        
        # Check that results section becomes visible
        results_section = page.locator("#query-results-section")
        expect(results_section).to_be_visible()
        
        # Check that results area contains both counts
        results_area = page.locator("#query-results")
        expect(results_area).to_be_visible()
        expect(results_area).to_contain_text("nginx_count")
        expect(results_area).to_contain_text("nexus_count")
        
        print("✓ Combined logs count query executed successfully")

    def test_table_schema_information(self, page: Page, web_server):
        """AI: Test loading database schema information."""
        page.goto(web_server)
        
        # Navigate to schema section
        schema_section = page.locator("#schema-info")
        expect(schema_section).to_be_visible()
        
        # Click load schema button
        load_schema_button = page.locator("#load-schema")
        expect(load_schema_button).to_be_visible()
        load_schema_button.click()
        
        # Wait for schema details to load
        page.wait_for_timeout(2000)
        
        # Check that schema details are now visible
        schema_details = page.locator("#schema-details")
        expect(schema_details).to_be_visible()
        
        print("✓ Database schema information loaded successfully")

    def test_health_check_functionality(self, page: Page, web_server):
        """AI: Test application health check endpoint."""
        page.goto(web_server)
        
        # Find health check button
        health_button = page.locator("#check-health")
        expect(health_button).to_be_visible()
        
        # Click health check button
        health_button.click()
        
        # Wait for health results
        page.wait_for_timeout(2000)
        
        # Check that health results are displayed
        health_results = page.locator("#health-results")
        expect(health_results).to_be_visible()
        
        print("✓ Health check functionality working")

    def test_example_query_buttons_work(self, page: Page, web_server):
        """AI: Test that example query buttons populate the textarea."""
        page.goto(web_server)
        
        # Find first example query button
        first_example = page.locator(".example-query").first
        expect(first_example).to_be_visible()
        
        # Click the example button
        first_example.click()
        
        # Check that query textarea now contains text
        query_textarea = page.locator("#sql-query")
        expect(query_textarea).not_to_be_empty()
        
        print("✓ Example query buttons populate textarea correctly")


class TestWebInterfaceEdgeCases:
    """AI: Test class for edge cases and error handling."""

    def test_invalid_sql_query_shows_error(self, page: Page, web_server):
        """AI: Test that invalid SQL queries show appropriate error messages."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter invalid SQL query
        invalid_query = "INVALID SQL QUERY SYNTAX"
        query_textarea.fill(invalid_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for error to appear
        page.wait_for_timeout(2000)
        
        # Check that error section becomes visible
        error_section = page.locator("#error-messages")
        expect(error_section).to_be_visible()
        
        print("✓ Invalid SQL query shows error message correctly")

    def test_forbidden_sql_operations_blocked(self, page: Page, web_server):
        """AI: Test that non-SELECT SQL operations are blocked."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter forbidden DELETE query
        forbidden_query = "DELETE FROM nginx_logs WHERE id = 1"
        query_textarea.fill(forbidden_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for error to appear
        page.wait_for_timeout(2000)
        
        # Check that error section becomes visible with forbidden operation message
        error_section = page.locator("#error-messages")
        expect(error_section).to_be_visible()
        expect(error_section).to_contain_text("Only SELECT queries are allowed")
        
        print("✓ Forbidden SQL operations correctly blocked")

    def test_large_query_results_handled(self, page: Page, web_server):
        """AI: Test that large query results are handled gracefully."""
        page.goto(web_server)
        
        # Navigate to SQL query section
        query_textarea = page.locator("#sql-query")
        execute_button = page.locator("#execute-query")
        
        # Enter query that might return large results
        large_query = "SELECT * FROM nginx_logs UNION ALL SELECT * FROM nexus_logs"
        query_textarea.fill(large_query)
        
        # Execute the query
        execute_button.click()
        
        # Wait for results to appear (may take longer for large results)
        page.wait_for_timeout(5000)
        
        # Check that either results appear or proper handling occurs
        results_section = page.locator("#query-results-section")
        error_section = page.locator("#error-messages")
        
        # Should either show results or error, but not crash
        has_results = results_section.is_visible()
        has_error = error_section.is_visible()
        assert has_results or has_error, "Query should either show results or error"
        
        print("✓ Large query results handled appropriately")
