// Common utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Enhanced UI/UX functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 7 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const dismissButton = alert.querySelector('.btn-close');
            if (dismissButton) {
                dismissButton.click();
            }
        });
    }, 7000);
    
    // Initialize enhanced features
    initializeLoadingStates();
    initializeEnhancedValidation();
    initializeProgressAnimations();
    initializeToastSystem();
});

// Form validation
function validateDateRange(startDate, endDate) {
    if (!startDate || !endDate) return true;
    return new Date(startDate) <= new Date(endDate);
}

function validateNumericInput(input, min = null, max = null) {
    const value = parseFloat(input.value);
    if (isNaN(value)) return false;
    if (min !== null && value < min) return false;
    if (max !== null && value > max) return false;
    return true;
}

// Add event listeners to numeric inputs
document.addEventListener('DOMContentLoaded', function() {
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            if (!validateNumericInput(this, this.min ? parseFloat(this.min) : null, this.max ? parseFloat(this.max) : null)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
});

// Date range validation
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        function validateDates() {
            if (!validateDateRange(startDateInput.value, endDateInput.value)) {
                endDateInput.classList.add('is-invalid');
                return false;
            } else {
                endDateInput.classList.remove('is-invalid');
                return true;
            }
        }
        
        startDateInput.addEventListener('change', validateDates);
        endDateInput.addEventListener('change', validateDates);
    }
});

/**
 * Initialize loading states for form submissions
 */
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Store original button text
                const originalText = submitBtn.innerHTML;
                
                // Add loading state
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitBtn.disabled = true;
                submitBtn.classList.add('loading');
                
                // Re-enable after 10 seconds (fallback)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('loading');
                }, 10000);
            }
        });
    });
}

/**
 * Enhanced form validation with better UX
 */
function initializeEnhancedValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const requiredInputs = form.querySelectorAll('[required]');
            let isValid = true;
            let firstInvalid = null;
            
            requiredInputs.forEach(function(input) {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    if (!firstInvalid) firstInvalid = input;
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                showToast('Please fill in all required fields correctly.', 'error');
            }
        });
        
        // Real-time validation feedback
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.required && !this.value.trim()) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                } else if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
}

/**
 * Initialize progress bar animations
 */
function initializeProgressAnimations() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        
        // Animate to target width
        setTimeout(() => {
            bar.style.transition = 'width 1.5s ease-in-out';
            bar.style.width = targetWidth;
        }, 200);
    });
}

/**
 * Toast notification system
 */
function initializeToastSystem() {
    // Create toast container if it doesn't exist
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
}

/**
 * Show toast notifications
 */
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const iconClass = type === 'success' ? 'fa-check-circle text-success' : 
                     type === 'error' ? 'fa-exclamation-triangle text-danger' :
                     type === 'warning' ? 'fa-exclamation-circle text-warning' :
                     'fa-info-circle text-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body d-flex align-items-center">
                <i class="fas ${iconClass} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close btn-close-sm ms-2" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Make showToast globally available
window.showToast = showToast;

/**
 * Export all evaluee data
 */
function exportAllData() {
    showToast('Preparing data export...', 'info');
    
    // Create download link
    const link = document.createElement('a');
    link.href = '/api/export-all-data';
    link.download = `economic-analysis-data-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        showToast('Data export completed!', 'success');
    }, 1000);
}

/**
 * Import data functionality
 */
function importData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.style.display = 'none';
    
    input.onchange = function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = JSON.parse(e.target.result);
                    
                    // Show confirmation modal
                    if (confirm('This will import data and may overwrite existing information. Continue?')) {
                        showToast('Importing data...', 'info');
                        
                        // Send data to server
                        fetch('/api/import-data', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(data)
                        })
                        .then(response => response.json())
                        .then(result => {
                            if (result.success) {
                                showToast('Data imported successfully!', 'success');
                                setTimeout(() => location.reload(), 2000);
                            } else {
                                showToast('Import failed: ' + result.message, 'error');
                            }
                        })
                        .catch(error => {
                            showToast('Import failed: ' + error.message, 'error');
                        });
                    }
                } catch (error) {
                    showToast('Invalid file format. Please select a valid JSON file.', 'error');
                }
            };
            reader.readAsText(file);
        }
    };
    
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
}

// Make functions globally available
window.exportAllData = exportAllData;
window.importData = importData;

// Enhanced confirmation dialogs
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    // Use Bootstrap modal if available, otherwise fallback to confirm
    if (typeof bootstrap !== 'undefined') {
        return new Promise((resolve) => {
            const modalHTML = `
                <div class="modal fade" id="confirmModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Confirm Action</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="d-flex align-items-center">
                                    <i class="fas fa-exclamation-triangle text-warning me-3 fa-2x"></i>
                                    <div>${message}</div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-danger" id="confirmBtn">Delete</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            
            document.getElementById('confirmBtn').addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });
            
            document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
                document.getElementById('confirmModal').remove();
            });
            
            modal.show();
        });
    } else {
        return confirm(message);
    }
}

// Table sorting
function sortTable(table, column) {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const direction = table.dataset.sortDirection === 'asc' ? -1 : 1;
    
    rows.sort((a, b) => {
        const aValue = a.children[column].textContent;
        const bValue = b.children[column].textContent;
        
        if (!isNaN(parseFloat(aValue)) && !isNaN(parseFloat(bValue))) {
            return direction * (parseFloat(aValue) - parseFloat(bValue));
        }
        return direction * aValue.localeCompare(bValue);
    });
    
    table.dataset.sortDirection = direction === 1 ? 'asc' : 'desc';
    
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

// Initialize tooltips and popovers if Bootstrap is present
document.addEventListener('DOMContentLoaded', function() {
    if (typeof bootstrap !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
        
        const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(popover => new bootstrap.Popover(popover));
    }
}); 