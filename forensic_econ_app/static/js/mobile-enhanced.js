/**
 * Mobile Enhancement JavaScript for Economic Analysis Tool
 * Provides touch-friendly interactions and mobile-specific optimizations
 */

(function() {
    'use strict';
    
    // Mobile device detection
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // Initialize mobile enhancements when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        if (isMobile || isTouch) {
            document.body.classList.add('mobile-device');
            initializeMobileEnhancements();
        }
    });
    
    function initializeMobileEnhancements() {
        // Enhance form inputs for mobile
        enhanceFormInputs();
        
        // Add touch feedback to buttons
        addTouchFeedback();
        
        // Optimize date pickers for mobile
        optimizeDatePickers();
        
        // Add mobile-friendly tooltips
        convertTooltipsToTapable();
        
        // Enhance table interactions
        enhanceTableInteractions();
        
        // Add swipe gestures where appropriate
        addSwipeGestures();
        
        // Fix iOS specific issues
        fixiOSIssues();
        
        // Add mobile navigation helpers
        addMobileNavigationHelpers();
    }
    
    function enhanceFormInputs() {
        // Set appropriate input modes for numeric fields
        const numericInputs = document.querySelectorAll('input[type="number"], .numeric-input');
        numericInputs.forEach(input => {
            if (!input.hasAttribute('inputmode')) {
                if (input.step && input.step.includes('.')) {
                    input.setAttribute('inputmode', 'decimal');
                } else {
                    input.setAttribute('inputmode', 'numeric');
                }
            }
        });
        
        // Prevent zoom on iOS for inputs
        const allInputs = document.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                input.style.fontSize = '16px';
            }
        });
        
        // Add clear buttons to text inputs on mobile
        const textInputs = document.querySelectorAll('input[type="text"], input[type="email"]');
        textInputs.forEach(addClearButton);
    }
    
    function addClearButton(input) {
        if (input.parentElement.classList.contains('input-group')) return;
        
        const wrapper = document.createElement('div');
        wrapper.className = 'position-relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-link position-absolute top-50 end-0 translate-middle-y me-2 p-1';
        clearBtn.style.display = 'none';
        clearBtn.innerHTML = '<i class="fas fa-times-circle text-muted"></i>';
        clearBtn.setAttribute('aria-label', 'Clear input');
        
        clearBtn.addEventListener('click', function() {
            input.value = '';
            input.focus();
            clearBtn.style.display = 'none';
            input.dispatchEvent(new Event('input', { bubbles: true }));
        });
        
        input.addEventListener('input', function() {
            clearBtn.style.display = input.value.length > 0 ? 'block' : 'none';
        });
        
        wrapper.appendChild(clearBtn);
    }
    
    function addTouchFeedback() {
        const buttons = document.querySelectorAll('.btn, .card, .list-group-item');
        buttons.forEach(button => {
            if (!button.classList.contains('no-touch-feedback')) {
                button.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.98)';
                    this.style.transition = 'transform 0.1s ease';
                });
                
                button.addEventListener('touchend', function() {
                    setTimeout(() => {
                        this.style.transform = '';
                    }, 100);
                });
            }
        });
    }
    
    function optimizeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"], input[type="datetime-local"]');
        dateInputs.forEach(input => {
            // Add calendar icon for better UX
            if (!input.parentElement.querySelector('.calendar-icon')) {
                const icon = document.createElement('span');
                icon.className = 'calendar-icon position-absolute top-50 end-0 translate-middle-y me-3';
                icon.innerHTML = '<i class="fas fa-calendar-alt text-muted"></i>';
                icon.style.pointerEvents = 'none';
                
                if (input.parentElement.classList.contains('position-relative')) {
                    input.parentElement.appendChild(icon);
                } else {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'position-relative';
                    input.parentNode.insertBefore(wrapper, input);
                    wrapper.appendChild(input);
                    wrapper.appendChild(icon);
                }
            }
        });
    }
    
    function convertTooltipsToTapable() {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            const originalTitle = element.getAttribute('data-bs-original-title') || element.getAttribute('title');
            if (originalTitle) {
                element.addEventListener('click', function(e) {
                    e.preventDefault();
                    showMobileTooltip(this, originalTitle);
                });
            }
        });
    }
    
    function showMobileTooltip(element, message) {
        // Remove any existing mobile tooltips
        const existingTooltip = document.querySelector('.mobile-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }
        
        const tooltip = document.createElement('div');
        tooltip.className = 'mobile-tooltip alert alert-info alert-dismissible fade show position-fixed';
        tooltip.style.cssText = `
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            max-width: 90%;
            min-width: 200px;
            font-size: 14px;
        `;
        
        tooltip.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(tooltip);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, 3000);
    }
    
    function enhanceTableInteractions() {
        const tables = document.querySelectorAll('.table-responsive table');
        tables.forEach(table => {
            // Add horizontal scroll hint
            const scrollHint = document.createElement('div');
            scrollHint.className = 'text-muted small text-center py-2 swipe-hint';
            scrollHint.textContent = 'Swipe left/right to see more columns';
            
            const tableContainer = table.closest('.table-responsive');
            if (tableContainer && !tableContainer.querySelector('.swipe-hint')) {
                tableContainer.appendChild(scrollHint);
                
                // Hide hint after user scrolls
                tableContainer.addEventListener('scroll', function() {
                    scrollHint.style.display = 'none';
                }, { once: true });
            }
        });
        
        // Make table rows tappable on mobile
        const tableRows = document.querySelectorAll('tbody tr[data-href]');
        tableRows.forEach(row => {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function() {
                const href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            });
        });
    }
    
    function addSwipeGestures() {
        // Add swipe-to-delete functionality for list items
        const swipeableItems = document.querySelectorAll('.swipeable-item, .list-group-item');
        
        swipeableItems.forEach(item => {
            let startX = 0;
            let currentX = 0;
            let isDragging = false;
            
            item.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
                isDragging = true;
                this.style.transition = '';
            });
            
            item.addEventListener('touchmove', function(e) {
                if (!isDragging) return;
                
                currentX = e.touches[0].clientX;
                const deltaX = currentX - startX;
                
                if (Math.abs(deltaX) > 10) {
                    e.preventDefault();
                    this.style.transform = `translateX(${deltaX}px)`;
                    
                    // Add visual feedback for delete action
                    if (deltaX < -50) {
                        this.style.backgroundColor = '#f8d7da';
                    } else {
                        this.style.backgroundColor = '';
                    }
                }
            });
            
            item.addEventListener('touchend', function() {
                if (!isDragging) return;
                
                const deltaX = currentX - startX;
                this.style.transition = 'transform 0.3s ease, background-color 0.3s ease';
                
                if (deltaX < -100) {
                    // Trigger delete action
                    const deleteBtn = this.querySelector('.btn-danger, [data-action="delete"]');
                    if (deleteBtn) {
                        deleteBtn.click();
                    }
                } else {
                    // Reset position
                    this.style.transform = '';
                    this.style.backgroundColor = '';
                }
                
                isDragging = false;
                startX = 0;
                currentX = 0;
            });
        });
    }
    
    function fixiOSIssues() {
        if (/(iPad|iPhone|iPod)/g.test(navigator.userAgent)) {
            // Fix iOS viewport scaling issues
            const viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
            }
            
            // Fix iOS rubber band scrolling
            document.body.addEventListener('touchmove', function(e) {
                if (e.target.closest('.table-responsive, .overflow-auto')) {
                    return;
                }
                e.preventDefault();
            }, { passive: false });
            
            // Fix iOS double-tap zoom
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(event) {
                const now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
        }
    }
    
    function addMobileNavigationHelpers() {
        // Add back-to-top button for long pages
        if (document.body.scrollHeight > window.innerHeight * 2) {
            const backToTop = document.createElement('button');
            backToTop.className = 'btn btn-primary btn-floating position-fixed';
            backToTop.style.cssText = `
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                display: none;
            `;
            backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
            backToTop.setAttribute('aria-label', 'Back to top');
            
            backToTop.addEventListener('click', function() {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            
            document.body.appendChild(backToTop);
            
            // Show/hide back-to-top button
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 300) {
                    backToTop.style.display = 'block';
                } else {
                    backToTop.style.display = 'none';
                }
            });
        }
        
        // Add mobile breadcrumb improvements
        const breadcrumb = document.querySelector('.breadcrumb');
        if (breadcrumb) {
            const items = breadcrumb.querySelectorAll('.breadcrumb-item');
            if (items.length > 3) {
                // Show only first, last, and current items on mobile
                items.forEach((item, index) => {
                    if (index > 0 && index < items.length - 2) {
                        item.classList.add('d-none', 'd-md-inline');
                    }
                });
                
                // Add ellipsis indicator
                if (items.length > 2) {
                    const ellipsis = document.createElement('li');
                    ellipsis.className = 'breadcrumb-item d-md-none';
                    ellipsis.innerHTML = '<span class="text-muted">...</span>';
                    breadcrumb.insertBefore(ellipsis, items[items.length - 1]);
                }
            }
        }
    }
    
    // Utility function to detect if element is in viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Export functions for use by other scripts
    window.MobileEnhancements = {
        isMobile: isMobile,
        isTouch: isTouch,
        showMobileTooltip: showMobileTooltip,
        isInViewport: isInViewport
    };
    
})();