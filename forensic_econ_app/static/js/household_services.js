/**
 * Household Services Module JavaScript
 * 
 * This script handles the interactive functionality for the household services module
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize stage management
    initializeStageManagement();
    
    // Initialize charts if they exist
    initializeCharts();
    
    // Set up auto-save functionality
    setupAutoSave();
    
    // Initialize mobile enhancements
    initializeMobileEnhancements();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Get all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize stage management functionality
 */
function initializeStageManagement() {
    // Auto-increment stage number
    const stageNumberInput = document.getElementById('stage_number');
    const stagesTable = document.querySelector('.stages-table');
    
    if (stageNumberInput && stagesTable) {
        // Get the highest stage number from the table
        const stageRows = stagesTable.querySelectorAll('tbody tr');
        let highestStage = 0;
        
        stageRows.forEach(row => {
            const stageNumber = parseInt(row.querySelector('td:first-child').textContent);
            if (stageNumber > highestStage) {
                highestStage = stageNumber;
            }
        });
        
        // Set the next stage number
        stageNumberInput.value = highestStage + 1;
    }
    
    // Add stage form validation
    const addStageForm = document.getElementById('add-stage-form');
    if (addStageForm) {
        addStageForm.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            this.classList.add('was-validated');
        });
    }
}

/**
 * Initialize charts for visualizing household services data
 */
function initializeCharts() {
    // Only initialize if Chart.js is available and we have a chart container
    if (typeof Chart === 'undefined' || !document.getElementById('household-chart')) {
        return;
    }
    
    // Get the stage data from the data attributes
    const chartElement = document.getElementById('household-chart');
    const stageNumbers = chartElement.dataset.stageNumbers.split(',').map(Number);
    const stageYears = chartElement.dataset.stageYears.split(',').map(Number);
    const stageValues = chartElement.dataset.stageValues.split(',').map(Number);
    
    // Create the chart
    new Chart(chartElement, {
        type: 'bar',
        data: {
            labels: stageNumbers.map(num => `Stage ${num}`),
            datasets: [{
                label: 'Annual Value ($)',
                data: stageValues,
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            }, {
                label: 'Years',
                data: stageYears,
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Set up auto-save functionality for forms
 */
function setupAutoSave() {
    const forms = document.querySelectorAll('.auto-save-form');
    
    forms.forEach(form => {
        // Track form changes
        const formInputs = form.querySelectorAll('input, select, textarea');
        let formChanged = false;
        
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                formChanged = true;
            });
        });
        
        // Auto-save every 30 seconds if the form has changed
        setInterval(() => {
            if (formChanged) {
                // Create a hidden submit button and click it
                const tempButton = document.createElement('button');
                tempButton.type = 'submit';
                tempButton.style.display = 'none';
                form.appendChild(tempButton);
                tempButton.click();
                form.removeChild(tempButton);
                
                // Reset the changed flag
                formChanged = false;
                
                // Show a notification
                showNotification('Form auto-saved', 'info');
            }
        }, 30000);
    });
}

/**
 * Show a notification message
 * 
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, info, warning, danger)
 * @param {number} duration - How long to show the notification in milliseconds
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Create the notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Add to document
    const container = document.createElement('div');
    container.className = 'notification-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.appendChild(notification);
    document.body.appendChild(container);
    
    // Auto-remove after duration
    setTimeout(() => {
        notification.classList.add('fade');
        setTimeout(() => {
            if (container.parentNode) {
                document.body.removeChild(container);
            }
        }, 500);
    }, duration);
}

/**
 * Initialize mobile-specific enhancements
 */
function initializeMobileEnhancements() {
    // Detect if on mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Add mobile class to body for additional styling
        document.body.classList.add('is-mobile');
        
        // Enhance touch interactions
        enhanceTouchInteractions();
        
        // Fix iOS input zoom issue
        fixIOSInputZoom();
        
        // Add swipe-to-delete functionality for stage cards on mobile
        addSwipeToDelete();
    }
    
    // Handle responsive tooltips
    handleResponsiveTooltips();
    
    // Optimize form inputs for mobile
    optimizeMobileFormInputs();
}

/**
 * Enhance touch interactions for better mobile experience
 */
function enhanceTouchInteractions() {
    // Add touch feedback to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.classList.add('btn-touch-active');
        });
        
        button.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('btn-touch-active');
            }, 150);
        });
    });
}

/**
 * Fix iOS input zoom issue
 */
function fixIOSInputZoom() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    if (isIOS) {
        const metaViewport = document.querySelector('meta[name="viewport"]');
        if (metaViewport) {
            metaViewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
        
        // Prevent double-tap zoom
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = new Date().getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
}

/**
 * Add swipe-to-delete functionality for mobile stage cards
 */
function addSwipeToDelete() {
    const stageCards = document.querySelectorAll('.d-md-none .card');
    
    stageCards.forEach(card => {
        let startX = 0;
        let currentX = 0;
        let cardElement = card;
        
        cardElement.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
        });
        
        cardElement.addEventListener('touchmove', function(e) {
            currentX = e.touches[0].clientX;
            const diffX = currentX - startX;
            
            if (diffX < -50) {
                this.style.transform = `translateX(${diffX}px)`;
                this.style.opacity = 1 + (diffX / 200);
            }
        });
        
        cardElement.addEventListener('touchend', function() {
            const diffX = currentX - startX;
            
            if (diffX < -100) {
                // Show delete confirmation
                const deleteBtn = this.querySelector('.btn-danger');
                if (deleteBtn && confirm('Swipe to delete this stage?')) {
                    deleteBtn.click();
                }
            }
            
            // Reset position
            this.style.transform = '';
            this.style.opacity = '';
        });
    });
}

/**
 * Handle responsive tooltips - disable on touch devices
 */
function handleResponsiveTooltips() {
    const hasTouch = 'ontouchstart' in window;
    
    if (hasTouch) {
        // Convert tooltips to click-based info buttons on mobile
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            element.removeAttribute('data-bs-toggle');
            element.addEventListener('click', function(e) {
                e.preventDefault();
                const title = this.getAttribute('title') || this.getAttribute('data-bs-original-title');
                if (title) {
                    showNotification(title, 'info', 5000);
                }
            });
        });
    }
}

/**
 * Optimize form inputs for mobile devices
 */
function optimizeMobileFormInputs() {
    // Add proper input modes for better mobile keyboards
    const inputs = document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        // Already set in HTML, but ensure it's there
        if (!input.hasAttribute('inputmode')) {
            if (input.step && parseFloat(input.step) < 1) {
                input.setAttribute('inputmode', 'decimal');
            } else {
                input.setAttribute('inputmode', 'numeric');
            }
        }
        
        // Add pattern for better mobile validation
        if (!input.hasAttribute('pattern') && input.getAttribute('inputmode') === 'decimal') {
            input.setAttribute('pattern', '[0-9]*\\.?[0-9]*');
        }
    });
    
    // Auto-focus management for mobile
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
        // Remove auto-focus on mobile to prevent keyboard popup
        const autoFocusElements = document.querySelectorAll('[autofocus]');
        autoFocusElements.forEach(element => {
            element.removeAttribute('autofocus');
        });
    }
}
