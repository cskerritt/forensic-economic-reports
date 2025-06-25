/**
 * User Preferences System
 * 
 * This script provides functionality to save and load user preferences
 * for the Economic Analysis application.
 */

// Define the key for storing preferences in localStorage
const PREFERENCES_KEY = 'economic_analysis_preferences';

/**
 * Get all user preferences
 * @returns {Object} User preferences object
 */
function getUserPreferences() {
    const preferencesJson = localStorage.getItem(PREFERENCES_KEY);
    return preferencesJson ? JSON.parse(preferencesJson) : {};
}

/**
 * Save a user preference
 * @param {string} key - Preference key
 * @param {any} value - Preference value
 */
function saveUserPreference(key, value) {
    const preferences = getUserPreferences();
    preferences[key] = value;
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
}

/**
 * Get a specific user preference
 * @param {string} key - Preference key
 * @param {any} defaultValue - Default value if preference doesn't exist
 * @returns {any} Preference value or default value
 */
function getUserPreference(key, defaultValue = null) {
    const preferences = getUserPreferences();
    return preferences.hasOwnProperty(key) ? preferences[key] : defaultValue;
}

/**
 * Delete a user preference
 * @param {string} key - Preference key to delete
 */
function deleteUserPreference(key) {
    const preferences = getUserPreferences();
    if (preferences.hasOwnProperty(key)) {
        delete preferences[key];
        localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
    }
}

/**
 * Clear all user preferences
 */
function clearUserPreferences() {
    localStorage.removeItem(PREFERENCES_KEY);
}

/**
 * Initialize the preferences system
 */
function initializePreferences() {
    // Apply saved theme if it exists
    const theme = getUserPreference('theme', 'light');
    applyTheme(theme);
    
    // Apply saved dashboard layout if on dashboard
    if (window.location.pathname.includes('/dashboard')) {
        const layout = getUserPreference('dashboardLayout', 'default');
        applyDashboardLayout(layout);
    }
    
    // Apply table display preferences
    applyTablePreferences();
    
    // Initialize preference controls
    initializePreferenceControls();
}

/**
 * Apply the selected theme
 * @param {string} theme - Theme name ('light' or 'dark')
 */
function applyTheme(theme) {
    const body = document.body;
    
    if (theme === 'dark') {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
    } else {
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
    }
    
    // Save the preference
    saveUserPreference('theme', theme);
}

/**
 * Apply dashboard layout preference
 * @param {string} layout - Layout name
 */
function applyDashboardLayout(layout) {
    const dashboardContainer = document.querySelector('.dashboard-container');
    if (!dashboardContainer) return;
    
    // Remove existing layout classes
    dashboardContainer.classList.remove('layout-default', 'layout-compact', 'layout-expanded');
    
    // Add the selected layout class
    dashboardContainer.classList.add(`layout-${layout}`);
    
    // Save the preference
    saveUserPreference('dashboardLayout', layout);
}

/**
 * Apply table display preferences
 */
function applyTablePreferences() {
    const tableRowsPerPage = getUserPreference('tableRowsPerPage', 10);
    const tableCompactView = getUserPreference('tableCompactView', false);
    
    // Apply rows per page to any pagination controls
    const paginationSelects = document.querySelectorAll('.pagination-rows-select');
    paginationSelects.forEach(select => {
        select.value = tableRowsPerPage;
    });
    
    // Apply compact view to tables
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        if (tableCompactView) {
            table.classList.add('table-sm');
        } else {
            table.classList.remove('table-sm');
        }
    });
}

/**
 * Initialize preference controls
 */
