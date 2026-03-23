// Movie Details page functionality

// Set movie backdrop dynamically (to avoid inline styles)
document.addEventListener('DOMContentLoaded', function() {
    const backdrop = document.querySelector('.movie-backdrop');
    if (backdrop && backdrop.dataset.poster) {
        backdrop.style.backgroundImage = `linear-gradient(to bottom, rgba(43, 45, 66, 0.95), rgba(43, 45, 66, 0.98)), url('${backdrop.dataset.poster}')`;
    }
    
    // Update showtimes counts to only include future showtimes
    updateShowtimesCounts();
});

// Update the count of available showtimes (future only)
function updateShowtimesCounts() {
    const now = new Date();
    
    // Find all "View Showtimes" buttons
    document.querySelectorAll('button[onclick="showTimesModal(this)"]').forEach(button => {
        try {
            const showtimes = JSON.parse(button.dataset.showtimes);
            
            // Filter to only future showtimes
            const futureShowtimes = showtimes.filter(showtime => {
                try {
                    const showDateTime = new Date(`${showtime.show_date}T${showtime.show_time}:00`);
                    return showDateTime > now;
                } catch (e) {
                    return true;
                }
            });
            
            // Update the showtime count in the parent card
            const card = button.closest('.showtime-card');
            if (card) {
                const countElement = card.querySelector('.showtime-count');
                if (countElement) {
                    if (futureShowtimes.length === 0) {
                        countElement.textContent = '🎬 No upcoming shows';
                        countElement.style.color = '#DC2626';
                        countElement.style.fontWeight = '500';
                        button.disabled = true;
                        button.style.opacity = '0.5';
                        button.style.cursor = 'not-allowed';
                        button.title = 'No upcoming showtimes available';
                    } else {
                        countElement.textContent = `🎬 ${futureShowtimes.length} show(s) available`;
                    }
                }
            }
        } catch (e) {
            console.error('Error updating showtimes count:', e);
        }
    });
}

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
    
    // Get current datetime
    const now = new Date();
    
    // Filter out past showtimes
    const futureShowtimes = showtimes.filter(showtime => {
        try {
            // Parse show datetime
            const showDateTime = new Date(`${showtime.show_date}T${showtime.show_time}:00`);
            // Keep only showtimes that haven't started yet
            return showDateTime > now;
        } catch (e) {
            console.error('Error parsing showtime:', showtime, e);
            return true; // Include if unable to parse
        }
    });
    
    // If no future showtimes, show message
    if (futureShowtimes.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: var(--text-dark);">
                <p style="font-size: 18px; margin-bottom: 10px;">📭 No upcoming showtimes</p>
                <p style="opacity: 0.7;">All showtimes for this theatre have already started.</p>
            </div>
        `;
        modal.style.display = 'flex';
        return;
    }
    
    // Group showtimes by date
    const showtimesByDate = {};
    futureShowtimes.forEach(showtime => {
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
                <div class="showtime-time">⏰ ${formatTime(showtime.show_time)}</div>
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

// Format date for display (DD-MM-YYYY)
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const options = { weekday: 'short' };
    const weekday = date.toLocaleDateString('en-US', options);
    return `${weekday}, ${day}-${month}-${year}`;
}

// Format time for display (12-hour with AM/PM)
function formatTime(timeStr) {
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${String(displayHour).padStart(2, '0')}:${minutes} ${ampm}`;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('showtimeModal');
    if (event.target === modal) {
        closeModal();
    }
}

console.log('Movie details page loaded! 🎥');
