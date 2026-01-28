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

// Custom genre tags UI (syncs with hidden select#genre)
function initGenreTags() {
    const select = document.getElementById('genre');
    if (!select) return;

    // dropdown container
    const dropdown = document.getElementById('genreDropdown');
    const tagsContainer = document.getElementById('genreTags');
    const input = document.getElementById('genreInput');
    const box = document.getElementById('genreBox');

    if (!dropdown || !tagsContainer || !input || !box) return;

    // Populate dropdown from select options
    dropdown.innerHTML = '';
    Array.from(select.options).forEach(opt => {
        const o = document.createElement('div');
        o.className = 'genre-option';
        o.dataset.value = opt.value;
        o.textContent = opt.value;
        if (opt.selected) o.classList.add('selected');
        o.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleGenre(opt.value);
        });
        dropdown.appendChild(o);
    });

    function renderTags() {
        const selected = Array.from(select.selectedOptions).map(o => o.value);
        tagsContainer.innerHTML = '';
        selected.forEach(val => {
            const tag = document.createElement('span');
            tag.className = 'genre-tag';
            tag.textContent = val;

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-genre';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                deselectGenre(val);
            });

            tag.appendChild(removeBtn);
            tagsContainer.appendChild(tag);
        });
        // Keep the input empty (tags show selections); input retained for focus/accessibility
        input.value = '';
    }

    function toggleGenre(val) {
        const opt = Array.from(select.options).find(o => o.value === val);
        if (!opt) return;
        opt.selected = !opt.selected;
        // update dropdown option state
        const ddOpt = dropdown.querySelector(`.genre-option[data-value="${CSS.escape(val)}"]`);
        if (ddOpt) ddOpt.classList.toggle('selected', opt.selected);
        renderTags();
        // notify existing listeners (preview update)
        select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function deselectGenre(val) {
        const opt = Array.from(select.options).find(o => o.value === val);
        if (!opt) return;
        opt.selected = false;
        const ddOpt = dropdown.querySelector(`.genre-option[data-value="${CSS.escape(val)}"]`);
        if (ddOpt) ddOpt.classList.remove('selected');
        renderTags();
        select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Toggle dropdown visibility
    box.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('open');
        dropdown.setAttribute('aria-hidden', dropdown.classList.contains('open') ? 'false' : 'true');
    });

    // Close when clicking outside
    document.addEventListener('click', function(e) {
        if (!box.contains(e.target)) {
            dropdown.classList.remove('open');
            dropdown.setAttribute('aria-hidden', 'true');
        }
    });

    // Initial render
    renderTags();
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

    // Initialize custom genre tag selector
    try { initGenreTags(); } catch (e) { console.debug('Genre tags init failed', e); }

    // Load existing movies and render horizontally-scrollable cards for selection
    const existingMovieContainer = document.getElementById('existing_movie_list');
    const movieMap = {};
    if (existingMovieContainer) {
        // Helper to clear autofill fields and reset preview/buttons
        const clearAutofill = () => {
            const ids = ['title','description','poster_url','director','cast','duration','release_date','language','certificate','trailer_url'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                if (el.tagName === 'SELECT' || el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.value = '';
            });

            const gSelect = document.getElementById('genre');
            if (gSelect) {
                Array.from(gSelect.options).forEach(opt => opt.selected = false);
                gSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }

            const previewTitle = document.getElementById('preview-title');
            if (previewTitle) previewTitle.textContent = 'Movie Title';
            const previewImage = document.getElementById('preview-image');
            if (previewImage) previewImage.src = 'https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop';
            const previewGenre = document.getElementById('preview-genre');
            if (previewGenre) previewGenre.textContent = 'Genre';

            // reset all select buttons
            const allBtns = existingMovieContainer.querySelectorAll('.select-movie-btn');
            allBtns.forEach(b => {
                b.dataset.selected = 'false';
                b.textContent = 'Select';
                b.classList.remove('selected');
            });
        };

        // Add a clear-autofill button above the list for convenience
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-outline';
        clearBtn.id = 'clear_autofill_btn';
        clearBtn.textContent = 'Clear Autofill';
        clearBtn.addEventListener('click', clearAutofill);
        existingMovieContainer.insertAdjacentElement('beforebegin', clearBtn);

        fetch('/movies-for-form')
            .then(response => {
                if (!response.ok) throw new Error('Not authorized or failed');
                return response.json();
            })
            .then(data => {
                if (!Array.isArray(data) || data.length === 0) return;
                data.forEach(m => {
                    movieMap[m._id] = m;

                    const card = document.createElement('div');
                    card.className = 'existing-movie-card';

                    const imgWrap = document.createElement('div');
                    imgWrap.className = 'existing-movie-poster';
                    const img = document.createElement('img');
                    img.src = m.poster_url || 'https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop';
                    img.alt = m.title || 'Poster';
                    imgWrap.appendChild(img);

                    const info = document.createElement('div');
                    info.className = 'existing-movie-info';
                    const h4 = document.createElement('h4');
                    h4.textContent = m.title || 'Untitled';
                    info.appendChild(h4);

                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'btn btn-primary select-movie-btn';
                    btn.textContent = 'Select';
                    btn.dataset.movieId = m._id;
                    btn.dataset.selected = 'false';
                    btn.addEventListener('click', function() {
                        const id = this.dataset.movieId;
                        const mm = movieMap[id];
                        if (!mm) return;

                        // Toggle: if already selected, deselect and clear autofill
                        if (this.dataset.selected === 'true') {
                            clearAutofill();
                            return;
                        }

                        // Ensure only one selected at a time
                        const allBtns = existingMovieContainer.querySelectorAll('.select-movie-btn');
                        allBtns.forEach(b => {
                            b.dataset.selected = 'false';
                            b.textContent = 'Select';
                            b.classList.remove('selected');
                        });

                        // Mark this button as selected and change label to 'Deselect'
                        this.dataset.selected = 'true';
                        this.textContent = 'Deselect';
                        this.classList.add('selected');

                        const setIf = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
                        setIf('title', mm.title || '');
                        setIf('description', mm.description || '');
                        setIf('poster_url', mm.poster_url || '');
                        setIf('director', mm.director || '');
                        setIf('cast', mm.cast || '');
                        setIf('duration', mm.duration || '');
                        setIf('release_date', mm.release_date || '');
                        setIf('language', mm.language || '');
                        setIf('certificate', mm.certificate || '');
                        setIf('trailer_url', mm.trailer_url || '');

                        // Genres (multi-select)
                        const gSelect = document.getElementById('genre');
                        if (gSelect && Array.isArray(mm.genre)) {
                            Array.from(gSelect.options).forEach(opt => {
                                opt.selected = mm.genre.includes(opt.value);
                            });
                            gSelect.dispatchEvent(new Event('change', { bubbles: true }));
                        }

                        // Update preview
                        const previewTitle = document.getElementById('preview-title');
                        if (previewTitle) previewTitle.textContent = mm.title || 'Movie Title';
                        const previewImage = document.getElementById('preview-image');
                        if (previewImage && mm.poster_url) previewImage.src = mm.poster_url;
                        const previewGenre = document.getElementById('preview-genre');
                        if (previewGenre) previewGenre.textContent = (mm.genre && mm.genre.length) ? mm.genre.join(', ') : 'Genre';

                        // Scroll selected card into view briefly
                        card.scrollIntoView({ behavior: 'smooth', inline: 'center' });
                    });

                    card.appendChild(imgWrap);
                    card.appendChild(info);
                    card.appendChild(btn);
                    existingMovieContainer.appendChild(card);
                });
            })
            .catch(err => {
                console.debug('Could not load movies for form:', err);
            });
    }
});

console.log('Add movie page loaded! ➕🎬');
