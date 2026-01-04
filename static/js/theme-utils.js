/**
 * Theme Utility Functions
 * Toast notifications, alerts, modals, and theme initialization
 */

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast alert alert-${type}`;
    
    // Add icon based on type
    const icons = {
        success: '✓',
        warning: '⚠',
        error: '✕',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span style="font-size: 1.25rem; font-weight: bold;">${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        toast.style.animation = 'toastSlideOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Modal alert dialog
function showAlert(title, message, type = 'info') {
    // Remove existing alert modal if any
    const existingModal = document.getElementById('alert-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'alert-modal';
    modal.className = 'modal active';
    
    const typeColors = {
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-danger)',
        info: 'var(--color-accent)'
    };
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title" style="color: ${typeColors[type] || typeColors.info}">${title}</h3>
                <button class="modal-close" onclick="closeAlertModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="color: var(--color-light); font-size: 1rem;">${message}</p>
            </div>
            <div class="modal-footer" style="margin-top: 1.5rem; text-align: right;">
                <button class="btn btn-primary" onclick="closeAlertModal()">OK</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAlertModal();
        }
    });
}

function closeAlertModal() {
    const modal = document.getElementById('alert-modal');
    if (modal) {
        modal.remove();
    }
}

// Initialize theme on page load
function initTheme() {
    console.log('Smart Traffic Management System - Theme Initialized');
    
    // Apply saved theme preference (placeholder for future light mode)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // ESC key closes modals
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });
}

// Toggle theme (placeholder for future light mode)
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    showToast(`Theme changed to ${newTheme} mode`, 'info');
}

// Show loading overlay
function showLoading() {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Confirm dialog
function showConfirm(title, message, onConfirm, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'confirm-modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" onclick="closeConfirmModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="color: var(--color-light); font-size: 1rem;">${message}</p>
            </div>
            <div class="modal-footer" style="margin-top: 1.5rem; text-align: right; display: flex; gap: 1rem; justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="closeConfirmModal(false)">Cancel</button>
                <button class="btn btn-primary" onclick="closeConfirmModal(true)">Confirm</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    window.confirmModalCallbacks = { onConfirm, onCancel };
}

function closeConfirmModal(confirmed) {
    const modal = document.getElementById('confirm-modal');
    if (modal) {
        modal.remove();
        
        if (window.confirmModalCallbacks) {
            if (confirmed && window.confirmModalCallbacks.onConfirm) {
                window.confirmModalCallbacks.onConfirm();
            } else if (!confirmed && window.confirmModalCallbacks.onCancel) {
                window.confirmModalCallbacks.onCancel();
            }
            delete window.confirmModalCallbacks;
        }
    }
}

// Format date helper
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format currency helper
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Initialize theme on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
} else {
    initTheme();
}

// Export functions for global use
window.showToast = showToast;
window.showAlert = showAlert;
window.showConfirm = showConfirm;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;
window.toggleTheme = toggleTheme;
