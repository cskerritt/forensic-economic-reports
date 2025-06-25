/**
 * Advanced Filtering System
 * 
 * This script provides advanced filtering functionality for tables
 * in the Economic Analysis application.
 */

/**
 * Initialize the advanced filtering system
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with a filterable table
    const filterableTable = document.querySelector('.filterable-table');
    if (!filterableTable) return;
    
    // Create the filter panel
    createFilterPanel(filterableTable);
    
    // Initialize the quick filter
    initializeQuickFilter(filterableTable);
});

/**
 * Create the advanced filter panel
 * @param {HTMLElement} table - The table to filter
 */
function createFilterPanel(table) {
    // Get the table container
    const tableContainer = table.closest('.table-container') || table.parentNode;
    
    // Create the filter panel
    const filterPanel = document.createElement('div');
    filterPanel.className = 'filter-panel mb-4';
    filterPanel.innerHTML = `
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="fas fa-filter me-2"></i> Advanced Filters
                </h5>
                <button type="button" class="btn btn-sm btn-outline-light" id="toggle-filter-panel">
                    <i class="fas fa-chevron-up"></i>
                </button>
            </div>
            <div class="card-body filter-panel-body">
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label for="filter-name" class="form-label">Name</label>
                        <input type="text" class="form-control" id="filter-name" placeholder="Search by name">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="filter-status" class="form-label">Status</label>
                        <select class="form-select" id="filter-status">
                            <option value="">All Statuses</option>
                            <option value="completed">Completed</option>
                            <option value="in-progress">In Progress</option>
                        </select>
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="filter-date-range" class="form-label">Date Range</label>
                        <select class="form-select" id="filter-date-range">
                            <option value="">All Time</option>
                            <option value="today">Today</option>
                            <option value="this-week">This Week</option>
                            <option value="this-month">This Month</option>
                            <option value="this-year">This Year</option>
                            <option value="custom">Custom Range</option>
                        </select>
                    </div>
                </div>
                
                <div class="row custom-date-range d-none">
                    <div class="col-md-6 mb-3">
                        <label for="filter-date-start" class="form-label">Start Date</label>
                        <input type="date" class="form-control" id="filter-date-start">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label for="filter-date-end" class="form-label">End Date</label>
                        <input type="date" class="form-control" id="filter-date-end">
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-12">
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-primary" id="apply-filters">
                                <i class="fas fa-search me-2"></i> Apply Filters
                            </button>
                            <button type="button" class="btn btn-outline-secondary" id="reset-filters">
                                <i class="fas fa-undo me-2"></i> Reset Filters
                            </button>
                            <button type="button" class="btn btn-outline-success" id="save-filters">
                                <i class="fas fa-save me-2"></i> Save Filter Set
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="saved-filters mt-3 d-none">
                    <h6>Saved Filters</h6>
                    <div class="list-group saved-filters-list">
                        <!-- Saved filters will be added here -->
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert the filter panel before the table
    tableContainer.insertBefore(filterPanel, table);
    
    // Add event listeners
    document.getElementById('toggle-filter-panel').addEventListener('click', function() {
        const filterPanelBody = document.querySelector('.filter-panel-body');
        filterPanelBody.classList.toggle('d-none');
        
        // Update the toggle button icon
        const icon = this.querySelector('i');
        if (filterPanelBody.classList.contains('d-none')) {
            icon.className = 'fas fa-chevron-down';
        } else {
            icon.className = 'fas fa-chevron-up';
        }
    });
    
    document.getElementById('filter-date-range').addEventListener('change', function() {
        const customDateRange = document.querySelector('.custom-date-range');
        if (this.value === 'custom') {
            customDateRange.classList.remove('d-none');
        } else {
            customDateRange.classList.add('d-none');
        }
    });
    
    document.getElementById('apply-filters').addEventListener('click', function() {
        applyFilters(table);
    });
    
    document.getElementById('reset-filters').addEventListener('click', function() {
        resetFilters(table);
    });
    
    document.getElementById('save-filters').addEventListener('click', function() {
        saveCurrentFilters();
    });
    
    // Load saved filters
    loadSavedFilters();
}

/**
 * Initialize the quick filter
 * @param {HTMLElement} table - The table to filter
 */
function initializeQuickFilter(table) {
    // Get the table container
    const tableContainer = table.closest('.table-container') || table.parentNode;
    
    // Create the quick filter
    const quickFilter = document.createElement('div');
    quickFilter.className = 'quick-filter mb-3';
    quickFilter.innerHTML = `
        <div class="input-group">
            <span class="input-group-text">
                <i class="fas fa-search"></i>
            </span>
            <input type="text" class="form-control" id="quick-filter-input" placeholder="Quick search...">
            <button class="btn btn-outline-secondary" type="button" id="clear-quick-filter">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Insert the quick filter before the table but after the filter panel
    const filterPanel = tableContainer.querySelector('.filter-panel');
    if (filterPanel) {
        tableContainer.insertBefore(quickFilter, filterPanel.nextSibling);
    } else {
        tableContainer.insertBefore(quickFilter, table);
    }
    
    // Add event listeners
    document.getElementById('quick-filter-input').addEventListener('input', function() {
        quickFilterTable(table, this.value);
    });
    
    document.getElementById('clear-quick-filter').addEventListener('click', function() {
        document.getElementById('quick-filter-input').value = '';
        quickFilterTable(table, '');
    });
}

