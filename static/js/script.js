// Office Check-In System JavaScript

// Global state management
const AppState = {
    isOnline: navigator.onLine,
    pendingActions: [],
    notifications: [],
    init() {
        this.loadPendingActions();
        this.setupEventListeners();
    },
    loadPendingActions() {
        this.pendingActions = JSON.parse(localStorage.getItem('pendingActions') || '[]');
    },
    savePendingActions() {
        localStorage.setItem('pendingActions', JSON.stringify(this.pendingActions));
    },
    addPendingAction(action) {
        this.pendingActions.push(action);
        this.savePendingActions();
    },
    removePendingAction(actionId) {
        this.pendingActions = this.pendingActions.filter(a => a.id !== actionId);
        this.savePendingActions();
    },
    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            showNotification('Back online', 'success');
            this.syncPendingActions();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            showNotification('You are offline', 'warning');
        });
    }
};

// Form handling
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!AppState.isOnline) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => data[key] = value);
            
            AppState.addPendingAction({
                id: Date.now(),
                url: this.action,
                method: this.method,
                data: data
            });
            
            showNotification('Action saved for sync', 'info');
        }
    });
});

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.notification-container') || createNotificationContainer();
    container.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);

    // Animate out
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'notification-container';
    document.body.appendChild(container);
    return container;
}

// Loading indicator
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    element.appendChild(spinner);
    return spinner;
}

function hideLoading(spinner) {
    spinner.remove();
}

// Date and time formatting
function formatDate(date) {
    return new Date(date).toLocaleDateString();
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

document.addEventListener('DOMContentLoaded', function() {
    // Password toggle functionality
    const setupPasswordToggle = function() {
        const togglePassword = document.getElementById('togglePassword');
        const passwordInput = document.getElementById('password');
        const toggleIcon = document.getElementById('toggleIcon');
        
        if (togglePassword && passwordInput && toggleIcon) {
            togglePassword.addEventListener('click', function() {
                // Toggle the password input type
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                
                // Toggle the icon and button text
                if (type === 'text') {
                    toggleIcon.classList.remove('bi-eye');
                    toggleIcon.classList.add('bi-eye-slash');
                    togglePassword.textContent = ' Hide';
                    togglePassword.prepend(toggleIcon);
                } else {
                    toggleIcon.classList.remove('bi-eye-slash');
                    toggleIcon.classList.add('bi-eye');
                    togglePassword.textContent = ' Show';
                    togglePassword.prepend(toggleIcon);
                }
            });
        }
    };
    
    // Initialize password toggle on any page that has it
    setupPasswordToggle();
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Update current time
    function updateClock() {
        const now = new Date();
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            timeElement.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }

    // If there's a clock element, update it every second
    if (document.getElementById('current-time')) {
        updateClock();
        setInterval(updateClock, 1000);
    }

    // Add confirmation for check-out button
    const checkOutBtn = document.querySelector('button[formaction*="check_out"]');
    if (checkOutBtn) {
        checkOutBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to check out?')) {
                e.preventDefault();
            }
        });
    }

    // Add date picker default value
    const datePicker = document.getElementById('date');
    if (datePicker && !datePicker.value) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        datePicker.value = `${year}-${month}-${day}`;
    }

    // Add current time display to dashboard
    const dashboardHeader = document.querySelector('.card-header h4');
    if (dashboardHeader && dashboardHeader.textContent.includes('Welcome')) {
        const timeSpan = document.createElement('span');
        timeSpan.id = 'current-time';
        timeSpan.className = 'float-end badge bg-light text-dark';
        dashboardHeader.parentNode.appendChild(timeSpan);
        updateClock();
        setInterval(updateClock, 1000);
    }

    // Initialize app
    AppState.init();
    
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('Service Worker registered');
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
            });
    }
    
    // Auto-refresh status (every 5 minutes if online and page is visible)
    setInterval(() => {
        if (AppState.isOnline && !document.hidden) {
            window.location.reload();
        }
    }, 300000);
});