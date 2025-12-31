/**
 * AI: JavaScript functionality for log analysis web interface.
 * 
 * Provides:
 * - Dynamic table loading and refreshing
 * - SQL query execution with error handling
 * - Database schema inspection
 * - Example query insertion
 * - Application health checking
 */

// API endpoints configuration
const API_BASE = '/api';
const ENDPOINTS = {
    nginxPreview: `${API_BASE}/nginx-preview`,
    nexusPreview: `${API_BASE}/nexus-preview`,
    executeQuery: `${API_BASE}/execute-query`,
    tableInfo: `${API_BASE}/table-info`,
    health: '/health'
};

// DOM elements cache
const elements = {
    nginxTable: () => document.getElementById('nginx-table-body'),
    nexusTable: () => document.getElementById('nexus-table-body'),
    nginxStatus: () => document.getElementById('nginx-status'),
    nexusStatus: () => document.getElementById('nexus-status'),
    sqlQuery: () => document.getElementById('sql-query'),
    queryResults: () => document.getElementById('query-results'),
    queryResultsSection: () => document.getElementById('query-results-section'),
    errorMessages: () => document.getElementById('error-messages'),
    queryStatus: () => document.getElementById('query-status'),
    resultsCount: () => document.getElementById('results-count'),
    executionTime: () => document.getElementById('execution-time'),
    schemaDetails: () => document.getElementById('schema-details'),
    healthResults: () => document.getElementById('health-results')
};

/**
 * AI: Initialize application when DOM is loaded.
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadInitialData();
});

/**
 * AI: Initialize application state and UI.
 */
function initializeApp() {
    console.log('Log Analysis Application initialized');
    hideElement(elements.queryResultsSection());
    hideElement(elements.errorMessages());
}

/**
 * AI: Setup all event listeners for interactive elements.
 */
function setupEventListeners() {
    // Table refresh buttons
    document.getElementById('refresh-nginx')?.addEventListener('click', () => loadNginxPreview());
    document.getElementById('refresh-nexus')?.addEventListener('click', () => loadNexusPreview());
    
    // Query execution
    document.getElementById('execute-query')?.addEventListener('click', executeQuery);
    document.getElementById('clear-query')?.addEventListener('click', clearQuery);
    
    // Example queries
    document.querySelectorAll('.example-query').forEach(button => {
        button.addEventListener('click', (e) => {
            const query = e.target.getAttribute('data-query');
            elements.sqlQuery().value = query;
        });
    });
    
    // Schema loading
    document.getElementById('load-schema')?.addEventListener('click', loadSchemaInfo);
    
    // Health check
    document.getElementById('check-health')?.addEventListener('click', checkHealth);
    
    // Keyboard shortcuts
    elements.sqlQuery()?.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            executeQuery();
        }
    });
}

/**
 * AI: Load initial data when page loads.
 */
function loadInitialData() {
    loadNginxPreview();
    loadNexusPreview();
}

/**
 * AI: Load nginx log preview data.
 */
async function loadNginxPreview() {
    const statusElement = elements.nginxStatus();
    const tableBody = elements.nginxTable();
    
    try {
        statusElement.textContent = 'Loading...';
        statusElement.className = 'status-text loading';
        
        const response = await fetch(ENDPOINTS.nginxPreview);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        renderNginxTable(data);
        
        statusElement.textContent = `Loaded ${data.length} entries`;
        statusElement.className = 'status-text';
        
    } catch (error) {
        console.error('Failed to load nginx preview:', error);
        statusElement.textContent = `Error: ${error.message}`;
        statusElement.className = 'status-text error';
        
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="error-message">
                    Failed to load nginx data: ${error.message}
                </td>
            </tr>
        `;
    }
}

/**
 * AI: Load nexus log preview data.
 */
async function loadNexusPreview() {
    const statusElement = elements.nexusStatus();
    const tableBody = elements.nexusTable();
    
    try {
        statusElement.textContent = 'Loading...';
        statusElement.className = 'status-text loading';
        
        const response = await fetch(ENDPOINTS.nexusPreview);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        renderNexusTable(data);
        
        statusElement.textContent = `Loaded ${data.length} entries`;
        statusElement.className = 'status-text';
        
    } catch (error) {
        console.error('Failed to load nexus preview:', error);
        statusElement.textContent = `Error: ${error.message}`;
        statusElement.className = 'status-text error';
        
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="error-message">
                    Failed to load nexus data: ${error.message}
                </td>
            </tr>
        `;
    }
}

