// Admin Dashboard functionality

// Admin-specific features like approve/reject requests
// Statistics management, etc.

console.log('Admin dashboard loaded! 👨‍💼');

// Offers Management
(function() {
    'use strict';
    
    // Load offers when page loads
    document.addEventListener('DOMContentLoaded', function() {
        loadOffers();
    });
    
    function loadOffers() {
        const container = document.getElementById('offersContainer');
        if (!container) return; // Exit if offers container doesn't exist on this page
        
        fetch('/get-offers', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayOffers(data.offers);
            } else {
                showError(data.message || 'Failed to load offers');
            }
        })
        .catch(error => {
            console.error('Error loading offers:', error);
            showError('Unable to load offers. Please refresh the page.');
        });
    }
    
    function displayOffers(offers) {
        const container = document.getElementById('offersContainer');
        
        if (!offers || offers.length === 0) {
            container.innerHTML = `
                <div class="empty-offers">
                    <div class="icon">🎁</div>
                    <h4>No Offers Yet</h4>
                    <p>Create your first offer to start attracting more customers!</p>
                </div>
            `;
            return;
        }
        
        const offersHTML = offers.map(offer => createOfferCard(offer)).join('');
        container.innerHTML = offersHTML;
    }
    
    function createOfferCard(offer) {
        const isActive = offer.status === 'active';
        const discount = offer.discount_type === 'percentage' 
            ? `${offer.discount_value}% OFF` 
            : `₹${offer.discount_value} OFF`;
        
        const applicableTo = getApplicableText(offer);
        const usageText = offer.usage_limit > 0 
            ? `${offer.usage_count}/${offer.usage_limit}` 
            : offer.usage_count;
        
        return `
            <div class="offer-card ${isActive ? '' : 'inactive'}">
                <div class="offer-header">
                    <span class="offer-code">${escapeHtml(offer.code)}</span>
                    <span class="offer-badge ${isActive ? 'active' : 'inactive'}">
                        ${isActive ? '✓ Active' : '✗ Inactive'}
                    </span>
                </div>
                
                <div class="offer-description">
                    ${escapeHtml(offer.description)}
                </div>
                
                <div class="offer-details">
                    <div class="offer-detail-item">
                        <span class="offer-detail-label">Discount:</span>
                        <span class="offer-detail-value">${discount}</span>
                    </div>
                    ${offer.min_purchase > 0 ? `
                    <div class="offer-detail-item">
                        <span class="offer-detail-label">Min Purchase:</span>
                        <span class="offer-detail-value">₹${offer.min_purchase}</span>
                    </div>
                    ` : ''}
                    ${offer.max_discount > 0 ? `
                    <div class="offer-detail-item">
                        <span class="offer-detail-label">Max Discount:</span>
                        <span class="offer-detail-value">₹${offer.max_discount}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="offer-meta">
                    <span>📅 Valid: ${offer.valid_from} to ${offer.valid_until}</span>
                    <span>📊 Used: ${usageText} times</span>
                    <span>🎯 ${applicableTo}</span>
                </div>
                
                <div class="offer-actions">
                    <button class="btn-toggle ${isActive ? '' : 'activate'}" 
                            onclick="toggleOfferStatus('${offer._id}')">
                        ${isActive ? '⏸ Deactivate' : '▶ Activate'}
                    </button>
                    <button class="btn-delete" onclick="deleteOffer('${offer._id}')">
                        🗑 Delete
                    </button>
                </div>
            </div>
        `;
    }
    
    function getApplicableText(offer) {
        if (offer.applicable_to === 'all') return 'All bookings';
        if (offer.theatre_name) return `Theatre: ${offer.theatre_name}`;
        if (offer.theatre_names) return `Theatres: ${offer.theatre_names}`;
        if (offer.movie_name) return `Movie: ${offer.movie_name}`;
        if (offer.movie_names) return `Movies: ${offer.movie_names}`;
        return 'Specific conditions';
    }
    
    function showError(message) {
        const container = document.getElementById('offersContainer');
        container.innerHTML = `
            <div class="error-state">
                <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                <h4>Error Loading Offers</h4>
                <p>${escapeHtml(message)}</p>
                <button onclick="loadOffers()" style="margin-top: 15px; padding: 10px 20px; background: var(--primary-red, #e50914); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Try Again
                </button>
            </div>
        `;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Make functions globally available
    window.loadOffers = loadOffers;
    
    window.toggleOfferStatus = function(offerId) {
        fetch(`/toggle-offer-status/${offerId}`, {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadOffers();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to toggle offer status. Please try again.');
        });
    };
    
    window.deleteOffer = function(offerId) {
        if (!confirm('Are you sure you want to delete this offer? This action cannot be undone.')) {
            return;
        }
        
        fetch(`/delete-offer/${offerId}`, {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadOffers();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete offer. Please try again.');
        });
    };
})();
