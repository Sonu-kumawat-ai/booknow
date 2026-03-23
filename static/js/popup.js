/**
 * Global Website Popup System
 * Handles modal popups, notifications, and custom alerts across the website
 */

class WebsitePopup {
    constructor() {
        this.overlay = null;
        this.container = null;
        this.isOpen = false;
        this.init();
    }

    init() {
        // Create overlay and container if they don't exist
        if (!document.getElementById('popup-overlay')) {
            this.createPopupElements();
        } else {
            this.overlay = document.getElementById('popup-overlay');
            this.container = document.querySelector('.popup-container');
        }
    }

    createPopupElements() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.id = 'popup-overlay';
        this.overlay.className = 'popup-overlay';
        document.body.appendChild(this.overlay);

        // Create container
        this.container = document.createElement('div');
        this.container.className = 'popup-container';
        this.overlay.appendChild(this.container);

        // Close on overlay click
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    open(options = {}) {
        const {
            title = 'Notification',
            icon = '📢',
            message = '',
            html = '',
            primaryBtn = 'OK',
            secondaryBtn = null,
            onPrimaryClick = null,
            onSecondaryClick = null,
            onClose = null,
            closeable = true
        } = options;

        // Build HTML content
        let content = `
            <div class="popup-header">
                <div style="display: flex; align-items: center;">
                    <span class="popup-icon">${icon}</span>
                    <h2>${this.escapeHtml(title)}</h2>
                </div>
                ${closeable ? '<button class="popup-close" aria-label="Close">×</button>' : ''}
            </div>
            <div class="popup-body">
                ${html || `<p>${this.escapeHtml(message)}</p>`}
            </div>
        `;

        // Add footer if buttons exist
        if (primaryBtn || secondaryBtn) {
            content += '<div class="popup-footer">';
            
            if (primaryBtn) {
                content += `<button class="btn popup-btn-primary" id="popupPrimaryBtn">${this.escapeHtml(primaryBtn)}</button>`;
            }
            
            if (secondaryBtn) {
                content += `<button class="btn popup-btn-secondary" id="popupSecondaryBtn">${this.escapeHtml(secondaryBtn)}</button>`;
            }
            
            content += '</div>';
        }

        this.container.innerHTML = content;

        // Attach event listeners
        const closeBtn = this.container.querySelector('.popup-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        const primaryBtn_el = this.container.querySelector('#popupPrimaryBtn');
        if (primaryBtn_el) {
            primaryBtn_el.addEventListener('click', () => {
                if (onPrimaryClick) onPrimaryClick();
                this.close();
            });
        }

        const secondaryBtn_el = this.container.querySelector('#popupSecondaryBtn');
        if (secondaryBtn_el) {
            secondaryBtn_el.addEventListener('click', () => {
                if (onSecondaryClick) onSecondaryClick();
                this.close();
            });
        }

        // Show popup
        this.overlay.classList.add('show');
        this.isOpen = true;
        document.body.style.overflow = 'hidden'; // Prevent body scroll

        this._onClose = onClose;
    }

    showAnnouncement(message, duration = 8000) {
        this.open({
            title: '📣 Announcement',
            icon: '📣',
            message: message,
            primaryBtn: 'Got it',
            closeable: true
        });

        if (duration > 0) {
            setTimeout(() => {
                if (this.isOpen) this.close();
            }, duration);
        }
    }

    showOffer(title, discount, offerText, code = null, onApply = null) {
        let html = `
            <div class="popup-offer-badge">Limited Time Offer</div>
            <h3 style="margin: 0 0 12px 0; color: var(--text-dark);">${this.escapeHtml(title)}</h3>
            <div class="popup-discount">${this.escapeHtml(discount)}% OFF</div>
            <p style="color: var(--text-dark); margin-bottom: 16px;">${this.escapeHtml(offerText)}</p>
        `;

        if (code) {
            html += `
                <div class="popup-highlight">
                    <p style="margin: 0; font-size: 12px; color: var(--text-dark);">Use Code:</p>
                    <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 700; color: var(--primary-red);">${this.escapeHtml(code)}</p>
                </div>
            `;
        }

        this.open({
            title: '🎉 Special Offer',
            icon: '🎉',
            html: html,
            primaryBtn: 'Apply Offer',
            secondaryBtn: 'Later',
            onPrimaryClick: onApply,
            closeable: true
        });
    }

    showConfirm(message, onConfirm, onCancel = null) {
        this.open({
            title: 'Confirm',
            icon: '⚠️',
            message: message,
            primaryBtn: 'Confirm',
            secondaryBtn: 'Cancel',
            onPrimaryClick: onConfirm,
            onSecondaryClick: onCancel,
            closeable: true
        });
    }

    showError(message) {
        this.open({
            title: 'Error',
            icon: '❌',
            message: message,
            primaryBtn: 'OK',
            closeable: true
        });

        setTimeout(() => {
            if (this.isOpen) this.close();
        }, 5000);
    }

    showSuccess(message) {
        this.open({
            title: 'Success',
            icon: '✅',
            message: message,
            primaryBtn: 'OK',
            closeable: true
        });

        setTimeout(() => {
            if (this.isOpen) this.close();
        }, 3000);
    }

    close() {
        if (!this.isOpen) return;

        this.overlay.classList.remove('show');
        this.isOpen = false;
        document.body.style.overflow = ''; // Restore body scroll

        if (this._onClose) {
            this._onClose();
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Toast Notification System
class ToastNotification {
    static show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = 'popup-toast show';

        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️'
        };

        toast.innerHTML = `
            <span class="popup-toast-icon ${type}">${icons[type] || icons.info}</span>
            <span class="popup-toast-message">${message}</span>
        `;

        document.body.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('show');
                toast.classList.add('hide');
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, duration);
        }

        return toast;
    }

    static success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration = 4000) {
        return this.show(message, 'error', duration);
    }

    static info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    static warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }
}

// Initialize global popup instance when DOM is ready
let websitePopup;
document.addEventListener('DOMContentLoaded', () => {
    websitePopup = new WebsitePopup();

    // Check if there's a popup to show (passed from server)
    const popupData = window.websitePopupData;
    if (popupData) {
        websitePopup.open(popupData);
    }
});

// Make globally accessible
window.showPopup = (options) => websitePopup && websitePopup.open(options);
window.showAnnouncement = (msg, duration) => websitePopup && websitePopup.showAnnouncement(msg, duration);
window.showOffer = (title, discount, text, code, callback) => websitePopup && websitePopup.showOffer(title, discount, text, code, callback);
window.showConfirm = (msg, onConfirm, onCancel) => websitePopup && websitePopup.showConfirm(msg, onConfirm, onCancel);
window.showToast = (msg, type, duration) => ToastNotification.show(msg, type, duration);