/**
 * AI: Render nginx table data.
 */
function renderNginxTable(data) {
    const tableBody = elements.nginxTable();
    
    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="no-data">No nginx log data available</td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = data.map(row => `
        <tr>
            <td title="${escapeHtml(row.ip_address || '')}">${escapeHtml(row.ip_address || '')}</td>
            <td title="${escapeHtml(row.timestamp || '')}">${formatTimestamp(row.timestamp)}</td>
            <td title="${escapeHtml(row.method || '')}">${escapeHtml(row.method || '')}</td>
            <td title="${escapeHtml(row.path || '')}">${truncateText(row.path || '', 50)}</td>
            <td title="${escapeHtml(row.status_code || '')}" class="status-${getStatusClass(row.status_code)}">${escapeHtml(row.status_code || '')}</td>
            <td title="${escapeHtml(row.response_size || '')}">${formatSize(row.response_size)}</td>
            <td title="${escapeHtml(row.user_agent || '')}">${truncateText(row.user_agent || '', 30)}</td>
            <td title="${escapeHtml(row.file_source || '')}">${truncateText(row.file_source || '', 20)}</td>
        </tr>
    `).join('');
}

/**
 * AI: Render nexus table data.
 */
function renderNexusTable(data) {
    const tableBody = elements.nexusTable();
    
    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="no-data">No nexus log data available</td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = data.map(row => `
        <tr>
            <td title="${escapeHtml(row.ip_address || '')}">${escapeHtml(row.ip_address || '')}</td>
            <td title="${escapeHtml(row.timestamp || '')}">${formatTimestamp(row.timestamp)}</td>
            <td title="${escapeHtml(row.method || '')}">${escapeHtml(row.method || '')}</td>
            <td title="${escapeHtml(row.path || '')}">${truncateText(row.path || '', 50)}</td>
            <td title="${escapeHtml(row.status_code || '')}" class="status-${getStatusClass(row.status_code)}">${escapeHtml(row.status_code || '')}</td>
            <td title="${escapeHtml(row.response_size_1 || '')}">${formatSize(row.response_size_1)}</td>
            <td title="${escapeHtml(row.response_size_2 || '')}">${formatSize(row.response_size_2)}</td>
            <td title="${escapeHtml(row.thread_info || '')}">${truncateText(row.thread_info || '', 15)}</td>
            <td title="${escapeHtml(row.file_source || '')}">${truncateText(row.file_source || '', 20)}</td>
        </tr>
    `).join('');
}

/**
 * AI: Execute SQL query with error handling and result display.
 */
async function executeQuery() {
    const query = elements.sqlQuery().value.trim();
    const statusElement = elements.queryStatus();
    
    if (!query) {
        showError('Please enter a SQL query');
        return;
    }
    
    try {
        statusElement.textContent = 'Executing query...';
        statusElement.className = 'status-text loading';
        
        hideElement(elements.errorMessages());
        hideElement(elements.queryResultsSection());
        
        const response = await fetch(ENDPOINTS.executeQuery, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || `HTTP ${response.status}`);
        }
        
        renderQueryResults(result);
        statusElement.textContent = 'Query executed successfully';
        statusElement.className = 'status-text';
        
    } catch (error) {
        console.error('Query execution failed:', error);
        showError(`Query failed: ${error.message}`);
        statusElement.textContent = 'Query failed';
        statusElement.className = 'status-text error';
    }
}

/**
 * AI: Render query results in formatted table.
 */
