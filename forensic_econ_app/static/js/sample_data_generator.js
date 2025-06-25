/**
 * Sample Data Generator
 * 
 * This script provides functionality to generate sample data for testing purposes
 * across different modules of the Economic Analysis application.
 */

/**
 * Generate a random number between min and max (inclusive)
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {boolean} isInteger - Whether to return an integer
 * @returns {number} Random number
 */
function randomNumber(min, max, isInteger = true) {
    const value = Math.random() * (max - min) + min;
    return isInteger ? Math.floor(value) : value;
}

/**
 * Format a number as currency
 * @param {number} value - Number to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(value);
}

/**
 * Format a date as YYYY-MM-DD
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Generate a random date within a range
 * @param {number} startYear - Start year
 * @param {number} endYear - End year
 * @returns {Date} Random date
 */
function randomDate(startYear, endYear) {
    const year = randomNumber(startYear, endYear);
    const month = randomNumber(0, 11);
    const day = randomNumber(1, 28);
    return new Date(year, month, day);
}

/**
 * Show a notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, info, warning, danger)
 */
function showSampleDataNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'info' ? 'info-circle' : 'exclamation-circle'} me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" aria-label="Close"></button>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add close button functionality
    notification.querySelector('.btn-close').addEventListener('click', function() {
        document.body.removeChild(notification);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}

/**
 * Generate sample data for household services
 */
function generateSampleHouseholdData() {
    // Check if we're on the household services form page
    const scenarioNameInput = document.getElementById('scenario_name');
    if (!scenarioNameInput) return;
    
    // Generate a random scenario name
    const scenarioNames = [
        'Standard Household Services',
        'Comprehensive Home Care',
        'Basic Household Assistance',
        'Full Domestic Services',
        'Limited Household Support'
    ];
    scenarioNameInput.value = scenarioNames[randomNumber(0, scenarioNames.length - 1)];
    
    // Set area wage adjustment (90% to 130%)
    const areaWageAdjustment = document.getElementById('area_wage_adjustment');
    if (areaWageAdjustment) {
        areaWageAdjustment.value = (90 + randomNumber(0, 40)).toFixed(1);
    }
    
    // Set reduction percentage (30% to 80%)
    const reductionPercentage = document.getElementById('reduction_percentage');
    if (reductionPercentage) {
        reductionPercentage.value = (30 + randomNumber(0, 50)).toFixed(1);
    }
    
    // Set growth rate (2% to 5%)
    const growthRate = document.getElementById('growth_rate');
    if (growthRate) {
        growthRate.value = (2 + randomNumber(0, 30) / 10).toFixed(1);
    }
    
    // Set discount rate (3% to 6%)
    const discountRate = document.getElementById('discount_rate');
    if (discountRate) {
        discountRate.value = (3 + randomNumber(0, 30) / 10).toFixed(1);
    }
    
    showSampleDataNotification('Sample household services data generated. Click "Create Scenario" to save.');
}

/**
 * Generate sample data for household services stages
 */
function generateSampleHouseholdStages() {
    // Check if we're on the stages page
    const stageNumberInput = document.getElementById('stage_number');
    const yearsInput = document.getElementById('years');
    const annualValueInput = document.getElementById('annual_value');
    
    if (!stageNumberInput || !yearsInput || !annualValueInput) return;
    
    // Set stage number (should already be set correctly)
    
    // Set years (3 to 15)
    yearsInput.value = randomNumber(3, 15);
    
    // Set annual value ($10,000 to $50,000)
    annualValueInput.value = randomNumber(10000, 50000);
    
    showSampleDataNotification('Sample stage data generated. Click "Add Stage" to save.');
}

/**
 * Generate sample data for demographics
 */
function generateSampleDemographicsData() {
    // Check if we're on the demographics page
    const dateOfBirthInput = document.getElementById('date_of_birth');
    if (!dateOfBirthInput) return;
    
    // Generate date of birth (25 to 55 years ago)
    const currentYear = new Date().getFullYear();
    const dob = randomDate(currentYear - 55, currentYear - 25);
    dateOfBirthInput.value = formatDate(dob);
    
    // Generate date of injury (1 to 5 years ago)
    const dateOfInjuryInput = document.getElementById('date_of_injury');
    if (dateOfInjuryInput) {
        const doi = randomDate(currentYear - 5, currentYear - 1);
        dateOfInjuryInput.value = formatDate(doi);
    }
    
    // Set gender
    const genderSelect = document.getElementById('gender');
    if (genderSelect) {
        const genders = ['Men', 'Women'];
        genderSelect.value = genders[randomNumber(0, 1)];
    }
    
    // Set education level
    const educationSelect = document.getElementById('education_level');
    if (educationSelect) {
        const educationLevels = [
            'Less than High School',
            'High School',
            'Some College',
            'Associate\'s Degree',
            'Bachelor\'s Degree',
            'Master\'s Degree',
            'Doctoral Degree',
            'Professional Degree'
        ];
        educationSelect.value = educationLevels[randomNumber(0, educationLevels.length - 1)];
    }
    
    // Set race
    const raceSelect = document.getElementById('race');
    if (raceSelect) {
        const races = ['White', 'Black', 'Hispanic', 'N/A'];
        raceSelect.value = races[randomNumber(0, races.length - 1)];
    }
    
    showSampleDataNotification('Sample demographics data generated. Click "Save Demographics" to save.');
}

/**
 * Generate sample data for earnings
 */
function generateSampleEarningsData() {
    // Check if we're on the earnings page
    const scenarioNameInput = document.querySelector('input[name="scenario_name"]');
    if (!scenarioNameInput || !document.querySelector('input[name="base_earnings"]')) return;
    
    // Generate a random scenario name
    const scenarioNames = [
        'Standard Earnings',
        'Pre-Injury Earnings',
        'Post-Injury Earnings',
        'Alternative Career Path',
        'Reduced Capacity Earnings'
    ];
    scenarioNameInput.value = scenarioNames[randomNumber(0, scenarioNames.length - 1)];
    
    // Set base earnings ($40,000 to $120,000)
    const baseEarningsInput = document.querySelector('input[name="base_earnings"]');
    if (baseEarningsInput) {
        baseEarningsInput.value = randomNumber(40000, 120000);
    }
    
    // Set growth rate (2% to 5%)
    const growthRateInput = document.querySelector('input[name="growth_rate"]');
    if (growthRateInput) {
        growthRateInput.value = (2 + randomNumber(0, 30) / 10).toFixed(1);
    }
    
    // Set discount rate (3% to 6%)
    const discountRateInput = document.querySelector('input[name="discount_rate"]');
    if (discountRateInput) {
        discountRateInput.value = (3 + randomNumber(0, 30) / 10).toFixed(1);
    }
    
    // Set fringe benefits rate (15% to 35%)
    const fringeRateInput = document.querySelector('input[name="fringe_benefits_rate"]');
    if (fringeRateInput) {
        fringeRateInput.value = (15 + randomNumber(0, 20)).toFixed(1);
    }
    
    showSampleDataNotification('Sample earnings data generated. Click "Create Scenario" to save.');
}

/**
 * Generate sample data for healthcare
 */
function generateSampleHealthcareData() {
    // Check if we're on the healthcare page
    const scenarioNameInput = document.querySelector('input[name="scenario_name"]');
    if (!scenarioNameInput || !document.querySelector('select[name="category_id"]')) return;
    
    // Generate a random scenario name
    const scenarioNames = [
        'Standard Healthcare',
        'Comprehensive Medical Care',
        'Basic Medical Needs',
        'Specialized Treatment',
        'Ongoing Therapy'
    ];
    scenarioNameInput.value = scenarioNames[randomNumber(0, scenarioNames.length - 1)];
    
    // Set category (random selection)
    const categorySelect = document.querySelector('select[name="category_id"]');
    if (categorySelect && categorySelect.options.length > 1) {
        const validOptions = Array.from(categorySelect.options)
            .filter(option => option.value && option.value !== '');
        
        if (validOptions.length > 0) {
            const randomIndex = randomNumber(0, validOptions.length - 1);
            categorySelect.value = validOptions[randomIndex].value;
        }
    }
    
    // Set annual cost ($5,000 to $50,000)
    const annualCostInput = document.querySelector('input[name="annual_cost"]');
    if (annualCostInput) {
        annualCostInput.value = randomNumber(5000, 50000);
    }
    
    // Set growth rate (3% to 8%)
    const growthRateInput = document.querySelector('input[name="growth_rate"]');
    if (growthRateInput) {
        growthRateInput.value = (3 + randomNumber(0, 50) / 10).toFixed(1);
    }
    
    // Set discount rate (3% to 6%)
    const discountRateInput = document.querySelector('input[name="discount_rate"]');
    if (discountRateInput) {
        discountRateInput.value = (3 + randomNumber(0, 30) / 10).toFixed(1);
    }
    
    // Set years (5 to 40)
    const yearsInput = document.querySelector('input[name="years"]');
    if (yearsInput) {
        yearsInput.value = randomNumber(5, 40);
    }
    
    showSampleDataNotification('Sample healthcare data generated. Click "Create Scenario" to save.');
}

/**
 * Initialize sample data buttons on document load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Determine which page we're on and add the appropriate button
    const pageType = determinePageType();
    if (!pageType) return;
    
    // Create the sample data button
    createSampleDataButton(pageType);
});

/**
 * Determine which type of page we're on
 * @returns {string|null} Page type or null if not recognized
 */
function determinePageType() {
    // Check for household services form
    if (document.getElementById('scenario_name') && 
        document.getElementById('area_wage_adjustment') && 
        document.getElementById('reduction_percentage')) {
        return 'household';
    }
    
    // Check for household stages form
    if (document.getElementById('stage_number') && 
        document.getElementById('years') && 
        document.getElementById('annual_value')) {
        return 'household-stages';
    }
    
    // Check for demographics form
    if (document.getElementById('date_of_birth') && 
        document.getElementById('date_of_injury') && 
        document.getElementById('gender')) {
        return 'demographics';
    }
    
    // Check for earnings form
    if (document.querySelector('input[name="scenario_name"]') && 
        document.querySelector('input[name="base_earnings"]')) {
        return 'earnings';
    }
    
    // Check for healthcare form
    if (document.querySelector('input[name="scenario_name"]') && 
        document.querySelector('select[name="category_id"]')) {
        return 'healthcare';
    }
    
    return null;
}

/**
 * Create a sample data button for the specified page type
 * @param {string} pageType - Type of page
 */
function createSampleDataButton(pageType) {
    // Create the button
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-outline-info';
    button.innerHTML = '<i class="fas fa-magic me-2"></i> Generate Sample Data';
    
    // Set the click handler based on page type
    switch (pageType) {
        case 'household':
            button.addEventListener('click', generateSampleHouseholdData);
            break;
        case 'household-stages':
            button.addEventListener('click', generateSampleHouseholdStages);
            break;
        case 'demographics':
            button.addEventListener('click', generateSampleDemographicsData);
            break;
        case 'earnings':
            button.addEventListener('click', generateSampleEarningsData);
            break;
        case 'healthcare':
            button.addEventListener('click', generateSampleHealthcareData);
            break;
    }
    
    // Find the form and insert the button before the submit button
    const form = document.querySelector('form');
    if (form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mb-3';
            buttonContainer.appendChild(button);
            
            submitButton.parentNode.insertBefore(buttonContainer, submitButton);
        }
    }
}
