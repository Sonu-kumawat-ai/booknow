// Theatre Dashboard functionality


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
