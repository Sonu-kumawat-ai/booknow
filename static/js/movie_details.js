// Movie Details page functionality

// Set movie backdrop dynamically (to avoid inline styles)
document.addEventListener('DOMContentLoaded', function() {
    const backdrop = document.querySelector('.movie-backdrop');
    if (backdrop && backdrop.dataset.poster) {
        backdrop.style.backgroundImage = `linear-gradient(to bottom, rgba(43, 45, 66, 0.95), rgba(43, 45, 66, 0.98)), url('${backdrop.dataset.poster}')`;
    }
});

// Show showtime selection modal
function showTimesModal(button) {
    const theatreName = button.dataset.theatreName;
    const showtimes = JSON.parse(button.dataset.showtimes);
    
    const modal = document.getElementById('showtimeModal');
    const modalTitle = document.getElementById('modalTheatreName');
    const container = document.getElementById('showtimesContainer');
    
    // Set theatre name
    modalTitle.textContent = `Select Showtime - ${theatreName}`;
    
    // Clear previous showtimes
    container.innerHTML = '';
    
    // Group showtimes by date
    const showtimesByDate = {};
    showtimes.forEach(showtime => {
        if (!showtimesByDate[showtime.show_date]) {
            showtimesByDate[showtime.show_date] = [];
        }
        showtimesByDate[showtime.show_date].push(showtime);
    });
    
    // Create showtime cards grouped by date
    Object.keys(showtimesByDate).sort().forEach(date => {
        const dateSection = document.createElement('div');
        dateSection.className = 'showtime-date-section';
        
        const dateHeader = document.createElement('h4');
        dateHeader.className = 'showtime-date-header';
        dateHeader.textContent = `📅 ${formatDate(date)}`;
        dateSection.appendChild(dateHeader);
        
        const timesGrid = document.createElement('div');
        timesGrid.className = 'showtime-times-grid';
        
        showtimesByDate[date].forEach(showtime => {
            const timeCard = document.createElement('div');
            timeCard.className = 'showtime-time-card';
            timeCard.innerHTML = `
                <div class="showtime-time">⏰ ${showtime.show_time}</div>
                <div class="showtime-details">
                    <span>💰 ₹${showtime.ticket_price}</span>
                    <span>🪑 ${showtime.available_seats} seats</span>
                </div>
                <button class="btn btn-primary btn-sm" onclick="selectShowtime('${showtime._id}')">Book Now</button>
            `;
            timesGrid.appendChild(timeCard);
        });
        
        dateSection.appendChild(timesGrid);
        container.appendChild(dateSection);
    });
    
    // Show modal
    modal.style.display = 'flex';
}

// Close modal
function closeModal() {
    const modal = document.getElementById('showtimeModal');
    modal.style.display = 'none';
}

// Select showtime and redirect to booking
function selectShowtime(showtimeId) {
    window.location.href = `/book-seats/${showtimeId}`;
}

// Format date for display
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('showtimeModal');
    if (event.target === modal) {
        closeModal();
    }
}

console.log('Movie details page loaded! 🎥');
