/**
 * Demographics Automation Script
 *
 * This script provides automation features for the demographics form:
 * - Auto-fill demo data
 * - Form validation
 * - Tooltips
 * - Auto-save functionality
 */

// Date formatting and validation functions
function formatDateInput(input) {
    let value = input.value.replace(/\D/g, ''); // Remove non-digits
    let formattedValue = '';
    
    if (value.length >= 2) {
        formattedValue = value.substring(0, 2) + '/';
        if (value.length >= 4) {
            formattedValue += value.substring(2, 4) + '/';
            if (value.length >= 8) {
                formattedValue += value.substring(4, 8);
            } else {
                formattedValue += value.substring(4);
            }
        } else {
            formattedValue += value.substring(2);
        }
    } else {
        formattedValue = value;
    }
    
    input.value = formattedValue;
}

function validateDate(dateString) {
    // Check format
    const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    const match = dateString.match(dateRegex);
    
    if (!match) {
        return { valid: false, message: 'Please use MM/DD/YYYY format' };
    }
    
    const month = parseInt(match[1]);
    const day = parseInt(match[2]);
    const year = parseInt(match[3]);
    
    // Check ranges
    if (month < 1 || month > 12) {
        return { valid: false, message: 'Month must be between 01 and 12' };
    }
    
    if (year < 1900 || year > new Date().getFullYear()) {
        return { valid: false, message: 'Year must be between 1900 and current year' };
    }
    
    // Check day validity for the given month/year
    const daysInMonth = new Date(year, month, 0).getDate();
    if (day < 1 || day > daysInMonth) {
        return { valid: false, message: `Day must be between 01 and ${daysInMonth} for ${month}/${year}` };
    }
    
    // Check that date is not in the future
    const date = new Date(year, month - 1, day);
    if (date > new Date()) {
        return { valid: false, message: 'Date cannot be in the future' };
    }
    
    return { valid: true, date: date };
}

