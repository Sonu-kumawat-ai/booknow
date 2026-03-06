// Theatre Dashboard functionality

// Create tooltip element
const tooltip = document.createElement('div');
tooltip.className = 'show-tooltip';
tooltip.style.display = 'none';
document.body.appendChild(tooltip);

// Add hover functionality to show rows
document.addEventListener('DOMContentLoaded', function() {
    const showRows = document.querySelectorAll('.show-row');
    
    showRows.forEach(row => {
        row.addEventListener('mouseenter', function(e) {
            const revenue = this.dataset.revenue;
            const bookedSeats = this.dataset.bookedSeats;
            const totalBookings = this.dataset.totalBookings;
            const capacity = this.dataset.capacity;
            const movie = this.dataset.movie;
            const date = this.dataset.date;
            const time = this.dataset.time;
            
            const occupancy = capacity > 0 ? ((bookedSeats / capacity) * 100).toFixed(1) : 0;
            
            tooltip.innerHTML = `
                <div class="tooltip-header">
                    <strong>${movie}</strong>
                </div>
                <div class="tooltip-body">
                    <div class="tooltip-item">
                        <span class="tooltip-label">📅 Date & Time:</span>
                        <span class="tooltip-value">${date} at ${time}</span>
                    </div>
                    <div class="tooltip-item">
                        <span class="tooltip-label">💰 Revenue:</span>
                        <span class="tooltip-value">₹${parseFloat(revenue).toLocaleString('en-IN')}</span>
                    </div>
                    <div class="tooltip-item">
                        <span class="tooltip-label">🎟️ Total Bookings:</span>
                        <span class="tooltip-value">${totalBookings}</span>
                    </div>
                    <div class="tooltip-item">
                        <span class="tooltip-label">💺 Seats Booked:</span>
                        <span class="tooltip-value">${bookedSeats} / ${capacity}</span>
                    </div>
                    <div class="tooltip-item">
                        <span class="tooltip-label">📊 Occupancy:</span>
                        <span class="tooltip-value">${occupancy}%</span>
                    </div>
                </div>
            `;
            
            tooltip.style.display = 'block';
            positionTooltip(e);
        });
        
        row.addEventListener('mousemove', function(e) {
            positionTooltip(e);
        });
        
        row.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });
    });
});