/**
 * Apply filters to the table
 * @param {HTMLElement} table - The table to filter
 */
function applyFilters(table) {
    // Get filter values
    const nameFilter = document.getElementById('filter-name').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const dateRangeFilter = document.getElementById('filter-date-range').value;
    const dateStartFilter = document.getElementById('filter-date-start').value;
    const dateEndFilter = document.getElementById('filter-date-end').value;
    
    // Calculate date range
    let startDate = null;
    let endDate = null;
    
    if (dateRangeFilter === 'custom') {
        if (dateStartFilter) startDate = new Date(dateStartFilter);
        if (dateEndFilter) endDate = new Date(dateEndFilter);
    } else if (dateRangeFilter) {
        const now = new Date();
        endDate = new Date(now);
        
        switch (dateRangeFilter) {
            case 'today':
                startDate = new Date(now.setHours(0, 0, 0, 0));
                break;
            case 'this-week':
                startDate = new Date(now);
                startDate.setDate(now.getDate() - now.getDay());
                startDate.setHours(0, 0, 0, 0);
                break;
            case 'this-month':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                break;
            case 'this-year':
                startDate = new Date(now.getFullYear(), 0, 1);
                break;
        }
    }
    
    // Filter the table rows
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        let showRow = true;
        
        // Name filter
        if (nameFilter) {
            const nameCell = row.querySelector('td:nth-child(2)');
            if (nameCell && !nameCell.textContent.toLowerCase().includes(nameFilter)) {
                showRow = false;
            }
        }
        
        // Status filter
        if (statusFilter) {
            const statusCell = row.querySelector('td:nth-child(4)');
            if (statusCell) {
                const progressBar = statusCell.querySelector('.progress-bar');
                const progressValue = progressBar ? parseInt(progressBar.style.width) : 0;
                
                if (statusFilter === 'completed' && progressValue < 100) {
                    showRow = false;
                } else if (statusFilter === 'in-progress' && progressValue >= 100) {
                    showRow = false;
                }
            }
        }
        
        // Date filter
        if (startDate || endDate) {
            const dateCell = row.querySelector('td:nth-child(3)');
            if (dateCell) {
                const dateText = dateCell.textContent.trim();
                const rowDate = new Date(dateText);
                
                if (startDate && rowDate < startDate) {
                    showRow = false;
                }
                
                if (endDate && rowDate > endDate) {
                    showRow = false;
                }
            }
        }
        
        // Show or hide the row
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update the filter results count
    updateFilterResultsCount(visibleCount, rows.length);
}

/**
 * Reset all filters
 * @param {HTMLElement} table - The table to reset
 */
function resetFilters(table) {
    // Reset filter inputs
    document.getElementById('filter-name').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-date-range').value = '';
    document.getElementById('filter-date-start').value = '';
    document.getElementById('filter-date-end').value = '';
    
    // Hide custom date range
    document.querySelector('.custom-date-range').classList.add('d-none');
    
    // Show all rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.style.display = '';
    });
    
    // Reset the quick filter
    document.getElementById('quick-filter-input').value = '';
    
    // Update the filter results count
    updateFilterResultsCount(rows.length, rows.length);
}

/**
 * Quick filter the table
 * @param {HTMLElement} table - The table to filter
 * @param {string} query - The search query
 */
function quickFilterTable(table, query) {
    query = query.toLowerCase();
    
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        if (query === '') {
            row.style.display = '';
            visibleCount++;
            return;
        }
        
        let showRow = false;
        const cells = row.querySelectorAll('td');
        
        cells.forEach(cell => {
            if (cell.textContent.toLowerCase().includes(query)) {
                showRow = true;
            }
        });
        
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update the filter results count
    updateFilterResultsCount(visibleCount, rows.length);
}

/**
 * Update the filter results count
 * @param {number} visibleCount - Number of visible rows
 * @param {number} totalCount - Total number of rows
 */