function convertDateFormat(dateString) {
    const match = dateString.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (match) {
        return `${match[3]}-${match[1]}-${match[2]}`;
    }
    return dateString;
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Set up date inputs
    const dobInput = document.getElementById('date_of_birth');
    const doiInput = document.getElementById('date_of_injury');
    
    if (dobInput) {
        // Format as user types
        dobInput.addEventListener('input', function() {
            formatDateInput(this);
        });
        
        // Validate on blur
        dobInput.addEventListener('blur', function() {
            if (this.value) {
                const validation = validateDate(this.value);
                if (!validation.valid) {
                    this.setCustomValidity(validation.message);
                    this.classList.add('is-invalid');
                    this.reportValidity();
                } else {
                    this.setCustomValidity('');
                    this.classList.remove('is-invalid');
                }
            }
        });
    }
    
    if (doiInput) {
        // Format as user types
        doiInput.addEventListener('input', function() {
            formatDateInput(this);
        });
        
        // Validate on blur
        doiInput.addEventListener('blur', function() {
            if (this.value) {
                const validation = validateDate(this.value);
                if (!validation.valid) {
                    this.setCustomValidity(validation.message);
                    this.classList.add('is-invalid');
                    this.reportValidity();
                } else {
                    this.setCustomValidity('');
                    this.classList.remove('is-invalid');
                }
            }
        });
    }

    // Form validation
    const form = document.getElementById('demographics-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Validate dates
            let isValid = true;
            
            if (dobInput && dobInput.value) {
                const dobValidation = validateDate(dobInput.value);
                if (!dobValidation.valid) {
                    dobInput.setCustomValidity(dobValidation.message);
                    dobInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    // Convert to YYYY-MM-DD format for backend
                    dobInput.value = convertDateFormat(dobInput.value);
                }
            }
            
            if (doiInput && doiInput.value) {
                const doiValidation = validateDate(doiInput.value);
                if (!doiValidation.valid) {
                    doiInput.setCustomValidity(doiValidation.message);
                    doiInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    // Convert to YYYY-MM-DD format for backend
                    doiInput.value = convertDateFormat(doiInput.value);
                }
            }
            
            if (!form.checkValidity() || !isValid) {
                event.stopPropagation();
                showNotification('Please fill in all required fields correctly.', 'danger');
            } else {
                showNotification('Saving demographics...', 'info');
                form.submit();
            }
            
            form.classList.add('was-validated');
        });
    }

    // Auto-fill demo data button
    const autoFillButton = document.getElementById('auto-fill-demo');
    if (autoFillButton) {
        autoFillButton.addEventListener('click', function() {
            // Set demo values
            const today = new Date();
            const birthYear = today.getFullYear() - 35; // 35 years old
            const injuryYear = today.getFullYear() - 2; // Injured 2 years ago

            // Format dates as MM/DD/YYYY
            const formatDate = (date) => {
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const year = date.getFullYear();
                return `${month}/${day}/${year}`;
            };

            // Set form values
            if (dobInput) {
                dobInput.value = formatDate(new Date(birthYear, today.getMonth(), today.getDate()));
            }
            if (doiInput) {
                doiInput.value = formatDate(new Date(injuryYear, today.getMonth(), today.getDate()));
            }

            document.getElementById('gender').value = 'Men';
            document.getElementById('education_level').value = 'Bachelor\'s Degree';

            // Randomly select a race for demo purposes
            const races = ['N/A', 'White', 'Black', 'Hispanic'];
            const randomRace = races[Math.floor(Math.random() * races.length)];
            if (document.getElementById('race')) {
                document.getElementById('race').value = randomRace;
            }

            // Fill in sample work life values
            document.getElementById('life_expectancy').value = '42.5';
            document.getElementById('work_life_expectancy').value = '20.5';
            document.getElementById('years_to_final_separation').value = '23.5';

            // Show success message
            showNotification('Sample data filled successfully. All fields are now populated with example values.', 'success');
        });
    }

    // Add simple form validation feedback
    const saveButton = document.getElementById('save-demographics-btn');
    if (saveButton) {
        saveButton.addEventListener('click', function(event) {
            if (form && !form.checkValidity()) {
                showNotification('Please fill in all required fields before saving.', 'warning');
            } else {
                showNotification('Saving demographics...', 'info');
            }
        });
    }

    // Use table values button
    const useTableValuesButton = document.getElementById('use-table-values');
    if (useTableValuesButton) {
        useTableValuesButton.addEventListener('click', function() {
            // Validate required fields
            const dateOfBirth = document.getElementById('date_of_birth').value;
            const dateOfInjury = document.getElementById('date_of_injury').value;
            const gender = document.getElementById('gender').value;
            const educationLevel = document.getElementById('education_level').value;

            if (!dateOfBirth || !dateOfInjury || !gender || !educationLevel) {
                showNotification('Please fill in all required fields (Date of Birth, Date of Injury, Gender, Education Level).', 'danger');
                return;
            }

            // Show loading state
            const originalButtonText = useTableValuesButton.innerHTML;
            useTableValuesButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            useTableValuesButton.disabled = true;

            // Show notification
            showNotification('Looking up worklife values from tables...', 'info');

            // Submit form to lookup endpoint
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/demographics/${evalueeId}/lookup`;
            document.body.appendChild(form);
            form.submit();

            // Reset button after a short delay (in case the page doesn't redirect immediately)
            setTimeout(() => {
                useTableValuesButton.innerHTML = originalButtonText;
                useTableValuesButton.disabled = false;
            }, 5000);
        });
    }

    // Life expectancy lookup
    const lookupLifeExpectancyButton = document.getElementById('lookup-life-expectancy');
    if (lookupLifeExpectancyButton) {
        lookupLifeExpectancyButton.addEventListener('click', function() {
            // Get current values
            const gender = document.getElementById('gender').value;
            const race = document.getElementById('race').value;

            // Calculate current age
            const dateOfBirth = document.getElementById('date_of_birth').value;
            if (!dateOfBirth) {
                showNotification('Please enter a date of birth to calculate life expectancy.', 'warning');
                return;
            }

            // Convert MM/DD/YYYY to Date object
            const dobValidation = validateDate(dateOfBirth);
            if (!dobValidation.valid) {
                showNotification('Please enter a valid date of birth.', 'warning');
                return;
            }

            const birthDate = dobValidation.date;
            const today = new Date();
            const ageInMilliseconds = today - birthDate;
            const ageInYears = ageInMilliseconds / (1000 * 60 * 60 * 24 * 365.25);

            // Make API request
            fetch(`/demographics/${evalueeId}/life-expectancy?gender=${gender}&race=${race}&age=${ageInYears}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(`Error: ${data.error}`, 'danger');
                        return;
                    }

                    // Display results
                    document.getElementById('le-additional-years').textContent = data.results.additionalYears.toFixed(2);
                    document.getElementById('le-expected-age').textContent = data.results.totalYears.toFixed(2);
                    document.getElementById('le-death-year').textContent =
                        `${data.results.deathYear.monthName} ${data.results.deathYear.year}`;

                    // Set hidden form values
                    document.getElementById('le-gender').value = gender;
                    document.getElementById('le-race').value = race;
                    document.getElementById('le-age').value = ageInYears;

                    // Show success notification
                    showNotification('Life expectancy calculated successfully. Click "Apply to Evaluee" to save this value.', 'success');

                    // Show results
                    document.getElementById('life-expectancy-results').classList.remove('d-none');

                    // Set the life expectancy value in the input field
                    document.getElementById('life_expectancy').value = data.results.additionalYears.toFixed(2);
                })
                .catch(error => {
                    showNotification(`Error fetching life expectancy: ${error}`, 'danger');
                });
        });
    }

    // Auto-save functionality (every 30 seconds)
    let autoSaveTimer;
    const autoSaveInterval = 30000; // 30 seconds

    const startAutoSave = () => {
        autoSaveTimer = setInterval(() => {
            const formData = new FormData(form);

            // Only auto-save if form is valid and has been modified
            if (form.checkValidity() && form.dataset.modified === 'true') {
                fetch(form.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        showNotification('Form auto-saved', 'info', 2000);
                        form.dataset.modified = 'false';
                    }
                })
                .catch(error => {
                    console.error('Auto-save error:', error);
                });
            }
        }, autoSaveInterval);
    };

    // Track form modifications
    if (form) {
        form.dataset.modified = 'false';

        const formInputs = form.querySelectorAll('input, select, textarea');
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                form.dataset.modified = 'true';
            });
        });

        // Start auto-save
        startAutoSave();
    }

    // Helper function to show notifications
    function showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
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
        container.appendChild(notification);
        document.body.appendChild(container);

        // Auto-remove after duration
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (container.parentNode) {
                    document.body.removeChild(container);
                }
            }, 500);
        }, duration);
    }
});