function positionTooltip(e) {
    const tooltipWidth = tooltip.offsetWidth;
    const tooltipHeight = tooltip.offsetHeight;
    const padding = 15;
    
    let left = e.pageX + padding;
    let top = e.pageY + padding;
    
    // Keep tooltip within viewport
    if (left + tooltipWidth > window.innerWidth + window.scrollX) {
        left = e.pageX - tooltipWidth - padding;
    }
    
    if (top + tooltipHeight > window.innerHeight + window.scrollY) {
        top = e.pageY - tooltipHeight - padding;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

// Delete showtime function
function deleteShowtime(showtimeId, movieTitle) {
    if (!confirm(`Are you sure you want to delete the showtime for "${movieTitle}"?\n\nThis will remove the showtime and all related bookings and reviews.`)) {
        return;
    }
    fetch(`/delete-showtime/${showtimeId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message || 'Showtime deleted successfully!');
            window.location.reload();
        } else {
            alert(data.message || 'Failed to delete showtime');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the showtime');
    });
}

// Edit movie function (placeholder for now - will redirect to add movie page with edit mode)
function editMovie(movieId) {
    // For now, just show alert that feature is coming
    alert('Edit functionality coming soon!\n\nFor now, you can delete and re-add the movie with updated information.');
}

console.log('Theatre dashboard loaded! 🎭');

// Theatre Offers Management
(function() {
    'use strict';
    
    // Load offers when page loads
    document.addEventListener('DOMContentLoaded', function() {
        loadTheatreOffers();
    });
    
    function loadTheatreOffers() {
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
                displayTheatreOffers(data.offers);
            } else {
                showTheatreError(data.message || 'Failed to load offers');
            }
        })
        .catch(error => {
            console.error('Error loading offers:', error);
            showTheatreError('Unable to load offers. Please refresh the page.');
        });
    }
    
    function displayTheatreOffers(offers) {
        const container = document.getElementById('offersContainer');
        
        if (!offers || offers.length === 0) {
            container.innerHTML = `
                <div class="empty-offers">
                    <div class="icon">🎁</div>
                    <h4>No Offers Created Yet</h4>
                    <p>Start creating promotional offers to attract more customers to your theatre!</p>
                </div>
            `;
            return;
        }
        
        const offersHTML = offers.map(offer => createTheatreOfferCard(offer)).join('');
        container.innerHTML = offersHTML;
    }
    
    function createTheatreOfferCard(offer) {
        const isActive = offer.status === 'active';
        const discount = offer.discount_type === 'percentage' 
            ? `${offer.discount_value}% OFF` 
            : `₹${offer.discount_value} OFF`;
        
        const movieInfo = offer.movie_name 
            ? `Movie: ${offer.movie_name}` 
            : offer.movie_names 
                ? `Movies: ${offer.movie_names}` 
                : 'All Movies';
        
        const usageText = offer.usage_limit > 0 
            ? `${offer.usage_count} / ${offer.usage_limit}` 
            : offer.usage_count;
        
        return `
            <div class="theatre-offer-card ${isActive ? '' : 'inactive'}">
                <div class="theatre-offer-header">
                    <span class="theatre-offer-code">${escapeHtml(offer.code)}</span>
                    <span class="theatre-offer-badge ${isActive ? 'active' : 'inactive'}">
                        ${isActive ? '✓ Active' : '✗ Inactive'}
                    </span>
                </div>
                
                <div class="theatre-offer-description">
                    ${escapeHtml(offer.description)}
                </div>
                
                <div class="theatre-offer-details">
                    <div class="theatre-offer-detail-item">
                        <span class="theatre-offer-detail-label">Discount</span>
                        <span class="theatre-offer-detail-value">${discount}</span>
                    </div>
                    ${offer.min_purchase > 0 ? `
                    <div class="theatre-offer-detail-item">
                        <span class="theatre-offer-detail-label">Min Purchase</span>
                        <span class="theatre-offer-detail-value">₹${offer.min_purchase}</span>
                    </div>
                    ` : ''}
                    ${offer.max_discount > 0 ? `
                    <div class="theatre-offer-detail-item">
                        <span class="theatre-offer-detail-label">Max Discount</span>
                        <span class="theatre-offer-detail-value">₹${offer.max_discount}</span>
                    </div>
                    ` : ''}
                    <div class="theatre-offer-detail-item">
                        <span class="theatre-offer-detail-label">Usage Count</span>
                        <span class="theatre-offer-detail-value">${usageText}</span>
                    </div>
                </div>
                
                <div class="theatre-offer-meta">
                    <div class="theatre-offer-meta-item">
                        <span>📅</span>
                        <span>Valid: ${offer.valid_from} to ${offer.valid_until}</span>
                    </div>
                    <div class="theatre-offer-meta-item">
                        <span>🎬</span>
                        <span>${movieInfo}</span>
                    </div>
                </div>
                
                <div class="theatre-offer-actions">
                    <button class="theatre-btn-toggle ${isActive ? '' : 'activate'}" 
                            onclick="toggleTheatreOfferStatus('${offer._id}')">
                        ${isActive ? '⏸️ Deactivate' : '▶️ Activate'}
                    </button>
                    <button class="theatre-btn-delete" onclick="deleteTheatreOffer('${offer._id}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    }
    
    function showTheatreError(message) {
        const container = document.getElementById('offersContainer');
        container.innerHTML = `
            <div class="error-state">
                <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                <h4>Error Loading Offers</h4>
                <p>${escapeHtml(message)}</p>
                <button onclick="loadTheatreOffers()" style="margin-top: 15px; padding: 10px 20px; background: var(--primary-red, #e50914); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    🔄 Try Again
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
    window.loadTheatreOffers = loadTheatreOffers;
    
    window.toggleTheatreOfferStatus = function(offerId) {
        fetch(`/toggle-offer-status/${offerId}`, {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadTheatreOffers();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to toggle offer status. Please try again.');
        });
    };
    
    window.deleteTheatreOffer = function(offerId) {
        if (!confirm('Are you sure you want to delete this offer?\n\nThis action cannot be undone.')) {
            return;
        }
        
        fetch(`/delete-offer/${offerId}`, {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadTheatreOffers();
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
