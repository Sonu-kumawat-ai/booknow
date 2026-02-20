// Add Offer Page JavaScript

// Global variables for multi-select
let selectedTheatres = [];
let selectedMovies = [];
let allMovies = [];  // Store all movies for filtering

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    document.getElementById('validFrom').value = todayStr;
    
    // Set default end date to 1 month from now
    const nextMonth = new Date();
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    document.getElementById('validUntil').value = nextMonth.toISOString().split('T')[0];
    
    // Set min date for date inputs
    document.getElementById('validFrom').min = todayStr;
    document.getElementById('validUntil').min = todayStr;
    
    // Form submission handler
    document.getElementById('addOfferForm').addEventListener('submit', handleFormSubmit);
    
    // Real-time validation
    setupValidation();
    
    // Store all movies for filtering
    const movieOptions = document.querySelectorAll('#movieDropdown .multi-select-option');
    movieOptions.forEach(option => {
        allMovies.push({
            id: option.dataset.id,
            name: option.dataset.name,
            element: option
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.multi-select-container')) {
            closeAllDropdowns();
        }
    });
});

// Multi-select functions for theatres
function toggleTheatreDropdown() {
    const dropdown = document.getElementById('theatreDropdown');
    const wrapper = document.getElementById('theatreSelectWrapper');
    
    dropdown.classList.toggle('active');
    wrapper.classList.toggle('focused');
    
    // Close movie dropdown if open
    document.getElementById('movieDropdown').classList.remove('active');
    document.getElementById('movieSelectWrapper').classList.remove('focused');
}

function toggleTheatreSelection(event, theatreId, theatreName) {
    event.stopPropagation();
    
    const checkbox = document.getElementById('theatre_' + theatreId);
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        if (!selectedTheatres.find(t => t.id === theatreId)) {
            selectedTheatres.push({ id: theatreId, name: theatreName });
        }
    } else {
        selectedTheatres = selectedTheatres.filter(t => t.id !== theatreId);
    }
    
    updateTheatreDisplay();
}

function removeTheatre(theatreId) {
    selectedTheatres = selectedTheatres.filter(t => t.id !== theatreId);
    const checkbox = document.getElementById('theatre_' + theatreId);
    if (checkbox) checkbox.checked = false;
    updateTheatreDisplay();
}

function updateTheatreDisplay() {
    const container = document.getElementById('selectedTheatres');
    const placeholder = document.getElementById('theatrePlaceholder');
    const hiddenInput = document.getElementById('selectedTheatreIds');
    
    if (selectedTheatres.length === 0) {
        container.innerHTML = '';
        placeholder.style.display = 'block';
        hiddenInput.value = '';
    } else {
        placeholder.style.display = 'none';
        container.innerHTML = selectedTheatres.map(theatre => `
            <span class="selected-item">
                ${theatre.name}
                <span class="remove-btn" onclick="removeTheatre('${theatre.id}')">&times;</span>
            </span>
        `).join('');
        hiddenInput.value = selectedTheatres.map(t => t.id).join(',');
    }
}

// Multi-select functions for movies
function toggleMovieDropdown() {
    const dropdown = document.getElementById('movieDropdown');
    const wrapper = document.getElementById('movieSelectWrapper');
    
    dropdown.classList.toggle('active');
    wrapper.classList.toggle('focused');
    
    // Close theatre dropdown if open
    const theatreDropdown = document.getElementById('theatreDropdown');
    if (theatreDropdown) {
        theatreDropdown.classList.remove('active');
        const theatreWrapper = document.getElementById('theatreSelectWrapper');
        if (theatreWrapper) theatreWrapper.classList.remove('focused');
    }
}

function toggleMovieSelection(event, movieId, movieName) {
    event.stopPropagation();
    
    const checkbox = document.getElementById('movie_' + movieId);
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        if (!selectedMovies.find(m => m.id === movieId)) {
            selectedMovies.push({ id: movieId, name: movieName });
        }
    } else {
        selectedMovies = selectedMovies.filter(m => m.id !== movieId);
    }
    
    updateMovieDisplay();
}

function removeMovie(movieId) {
    selectedMovies = selectedMovies.filter(m => m.id !== movieId);
    const checkbox = document.getElementById('movie_' + movieId);
    if (checkbox) checkbox.checked = false;
    updateMovieDisplay();
}

function updateMovieDisplay() {
    const container = document.getElementById('selectedMovies');
    const placeholder = document.getElementById('moviePlaceholder');
    const hiddenInput = document.getElementById('selectedMovieIds');
    
    if (selectedMovies.length === 0) {
        container.innerHTML = '';
        placeholder.style.display = 'block';
        hiddenInput.value = '';
    } else {
        placeholder.style.display = 'none';
        container.innerHTML = selectedMovies.map(movie => `
            <span class="selected-item">
                ${movie.name}
                <span class="remove-btn" onclick="removeMovie('${movie.id}')">&times;</span>
            </span>
        `).join('');
        hiddenInput.value = selectedMovies.map(m => m.id).join(',');
    }
}

