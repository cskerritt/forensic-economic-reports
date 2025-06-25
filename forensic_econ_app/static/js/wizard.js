/**
 * Evaluation Wizard - Handles step-by-step navigation through the evaluation process
 */

class EvaluationWizard {
    constructor(options = {}) {
        this.currentStep = 0;
        this.steps = document.querySelectorAll('.wizard-step');
        this.progressBar = document.querySelector('.wizard-progress-bar');
        this.nextButton = document.querySelector('.wizard-next');
        this.prevButton = document.querySelector('.wizard-prev');
        this.stepIndicators = document.querySelectorAll('.wizard-step-indicator');
        this.formData = {};
        this.options = {
            autoSave: true,
            validateOnNext: true,
            ...options
        };

        this.init();
    }

    init() {
        // Hide all steps except the first one
        this.steps.forEach((step, index) => {
            step.classList.remove('active');
            if (index === 0) {
                step.classList.add('active');
            }
        });

        // Update progress indicators
        this.updateProgress();

        // Add event listeners
        if (this.nextButton) {
            this.nextButton.addEventListener('click', () => this.nextStep());
        }

        if (this.prevButton) {
            this.prevButton.addEventListener('click', () => this.prevStep());
        }

        // Add click event to step indicators
        this.stepIndicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                if (this.canNavigateToStep(index)) {
                    this.goToStep(index);
                }
            });
        });

        // Set up auto-save if enabled
        if (this.options.autoSave) {
            this.setupAutoSave();
        }
    }

    updateProgress() {
        // Update progress bar
        if (this.progressBar) {
            const progress = ((this.currentStep + 1) / this.steps.length) * 100;
            this.progressBar.style.width = `${progress}%`;
            this.progressBar.setAttribute('aria-valuenow', progress);
        }

        // Update step indicators
        this.stepIndicators.forEach((indicator, index) => {
            indicator.classList.remove('active', 'completed');

            if (index < this.currentStep) {
                indicator.classList.add('completed');
            } else if (index === this.currentStep) {
                indicator.classList.add('active');
            }
        });

        // Update button states
        if (this.prevButton) {
            this.prevButton.disabled = this.currentStep === 0;
        }

        if (this.nextButton) {
            if (this.currentStep === this.steps.length - 1) {
                this.nextButton.textContent = 'Finish';
            } else {
                this.nextButton.textContent = 'Next';
            }
        }
    }

    validateCurrentStep() {
        if (!this.options.validateOnNext) {
            return true;
        }

        const currentStepElement = this.steps[this.currentStep];
        const requiredInputs = currentStepElement.querySelectorAll('[required]');
        let isValid = true;

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        // Check for custom validation
        const customValidation = currentStepElement.getAttribute('data-validate');
        if (customValidation && window[customValidation]) {
            const customResult = window[customValidation]();
            isValid = isValid && customResult;
        }

        return isValid;
    }

    collectFormData() {
        const currentStepElement = this.steps[this.currentStep];
        const formElements = currentStepElement.querySelectorAll('input, select, textarea');

        formElements.forEach(element => {
            if (element.name) {
                if (element.type === 'checkbox') {
                    this.formData[element.name] = element.checked;
                } else if (element.type === 'radio') {
                    if (element.checked) {
                        this.formData[element.name] = element.value;
                    }
                } else {
                    this.formData[element.name] = element.value;
                }
            }
        });
    }

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            if (this.validateCurrentStep()) {
                this.collectFormData();

                if (this.options.autoSave) {
                    this.saveFormData();
                }

                this.steps[this.currentStep].classList.remove('active');
                this.currentStep++;
                this.steps[this.currentStep].classList.add('active');
                this.updateProgress();

                // Scroll to top of the step
                window.scrollTo(0, 0);
            }
        } else {
            // On the last step, finish the wizard
            if (this.validateCurrentStep()) {
                this.collectFormData();
                this.finishWizard();
            }
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.collectFormData();

            this.steps[this.currentStep].classList.remove('active');
            this.currentStep--;
            this.steps[this.currentStep].classList.add('active');
            this.updateProgress();

            // Scroll to top of the step
            window.scrollTo(0, 0);
        }
    }

    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.steps.length) {
            this.collectFormData();

            this.steps[this.currentStep].classList.remove('active');
            this.currentStep = stepIndex;
            this.steps[this.currentStep].classList.add('active');
            this.updateProgress();

            // Scroll to top of the step
            window.scrollTo(0, 0);
        }
    }

    canNavigateToStep(stepIndex) {
        // Allow navigation to any step
        return true;
    }

    setupAutoSave() {
        // Set up auto-save on form field changes
        this.steps.forEach(step => {
            const formElements = step.querySelectorAll('input, select, textarea');

            formElements.forEach(element => {
                element.addEventListener('change', () => {
                    this.collectFormData();
                    this.saveFormData();
                });
            });
        });
    }

    saveFormData() {
        // Save form data to server
        const evalueeId = document.querySelector('[name="evaluee_id"]').value;

        fetch(`/api/evaluee/${evalueeId}/autosave`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                step: this.currentStep,
                data: this.formData
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showSavedIndicator();
            }
        })
        .catch(error => {
            console.error('Error saving form data:', error);
        });
    }

    showSavedIndicator() {
        const savedIndicator = document.querySelector('.autosave-indicator');
        if (savedIndicator) {
            savedIndicator.textContent = 'Changes saved';
            savedIndicator.style.opacity = '1';

            setTimeout(() => {
                savedIndicator.style.opacity = '0';
            }, 2000);
        }
    }

    finishWizard() {
        // Submit the final form
        const form = document.querySelector('.wizard-form');
        if (form) {
            // Populate hidden fields with collected data
            for (const [key, value] of Object.entries(this.formData)) {
                let hiddenField = form.querySelector(`input[type="hidden"][name="${key}"]`);
                if (!hiddenField) {
                    hiddenField = document.createElement('input');
                    hiddenField.type = 'hidden';
                    hiddenField.name = key;
                    form.appendChild(hiddenField);
                }
                hiddenField.value = value;
            }

            form.submit();
        }
    }
}

// Initialize the wizard when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const wizardContainer = document.querySelector('.wizard-container');
    if (wizardContainer) {
        const wizard = new EvaluationWizard({
            autoSave: wizardContainer.getAttribute('data-autosave') !== 'false',
            validateOnNext: wizardContainer.getAttribute('data-validate') !== 'false'
        });

        // Make wizard accessible globally
        window.evaluationWizard = wizard;
    }
});
