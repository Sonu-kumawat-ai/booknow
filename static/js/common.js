// Common functionality shared across all pages

// Flash message close button (for both .close-flash and .flash-close)
document.addEventListener('DOMContentLoaded', function() {
    // Handle .close-flash buttons
    document.querySelectorAll('.close-flash').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                this.parentElement.remove();
            }, 300);
        });
    });
    
    // Handle .flash-close buttons (remove inline onclick)
    document.querySelectorAll('.flash-close').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.remove();
        });
    });
});

// Auto-hide flash messages after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(message => {
        message.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            message.remove();
        }, 300);
    });
}, 5000);

// Mobile menu toggle
const hamburger = document.querySelector('.hamburger');
const navLinksElement = document.querySelector('.nav-links');

if (hamburger && navLinksElement) {
    hamburger.addEventListener('click', () => {
        navLinksElement.classList.toggle('active');
        hamburger.classList.toggle('active');
    });
}

// Profile dropdown toggle
const profileToggle = document.getElementById('profileToggle');
const profileMenu = document.getElementById('profileMenu');

if (profileToggle && profileMenu) {
    profileToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        profileMenu.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!profileToggle.contains(e.target) && !profileMenu.contains(e.target)) {
            profileMenu.classList.remove('show');
        }
    });

    // Close dropdown when pressing Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            profileMenu.classList.remove('show');
        }
    });
}

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .nav-links.active {
        display: flex;
        flex-direction: column;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--surface);
        padding: 1rem;
        box-shadow: var(--shadow-md);
    }
    
    .hamburger.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 5px);
    }
    
    .hamburger.active span:nth-child(2) {
        opacity: 0;
    }
    
    .hamburger.active span:nth-child(3) {
        transform: rotate(-45deg) translate(7px, -6px);
    }
`;
document.head.appendChild(style);

console.log('BookNow - Common JS Loaded! 🎬');