function closeAllDropdowns() {
    document.querySelectorAll('.multi-select-dropdown').forEach(dropdown => {
        dropdown.classList.remove('active');
    });
    document.querySelectorAll('.multi-select-wrapper').forEach(wrapper => {
        wrapper.classList.remove('focused');
    });
}

// Load movies for selected theatre
async function loadMoviesForTheatre() {
    const theatreId = document.getElementById('theatreFilter').value;
    const movieDropdown = document.getElementById('movieDropdown');
    
    if (!theatreId) {
        // Show all movies
        allMovies.forEach(movie => {
            movie.element.style.display = 'flex';
        });
        return;
    }
    
    try {
        // Fetch movies for this theatre
        const response = await fetch(`/get-theatre-movies/${theatreId}`);
        const data = await response.json();
        
        if (data.success) {
            const theatreMovieIds = data.movies.map(m => m._id);
            
            // Show only movies in this theatre
            allMovies.forEach(movie => {
                if (theatreMovieIds.includes(movie.id)) {
                    movie.element.style.display = 'flex';
                } else {
                    movie.element.style.display = 'none';
                }
            });
            
            // Clear selected movies that are not in this theatre
            selectedMovies = selectedMovies.filter(m => theatreMovieIds.includes(m.id));
            updateMovieDisplay();
        }
    } catch (error) {
        console.error('Error loading movies:', error);
        showFlashMessage('Failed to load theatre movies', 'error');
    }
}

// Toggle max discount field based on discount type
function toggleMaxDiscount() {
    const discountType = document.getElementById('discountType').value;
    const maxDiscountGroup = document.getElementById('maxDiscountGroup');
    const discountHint = document.getElementById('discountHint');
    
    if (discountType === 'percentage') {
        maxDiscountGroup.style.display = 'block';
        discountHint.textContent = 'Enter percentage value (e.g., 20 for 20%)';
        document.getElementById('discountValue').max = '100';
    } else {
        maxDiscountGroup.style.display = 'none';
        discountHint.textContent = 'Enter fixed amount in rupees';
        document.getElementById('discountValue').removeAttribute('max');
    }
}

