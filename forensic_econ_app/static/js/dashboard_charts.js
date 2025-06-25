/**
 * Dashboard Charts and Visualizations
 * 
 * This script creates interactive charts for the dashboard using Chart.js
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Chart.js
    initializeCharts();
    
    // Set up event listeners for chart toggles
    setupChartToggles();
});

/**
 * Initialize all dashboard charts
 */
function initializeCharts() {
    // Only initialize if the charts container exists
    if (!document.getElementById('charts-container')) return;
    
    // Create evaluee status chart
    createEvalueeStatusChart();
    
    // Create scenario distribution chart
    createScenarioDistributionChart();
    
    // Create recent activity chart
    createRecentActivityChart();
}

/**
 * Create the evaluee status chart (pie chart)
 */
function createEvalueeStatusChart() {
    const ctx = document.getElementById('evaluee-status-chart');
    if (!ctx) return;
    
    // Get data from the data attributes
    const totalEvaluees = parseInt(ctx.dataset.totalEvaluees || 0);
    const completedEvaluees = parseInt(ctx.dataset.completedEvaluees || 0);
    const inProgressEvaluees = parseInt(ctx.dataset.inProgressEvaluees || 0);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress'],
            datasets: [{
                data: [completedEvaluees, inProgressEvaluees],
                backgroundColor: ['#2ecc71', '#3498db'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const percentage = Math.round((value / totalEvaluees) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create the scenario distribution chart (bar chart)
 */
function createScenarioDistributionChart() {
    const ctx = document.getElementById('scenario-distribution-chart');
    if (!ctx) return;
    
    // Get data from the data attributes
    const earningsScenarios = parseInt(ctx.dataset.earningsScenarios || 0);
    const healthcareScenarios = parseInt(ctx.dataset.healthcareScenarios || 0);
    const householdScenarios = parseInt(ctx.dataset.householdScenarios || 0);
    const fringeBenefitScenarios = parseInt(ctx.dataset.fringeBenefitScenarios || 0);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Earnings', 'Healthcare', 'Household', 'Fringe Benefits'],
            datasets: [{
                label: 'Number of Scenarios',
                data: [earningsScenarios, healthcareScenarios, householdScenarios, fringeBenefitScenarios],
                backgroundColor: ['#3498db', '#e74c3c', '#f39c12', '#9b59b6'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Create the recent activity chart (line chart)
 */
function createRecentActivityChart() {
    const ctx = document.getElementById('recent-activity-chart');
    if (!ctx) return;
    
    // Get data from the data attributes (comma-separated values)
    const dates = (ctx.dataset.dates || '').split(',');
    const counts = (ctx.dataset.counts || '').split(',').map(Number);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Activity Count',
                data: counts,
                borderColor: '#2ecc71',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Set up event listeners for chart toggles
 */
function setupChartToggles() {
    const toggleButtons = document.querySelectorAll('.chart-toggle');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const chartContainer = document.getElementById(targetId);
            
            if (chartContainer) {
                // Toggle visibility
                if (chartContainer.classList.contains('d-none')) {
                    chartContainer.classList.remove('d-none');
                    this.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Chart';
                } else {
                    chartContainer.classList.add('d-none');
                    this.innerHTML = '<i class="fas fa-chevron-down"></i> Show Chart';
                }
            }
        });
    });
}
