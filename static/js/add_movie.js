// Add Movie page functionality

// Live preview for add movie form
const titleInput = document.getElementById('title');
if (titleInput) {
    titleInput.addEventListener('input', function(e) {
        const previewTitle = document.getElementById('preview-title');
        if (previewTitle) {
            previewTitle.textContent = e.target.value || 'Movie Title';
        }
    });
}

const posterUrlInput = document.getElementById('poster_url');
if (posterUrlInput) {
    posterUrlInput.addEventListener('input', function(e) {
        const img = document.getElementById('preview-image');
        if (img && e.target.value) {
            img.src = e.target.value;
            img.onerror = function() {
                this.src = 'https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop';
            };
        }
    });
}

const ratingInput = document.getElementById('rating');
if (ratingInput) {
    ratingInput.addEventListener('input', function(e) {
        const previewRating = document.getElementById('preview-rating');
        if (previewRating) {
            previewRating.textContent = e.target.value || '0.0';
        }
    });
}

const genreSelect = document.getElementById('genre');
if (genreSelect) {
    genreSelect.addEventListener('change', function(e) {
        const previewGenre = document.getElementById('preview-genre');
        if (previewGenre) {
            // support multiple selection: join selected options
            const selected = Array.from(e.target.selectedOptions).map(o => o.value).filter(Boolean);
            previewGenre.textContent = selected.length ? selected.join(', ') : 'Genre';
        }
    });
}

// Improve UX: allow single-click toggle of options (no Ctrl needed)
if (genreSelect) {
    genreSelect.addEventListener('mousedown', function(e) {
        const opt = e.target;
        if (opt && opt.tagName === 'OPTION') {
            e.preventDefault();
            opt.selected = !opt.selected;
            // dispatch change so preview updates
            const ev = new Event('change', { bubbles: true });
            genreSelect.dispatchEvent(ev);
        }
    });
}

// Load screens for selected theatre (for admin)
function loadTheatreScreens(theatreId) {
    const screenSelect = document.getElementById('screen_id');
    if (!screenSelect) return;
    
    if (!theatreId) {
        screenSelect.disabled = true;
        screenSelect.innerHTML = '<option value="">Select a theatre first</option>';
        return;
    }
    
    screenSelect.disabled = true;
    screenSelect.innerHTML = '<option value="">Loading...</option>';
    
    fetch(`/get_theatre_screens/${theatreId}`)
        .then(response => response.json())
        .then(screens => {
            screenSelect.disabled = false;
            if (screens.length === 0) {
                screenSelect.innerHTML = '<option value="">No screens available</option>';
            } else {
                screenSelect.innerHTML = '<option value="">Choose a screen</option>';
                screens.forEach(screen => {
                    const option = document.createElement('option');
                    option.value = screen._id;
                    option.textContent = `${screen.name} (Capacity: ${screen.seating_capacity})`;
                    screenSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading screens:', error);
            screenSelect.disabled = false;
            screenSelect.innerHTML = '<option value="">Error loading screens</option>';
        });
}

// Generate show time inputs based on total shows selected
function generateShowTimeInputs() {
    const totalShows = document.getElementById('total_shows').value;
    const container = document.getElementById('showTimesContainer');
    const inputsDiv = document.getElementById('showTimeInputs');
    
    if (totalShows && container && inputsDiv) {
        container.style.display = 'block';
        inputsDiv.innerHTML = '';
        
        for (let i = 1; i <= parseInt(totalShows); i++) {
            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'show-time-input-wrapper';
            
            // Get available screens
            const screenSelect = document.getElementById('screen_id');
            let screenOptions = '';
            if (screenSelect) {
                const options = screenSelect.querySelectorAll('option');
                options.forEach(option => {
                    if (option.value) {
                        screenOptions += `<option value="${option.value}">${option.textContent}</option>`;
                    }
                });
            }
            
            inputWrapper.innerHTML = `
                <label for="show_${i}">Show ${i}:</label>
                <div class="show-datetime-inputs">
                    <select name="screen_id[]" class="show-screen-select" required>
                        <option value="">Select Screen</option>
                        ${screenOptions}
                    </select>
                    <input type="date" name="show_date[]" class="show-date-input" placeholder="Date" required>
                    <input type="time" name="show_time[]" placeholder="Time" required>
                    <input type="number" name="ticket_price[]" placeholder="Normal Price (₹)" min="1" step="1" required style="width: 140px;">
                    <input type="number" name="vip_price[]" placeholder="VIP Price (₹)" min="1" step="1" required style="width: 140px;">
                </div>
            `;
            inputsDiv.appendChild(inputWrapper);
        }
        
        // Add validation listeners to show date inputs
        validateShowDates();
    } else if (container && inputsDiv) {
        container.style.display = 'none';
        inputsDiv.innerHTML = '';
    }
}

// Validate that show dates are not before release date
function validateShowDates() {
    const releaseDateInput = document.getElementById('release_date');
    const showDateInputs = document.querySelectorAll('.show-date-input');
    
    if (!releaseDateInput || showDateInputs.length === 0) return;
    
    // Add listener to release date changes
    releaseDateInput.addEventListener('change', function() {
        const releaseDate = this.value;
        if (releaseDate) {
            // Set min attribute on all show date inputs
            showDateInputs.forEach(input => {
                input.setAttribute('min', releaseDate);
                // Validate existing values
                if (input.value && input.value < releaseDate) {
                    input.value = '';
                    alert('Show date cannot be before the release date!');
                }
            });
        }
    });
    
    // Add listeners to each show date input
    showDateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const releaseDate = releaseDateInput.value;
            if (releaseDate && this.value && this.value < releaseDate) {
                alert('Show date cannot be before the release date (' + new Date(releaseDate).toLocaleDateString() + ')!');
                this.value = '';
            }
        });
        
        // Set min if release date is already selected
        const releaseDate = releaseDateInput.value;
        if (releaseDate) {
            input.setAttribute('min', releaseDate);
        }
    });
}

// Auto-load screens and setup event listeners on page load
window.addEventListener('DOMContentLoaded', function() {
    // Setup theatre selector event listener
    const theatreSelect = document.getElementById('theatre_id');
    if (theatreSelect && theatreSelect.tagName === 'SELECT') {
        theatreSelect.addEventListener('change', function() {
            loadTheatreScreens(this.value);
        });
    }
    
    // Setup total shows event listener
    const totalShowsInput = document.getElementById('total_shows');
    if (totalShowsInput) {
        totalShowsInput.addEventListener('change', generateShowTimeInputs);
    }
});

console.log('Add movie page loaded! ➕🎬');