// Toggle applicable fields based on selection
function toggleApplicableFields() {
    const applicableTo = document.getElementById('applicableTo').value;
    const theatreSelectGroup = document.getElementById('theatreSelectGroup');
    const theatreFilterGroup = document.getElementById('theatreFilterGroup');
    const movieSelectGroup = document.getElementById('movieSelectGroup');
    
    // Hide all groups first
    if (theatreSelectGroup) theatreSelectGroup.style.display = 'none';
    if (theatreFilterGroup) theatreFilterGroup.style.display = 'none';
    if (movieSelectGroup) movieSelectGroup.style.display = 'none';
    
    // Show relevant groups based on selection
    if (applicableTo === 'theatres' && theatreSelectGroup) {
        theatreSelectGroup.style.display = 'block';
    } else if (applicableTo === 'movies') {
        movieSelectGroup.style.display = 'block';
        // Reset movie filter if admin
        if (theatreFilterGroup) {
            const theatreFilter = document.getElementById('theatreFilter');
            if (theatreFilter) theatreFilter.value = '';
        }
        // Show all movies
        allMovies.forEach(movie => {
            movie.element.style.display = 'flex';
        });
    } else if (applicableTo === 'theatre_movies' && theatreFilterGroup && movieSelectGroup) {
        theatreFilterGroup.style.display = 'block';
        movieSelectGroup.style.display = 'block';
    }
    
    // Clear selections when changing type
    selectedTheatres = [];
    selectedMovies = [];
    updateTheatreDisplay();
    updateMovieDisplay();
    
    // Uncheck all checkboxes
    document.querySelectorAll('.multi-select-option input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
}

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    
    try {
        // Gather form data
        const formData = new FormData(e.target);
        const data = {};
        
        formData.forEach((value, key) => {
            // Skip empty values for optional fields
            if (value !== '' || isRequiredField(key)) {
                data[key] = value;
            }
        });
        
        // Send request
        const response = await fetch('/create-offer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message
            showFlashMessage('Offer created successfully! Redirecting...', 'success');
            
            // Redirect after short delay
            setTimeout(() => {
                // Redirect based on user role
                const userRole = document.body.dataset.userRole || 'admin';
                if (userRole === 'admin') {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/theatre-dashboard';
                }
            }, 1500);
        } else {
            // Show error message
            showFlashMessage(result.message || 'Failed to create offer', 'error');
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            submitBtn.innerHTML = originalText;
        }
        
    } catch (error) {
        console.error('Error:', error);
        showFlashMessage('An error occurred. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        submitBtn.innerHTML = originalText;
    }
}

// Form validation
function validateForm() {
    let isValid = true;
    
    // Validate offer code
    const offerCode = document.getElementById('offerCode');
    if (!offerCode.value.trim()) {
        showFieldError(offerCode, 'Offer code is required');
        isValid = false;
    } else if (offerCode.value.length < 3) {
        showFieldError(offerCode, 'Offer code must be at least 3 characters');
        isValid = false;
    } else {
        clearFieldError(offerCode);
    }
    
    // Validate description
    const description = document.getElementById('offerDescription');
    if (!description.value.trim()) {
        showFieldError(description, 'Description is required');
        isValid = false;
    } else {
        clearFieldError(description);
    }
    
    // Validate discount value
    const discountValue = document.getElementById('discountValue');
    const discountType = document.getElementById('discountType').value;
    
    if (!discountValue.value || parseFloat(discountValue.value) <= 0) {
        showFieldError(discountValue, 'Discount value must be greater than 0');
        isValid = false;
    } else if (discountType === 'percentage' && parseFloat(discountValue.value) > 100) {
        showFieldError(discountValue, 'Percentage cannot exceed 100%');
        isValid = false;
    } else {
        clearFieldError(discountValue);
    }
    
    // Validate dates
    const validFrom = document.getElementById('validFrom');
    const validUntil = document.getElementById('validUntil');
    
    if (!validFrom.value) {
        showFieldError(validFrom, 'Start date is required');
        isValid = false;
    } else {
        clearFieldError(validFrom);
    }
    
    if (!validUntil.value) {
        showFieldError(validUntil, 'End date is required');
        isValid = false;
    } else if (new Date(validUntil.value) <= new Date(validFrom.value)) {
        showFieldError(validUntil, 'End date must be after start date');
        isValid = false;
    } else {
        clearFieldError(validUntil);
    }
    
    // Validate applicable selection
    const applicableTo = document.getElementById('applicableTo').value;
    
    if (applicableTo === 'theatres') {
        if (selectedTheatres.length === 0) {
            showFlashMessage('Please select at least one theatre', 'error');
            isValid = false;
        }
    }
    
    if (applicableTo === 'movies' || applicableTo === 'theatre_movies') {
        if (selectedMovies.length === 0) {
            showFlashMessage('Please select at least one movie', 'error');
            isValid = false;
        }
    }
    
    if (applicableTo === 'theatre_movies') {
        const theatreFilter = document.getElementById('theatreFilter');
        if (!theatreFilter || !theatreFilter.value) {
            showFlashMessage('Please select a theatre', 'error');
            isValid = false;
        }
    }
    
    return isValid;
}

// Setup real-time validation
function setupValidation() {
    // Offer code - uppercase conversion
    const offerCode = document.getElementById('offerCode');
    offerCode.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
    
    // Discount type change
    document.getElementById('discountType').addEventListener('change', toggleMaxDiscount);
    
    // Applicable to change
    document.getElementById('applicableTo').addEventListener('change', toggleApplicableFields);
    
    // Date validation
    document.getElementById('validFrom').addEventListener('change', function() {
        const validUntil = document.getElementById('validUntil');
        validUntil.min = this.value;
    });
}

// Show field error
function showFieldError(field, message) {
    field.classList.add('error');
    
    // Remove existing error message
    const existingError = field.parentElement.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    field.parentElement.appendChild(errorDiv);
}

// Clear field error
function clearFieldError(field) {
    field.classList.remove('error');
    const errorMessage = field.parentElement.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

// Check if field is required
function isRequiredField(fieldName) {
    const requiredFields = ['code', 'description', 'discount_type', 'discount_value', 
                           'valid_from', 'valid_until', 'applicable_to'];
    return requiredFields.includes(fieldName);
}

// Show flash message
function showFlashMessage(message, type = 'success') {
    // Create flash container if it doesn't exist
    let flashContainer = document.querySelector('.flash-container');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-container';
        document.body.appendChild(flashContainer);
    }
    
    // Create flash message
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message flash-${type}`;
    flashDiv.innerHTML = `
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    flashContainer.appendChild(flashDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

// Go back function
function goBack() {
    if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
        window.history.back();
    }
}

// Prevent form submission on enter key (except in textarea)
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        const form = document.getElementById('addOfferForm');
        if (form.contains(e.target)) {
            e.preventDefault();
        }
    }
});
