// Theatre Dashboard functionality

// Delete movie function
function deleteMovie(movieId, movieTitle) {
    if (!confirm(`Are you sure you want to delete "${movieTitle}"?\n\nThis will remove all showtimes for this movie at your theatre.`)) {
        return;
    }
    
    fetch(`/delete-movie/${movieId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message || 'Movie deleted successfully!');
            window.location.reload();
        } else {
            alert(data.message || 'Failed to delete movie');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the movie');
    });
}

// Edit movie function (placeholder for now - will redirect to add movie page with edit mode)
function editMovie(movieId) {
    // For now, just show alert that feature is coming
    alert('Edit functionality coming soon!\n\nFor now, you can delete and re-add the movie with updated information.');
}

console.log('Theatre dashboard loaded! 🎭');
