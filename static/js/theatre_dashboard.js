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
