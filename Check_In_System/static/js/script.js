// Office Check-In System JavaScript

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
});