function updateFilterResultsCount(visibleCount, totalCount) {
    // Check if the results count element exists
    let resultsCount = document.querySelector('.filter-results-count');
    
    // If not, create it
    if (!resultsCount) {
        resultsCount = document.createElement('div');
        resultsCount.className = 'filter-results-count text-muted mt-2';
        
        const quickFilter = document.querySelector('.quick-filter');
        if (quickFilter) {
            quickFilter.appendChild(resultsCount);
        }
    }
    
    // Update the text
    resultsCount.textContent = `Showing ${visibleCount} of ${totalCount} records`;
}

/**
 * Save the current filter settings
 */
function saveCurrentFilters() {
    // Get the current filter values
    const filters = {
        name: document.getElementById('filter-name').value,
        status: document.getElementById('filter-status').value,
        dateRange: document.getElementById('filter-date-range').value,
        dateStart: document.getElementById('filter-date-start').value,
        dateEnd: document.getElementById('filter-date-end').value
    };
    
    // Prompt for a name
    const filterName = prompt('Enter a name for this filter set:');
    if (!filterName) return;
    
    // Get existing saved filters
    const savedFilters = JSON.parse(localStorage.getItem('savedFilters') || '{}');
    
    // Add the new filter
    savedFilters[filterName] = filters;
    
    // Save to localStorage
    localStorage.setItem('savedFilters', JSON.stringify(savedFilters));
    
    // Reload the saved filters list
    loadSavedFilters();
    
    // Show the saved filters section
    document.querySelector('.saved-filters').classList.remove('d-none');
}

/**
 * Load saved filters from localStorage
 */
function loadSavedFilters() {
    // Get saved filters
    const savedFilters = JSON.parse(localStorage.getItem('savedFilters') || '{}');
    
    // Get the saved filters list element
    const savedFiltersList = document.querySelector('.saved-filters-list');
    if (!savedFiltersList) return;
    
    // Clear the list
    savedFiltersList.innerHTML = '';
    
    // If there are no saved filters, hide the section
    if (Object.keys(savedFilters).length === 0) {
        document.querySelector('.saved-filters').classList.add('d-none');
        return;
    }
    
    // Show the section
    document.querySelector('.saved-filters').classList.remove('d-none');
    
    // Add each saved filter to the list
    for (const [name, filters] of Object.entries(savedFilters)) {
        const filterItem = document.createElement('a');
        filterItem.href = '#';
        filterItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        filterItem.innerHTML = `
            <span>${name}</span>
            <div>
                <button type="button" class="btn btn-sm btn-outline-primary apply-saved-filter" data-filter-name="${name}">
                    <i class="fas fa-check"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger delete-saved-filter" data-filter-name="${name}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        savedFiltersList.appendChild(filterItem);
    }
    
    // Add event listeners
    document.querySelectorAll('.apply-saved-filter').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            applySavedFilter(this.dataset.filterName);
        });
    });
    
    document.querySelectorAll('.delete-saved-filter').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            deleteSavedFilter(this.dataset.filterName);
        });
    });
}

/**
 * Apply a saved filter
 * @param {string} filterName - Name of the saved filter
 */
function applySavedFilter(filterName) {
    // Get saved filters
    const savedFilters = JSON.parse(localStorage.getItem('savedFilters') || '{}');
    
    // Get the specified filter
    const filter = savedFilters[filterName];
    if (!filter) return;
    
    // Apply the filter values to the form
    document.getElementById('filter-name').value = filter.name || '';
    document.getElementById('filter-status').value = filter.status || '';
    document.getElementById('filter-date-range').value = filter.dateRange || '';
    document.getElementById('filter-date-start').value = filter.dateStart || '';
    document.getElementById('filter-date-end').value = filter.dateEnd || '';
    
    // Show/hide custom date range
    const customDateRange = document.querySelector('.custom-date-range');
    if (filter.dateRange === 'custom') {
        customDateRange.classList.remove('d-none');
    } else {
        customDateRange.classList.add('d-none');
    }
    
    // Apply the filters
    const table = document.querySelector('.filterable-table');
    if (table) {
        applyFilters(table);
    }
}

/**
 * Delete a saved filter
 * @param {string} filterName - Name of the saved filter
 */
function deleteSavedFilter(filterName) {
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete the saved filter "${filterName}"?`)) {
        return;
    }
    
    // Get saved filters
    const savedFilters = JSON.parse(localStorage.getItem('savedFilters') || '{}');
    
    // Delete the specified filter
    delete savedFilters[filterName];
    
    // Save to localStorage
    localStorage.setItem('savedFilters', JSON.stringify(savedFilters));
    
    // Reload the saved filters list
    loadSavedFilters();
}
