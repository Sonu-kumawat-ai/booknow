document.addEventListener('DOMContentLoaded', () => {
    const reviewsList = document.getElementById('reviewsList');
    if (reviewsList && !reviewsList.classList.contains('reviews-list')) reviewsList.classList.add('reviews-list');
    const loadMoreBtn = document.getElementById('loadMoreReviews');
    const reviewForm = document.getElementById('reviewForm');
    const movieId = reviewsList ? reviewsList.dataset.movieId : null;
    let skip = 0;
    const limit = 3;

    const currentUserId = window.CURRENT_USER_ID || null;

    function renderReview(r) {
        const card = document.createElement('div');
        card.className = 'review-card';
        card.dataset.reviewId = r._id;

        // Avatar (initials)
        const avatar = document.createElement('div');
        avatar.className = 'review-avatar';
        const initials = (r.username || 'A').split(' ').map(s => s[0]).slice(0,2).join('').toUpperCase();
        avatar.textContent = initials;

        // Body
        const body = document.createElement('div');
        body.className = 'review-body';

        const meta = document.createElement('div');
        meta.className = 'review-meta';
        const name = document.createElement('div');
        name.className = 'review-username';
        name.textContent = r.username || 'Anonymous';

        const rating = document.createElement('div');
        rating.className = 'review-rating';
        rating.textContent = r.rating != null ? r.rating : '';

        const date = document.createElement('div');
        date.className = 'review-date';
        try {
            date.textContent = new Date(r.created_at).toLocaleString();
        } catch (e) {
            date.textContent = '';
        }

        meta.appendChild(name);
        meta.appendChild(rating);
        meta.appendChild(date);

        const text = document.createElement('div');
        text.className = 'review-text';
        text.textContent = r.text || '';

        body.appendChild(meta);
        body.appendChild(text);

        // Actions (delete)
        if (currentUserId && r.user_id && String(currentUserId) === String(r.user_id)) {
            const actions = document.createElement('div');
            actions.className = 'review-actions';
            const del = document.createElement('button');
            del.className = 'review-delete';
            del.textContent = 'Delete';
            del.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteReview(r._id);
            });
            actions.appendChild(del);
            body.appendChild(actions);
        }

        card.appendChild(avatar);
        card.appendChild(body);

        return card;
    }

    async function loadReviews(reset = false) {
        if (!movieId) return;
        if (reset) skip = 0;
        const resp = await fetch(`/reviews/${movieId}?skip=${skip}&limit=${limit}`);
        if (!resp.ok) return;
        const data = await resp.json();
        if (!data.success) return;

        // Update average rating display if present
        const avg = data.avg_rating;
        if (avg !== null && avg !== undefined) {
            const avgEl = document.getElementById('avgRating');
            if (avgEl) avgEl.textContent = `⭐ ${avg}`;
        }

        if (reset) reviewsList.innerHTML = '';

        // If skip==0 and user's review present, it will be first
        data.reviews.forEach(r => {
            const el = renderReview(r);
            reviewsList.appendChild(el);
        });

        skip += data.reviews.length - (data.reviews.length && data.reviews[0] && (currentUserId && data.reviews[0].user_id === currentUserId) ? 1 : 0);

        // Hide load more if we've loaded all
        if (reviewsList.children.length >= data.total) {
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'inline-block';
        }
    }

    async function submitReview(e) {
        e.preventDefault();
        if (!movieId) return;
        const rating = document.getElementById('reviewRating').value;
        const text = document.getElementById('reviewText').value;

        const resp = await fetch('/reviews/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({movie_id: movieId, rating, text})
        });
        const data = await resp.json();
        if (!data.success) {
            alert(data.error || 'Could not submit review');
            return;
        }

        // Prepend new review and reset
        loadReviews(true);
        if (reviewForm) reviewForm.reset();
    }

    async function deleteReview(reviewId) {
        if (!confirm('Delete your review?')) return;
        const resp = await fetch(`/reviews/delete/${reviewId}`, {method: 'POST'});
        const data = await resp.json();
        if (!data.success) {
            alert(data.error || 'Could not delete review');
            return;
        }
        loadReviews(true);
    }

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => loadReviews(false));
    }
    if (reviewForm) {
        reviewForm.addEventListener('submit', submitReview);
    }

    // Initialize: load first page
    loadReviews(true);
});
