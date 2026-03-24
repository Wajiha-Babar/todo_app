// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize task checkboxes for AJAX toggling
    initializeTaskCheckboxes();
    
    // Load statistics
    loadStatistics();
    
    // Auto-refresh statistics every 30 seconds
    setInterval(loadStatistics, 30000);
});

// Initialize task checkboxes
function initializeTaskCheckboxes() {
    const checkboxes = document.querySelectorAll('.task-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskId = this.dataset.taskId;
            if (taskId) {
                toggleTaskStatus(taskId, this.checked);
            }
        });
    });
}

// Toggle task status via AJAX
function toggleTaskStatus(taskId, completed) {
    fetch(`/toggle/${taskId}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // Reload page to refresh the view
            window.location.reload();
        } else {
            showNotification('Error updating task', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating task', 'error');
    });
}

// Load statistics via AJAX
function loadStatistics() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            // Update stats display
            const totalElem = document.getElementById('totalTasks');
            const completedElem = document.getElementById('completedTasks');
            const pendingElem = document.getElementById('pendingTasks');
            const highPriorityElem = document.getElementById('highPriority');
            
            if (totalElem) totalElem.textContent = data.total;
            if (completedElem) completedElem.textContent = data.completed;
            if (pendingElem) pendingElem.textContent = data.pending;
            if (highPriorityElem) highPriorityElem.textContent = data.high_priority;
            
            // Update chart if exists
            updateStatsChart(data);
        })
        .catch(error => {
            console.error('Error loading statistics:', error);
        });
}

// Update statistics chart
let statsChart = null;

function updateStatsChart(data) {
    const ctx = document.getElementById('statsChart');
    if (!ctx) return;
    
    if (statsChart) {
        statsChart.destroy();
    }
    
    statsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Pending'],
            datasets: [{
                data: [data.completed, data.pending],
                backgroundColor: ['#10b981', '#f59e0b'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = data.completed + data.pending;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.animation = 'slideInRight 0.5s ease';
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 type === 'info' ? 'info-circle' : 'bell';
    
    notification.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification && notification.remove) {
            notification.remove();
        }
    }, 3000);
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Form validation for add/edit pages
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        const titleInput = this.querySelector('#title');
        if (titleInput && (!titleInput.value || titleInput.value.trim() === '')) {
            e.preventDefault();
            showNotification('Please enter a task title', 'error');
            titleInput.focus();
        }
    });
});

// Add date input min attribute to prevent past dates
const dateInputs = document.querySelectorAll('input[type="date"]');
dateInputs.forEach(dateInput => {
    if (!dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }
});