function renderQueryResults(result) {
    const resultsSection = elements.queryResultsSection();
    const resultsDiv = elements.queryResults();
    const countElement = elements.resultsCount();
    const timeElement = elements.executionTime();
    
    // Update result information
    countElement.textContent = `${result.row_count} rows returned`;
    timeElement.textContent = `Executed in ${result.execution_time.toFixed(3)}s`;
    
    if (!result.results || result.results.length === 0) {
        resultsDiv.innerHTML = '<p class="no-data">No results returned</p>';
        showElement(resultsSection);
        return;
    }
    
    // Build results table
    const table = document.createElement('table');
    table.className = 'data-table';
    
    // Table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    result.columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Table body
    const tbody = document.createElement('tbody');
    result.results.forEach(row => {
        const tr = document.createElement('tr');
        result.columns.forEach(column => {
            const td = document.createElement('td');
            const value = row[column];
            td.textContent = formatCellValue(value);
            td.title = String(value || '');
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    resultsDiv.innerHTML = '';
    resultsDiv.appendChild(table);
    showElement(resultsSection);
}

/**
 * AI: Clear query input and results.
 */
function clearQuery() {
    elements.sqlQuery().value = '';
    hideElement(elements.queryResultsSection());
    hideElement(elements.errorMessages());
    elements.queryStatus().textContent = '';
}

/**
 * AI: Load and display database schema information.
 */
async function loadSchemaInfo() {
    const detailsElement = elements.schemaDetails();
    
    try {
        detailsElement.innerHTML = '<p class="loading">Loading schema information...</p>';
        
        const response = await fetch(ENDPOINTS.tableInfo);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const schemaInfo = await response.json();
        renderSchemaInfo(schemaInfo);
        
    } catch (error) {
        console.error('Failed to load schema:', error);
        detailsElement.innerHTML = `<p class="error-message">Failed to load schema: ${error.message}</p>`;
    }
}

/**
 * AI: Render database schema information.
 */
function renderSchemaInfo(schemaInfo) {
    const detailsElement = elements.schemaDetails();
    
    const html = schemaInfo.tables.map(table => `
        <div class="table-schema">
            <h4>${table.table_name}</h4>
            <div class="schema-stats">
                <div class="stat-item">
                    <div class="stat-value">${table.row_count}</div>
                    <div class="stat-label">Total Rows</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${table.columns.length}</div>
                    <div class="stat-label">Columns</div>
                </div>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Column Name</th>
                            <th>Data Type</th>
                            <th>Nullable</th>
                            <th>Primary Key</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${table.columns.map(col => `
                            <tr>
                                <td><strong>${col.name || col.column_name}</strong></td>
                                <td>${col.type || col.data_type}</td>
                                <td>${col.nullable ? 'Yes' : 'No'}</td>
                                <td>${col.primary_key ? 'Yes' : 'No'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `).join('');
    
    detailsElement.innerHTML = html;
}

/**
 * AI: Check application health status.
 */
async function checkHealth() {
    const resultsElement = elements.healthResults();
    
    try {
        resultsElement.innerHTML = 'Checking application health...';
        
        const response = await fetch(ENDPOINTS.health);
        const healthData = await response.json();
        
        const statusClass = healthData.status === 'healthy' ? 'success' : 'error';
        resultsElement.innerHTML = `
            <div class="health-${statusClass}">
                <strong>Status:</strong> ${healthData.status}<br>
                <strong>Database:</strong> ${healthData.database || 'Unknown'}<br>
                <strong>Nginx Logs:</strong> ${healthData.nginx_logs_count || 0}<br>
                <strong>Nexus Logs:</strong> ${healthData.nexus_logs_count || 0}<br>
                <strong>Total Entries:</strong> ${healthData.total_entries || 0}
                ${healthData.error ? `<br><strong>Error:</strong> ${healthData.error}` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('Health check failed:', error);
        resultsElement.innerHTML = `<div class="health-error">Health check failed: ${error.message}</div>`;
    }
}

/**
 * AI: Show error message to user.
 */
function showError(message) {
    const errorElement = elements.errorMessages();
    errorElement.innerHTML = `
        <h4>Error</h4>
        <p>${escapeHtml(message)}</p>
    `;
    showElement(errorElement);
}

/**
 * AI: Utility functions for DOM manipulation and formatting.
 */

function showElement(element) {
    if (element) element.style.display = 'block';
}

function hideElement(element) {
    if (element) element.style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    try {
        return new Date(timestamp).toLocaleString();
    } catch {
        return timestamp;
    }
}

function formatSize(size) {
    if (!size || size === '-') return '-';
    const num = parseInt(size);
    if (isNaN(num)) return size;
    
    if (num < 1024) return `${num}B`;
    if (num < 1048576) return `${(num / 1024).toFixed(1)}KB`;
    return `${(num / 1048576).toFixed(1)}MB`;
}

function formatCellValue(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'number') return value.toLocaleString();
    return String(value);
}

function getStatusClass(statusCode) {
    if (!statusCode) return 'unknown';
    const code = parseInt(statusCode);
    if (code >= 200 && code < 300) return 'success';
    if (code >= 300 && code < 400) return 'redirect';
    if (code >= 400 && code < 500) return 'client-error';
    if (code >= 500) return 'server-error';
    return 'unknown';
}