function initializePreferenceControls() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const currentTheme = getUserPreference('theme', 'light');
        themeToggle.checked = currentTheme === 'dark';
        
        themeToggle.addEventListener('change', function() {
            applyTheme(this.checked ? 'dark' : 'light');
        });
    }
    
    // Dashboard layout controls
    const layoutControls = document.querySelectorAll('[data-layout]');
    layoutControls.forEach(control => {
        control.addEventListener('click', function() {
            const layout = this.dataset.layout;
            applyDashboardLayout(layout);
            
            // Update active state on controls
            layoutControls.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
        
        // Set initial active state
        const currentLayout = getUserPreference('dashboardLayout', 'default');
        if (control.dataset.layout === currentLayout) {
            control.classList.add('active');
        }
    });
    
    // Table rows per page control
    const rowsPerPageSelect = document.getElementById('table-rows-per-page');
    if (rowsPerPageSelect) {
        rowsPerPageSelect.value = getUserPreference('tableRowsPerPage', 10);
        
        rowsPerPageSelect.addEventListener('change', function() {
            saveUserPreference('tableRowsPerPage', parseInt(this.value));
            applyTablePreferences();
        });
    }
    
    // Table compact view toggle
    const compactViewToggle = document.getElementById('table-compact-view');
    if (compactViewToggle) {
        compactViewToggle.checked = getUserPreference('tableCompactView', false);
        
        compactViewToggle.addEventListener('change', function() {
            saveUserPreference('tableCompactView', this.checked);
            applyTablePreferences();
        });
    }
}

// Initialize preferences when the DOM is loaded
document.addEventListener('DOMContentLoaded', initializePreferences);

// Create the preferences panel
document.addEventListener('DOMContentLoaded', function() {
    createPreferencesPanel();
});

/**
 * Create the preferences panel
 */
function createPreferencesPanel() {
    // Only create the panel if the user is logged in
    if (!document.querySelector('.navbar-nav .dropdown-toggle')) return;
    
    // Create the panel container
    const panel = document.createElement('div');
    panel.id = 'preferences-panel';
    panel.className = 'preferences-panel';
    panel.innerHTML = `
        <div class="preferences-header">
            <h5>User Preferences</h5>
            <button type="button" class="btn-close" id="close-preferences"></button>
        </div>
        <div class="preferences-body">
            <div class="preference-section">
                <h6>Theme</h6>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="theme-toggle">
                    <label class="form-check-label" for="theme-toggle">Dark Mode</label>
                </div>
            </div>
            
            <div class="preference-section">
                <h6>Dashboard Layout</h6>
                <div class="btn-group w-100">
                    <button type="button" class="btn btn-outline-primary" data-layout="default">Default</button>
                    <button type="button" class="btn btn-outline-primary" data-layout="compact">Compact</button>
                    <button type="button" class="btn btn-outline-primary" data-layout="expanded">Expanded</button>
                </div>
            </div>
            
            <div class="preference-section">
                <h6>Table Display</h6>
                <div class="mb-3">
                    <label for="table-rows-per-page" class="form-label">Rows per page</label>
                    <select class="form-select" id="table-rows-per-page">
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="table-compact-view">
                    <label class="form-check-label" for="table-compact-view">Compact View</label>
                </div>
            </div>
            
            <div class="preference-section">
                <h6>Reset Preferences</h6>
                <button type="button" class="btn btn-danger w-100" id="reset-preferences">
                    Reset All Preferences
                </button>
            </div>
        </div>
    `;
    
    // Add styles for the panel
    const style = document.createElement('style');
    style.textContent = `
        .preferences-panel {
            position: fixed;
            top: 0;
            right: -300px;
            width: 300px;
            height: 100%;
            background-color: #fff;
            box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
            z-index: 1050;
            transition: right 0.3s ease;
            overflow-y: auto;
        }
        .preferences-panel.open {
            right: 0;
        }
        .preferences-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
        }
        .preferences-header h5 {
            margin: 0;
        }
        .preferences-body {
            padding: 15px;
        }
        .preference-section {
            margin-bottom: 20px;
        }
        .preference-section h6 {
            margin-bottom: 10px;
            color: #495057;
        }
        .dark-theme {
            background-color: #343a40;
            color: #f8f9fa;
        }
        .dark-theme .card {
            background-color: #495057;
            color: #f8f9fa;
        }
        .dark-theme .navbar {
            background-color: #212529 !important;
        }
        .dark-theme .table {
            color: #f8f9fa;
        }
        .dark-theme .preferences-panel {
            background-color: #343a40;
            color: #f8f9fa;
        }
        .dark-theme .form-control,
        .dark-theme .form-select {
            background-color: #495057;
            color: #f8f9fa;
            border-color: #6c757d;
        }
        .layout-compact .card {
            margin-bottom: 10px;
        }
        .layout-compact .card-body {
            padding: 0.75rem;
        }
        .layout-expanded .card {
            margin-bottom: 30px;
        }
        .layout-expanded .card-body {
            padding: 1.5rem;
        }
        .preferences-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: #007bff;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            z-index: 1040;
        }
    `;
    
    // Add the panel and styles to the document
    document.head.appendChild(style);
    document.body.appendChild(panel);
    
    // Create the toggle button
    const toggleButton = document.createElement('div');
    toggleButton.className = 'preferences-toggle';
    toggleButton.innerHTML = '<i class="fas fa-cog"></i>';
    document.body.appendChild(toggleButton);
    
    // Add event listeners
    toggleButton.addEventListener('click', function() {
        panel.classList.toggle('open');
    });
    
    document.getElementById('close-preferences').addEventListener('click', function() {
        panel.classList.remove('open');
    });
    
    document.getElementById('reset-preferences').addEventListener('click', function() {
        if (confirm('Are you sure you want to reset all preferences to default?')) {
            clearUserPreferences();
            window.location.reload();
        }
    });
    
    // Initialize the controls
    initializePreferenceControls();
}
