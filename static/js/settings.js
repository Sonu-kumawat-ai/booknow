// Settings page functionality

document.addEventListener('DOMContentLoaded', function() {
    // Email update form
    const emailForm = document.getElementById('emailForm');
    if (emailForm) {
        emailForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(emailForm);
            
            fetch(emailForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Email updated successfully!');
                    location.reload();
                } else {
                    alert(data.message || 'Failed to update email');
                }
            })
            .catch(error => {
                alert('Error updating email. Please try again.');
            });
        });
    }
    
    // Delete account button
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            const confirmed = confirm(
                'Are you sure you want to delete your account?\\n\\n' +
                'This action cannot be undone. All your data including:\\n' +
                '- Profile information\\n' +
                '- Booking history\\n' +
                '- Payment records\\n\\n' +
                'will be permanently deleted.\\n\\n' +
                'Type "DELETE" to confirm:'
            );
            
            if (confirmed) {
                const finalConfirm = prompt('Type DELETE to confirm account deletion:');
                
                if (finalConfirm === 'DELETE') {
                    fetch('/delete-account', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Your account has been deleted successfully.');
                            window.location.href = data.redirect;
                        } else {
                            alert(data.message || 'Failed to delete account');
                        }
                    })
                    .catch(error => {
                        alert('Error deleting account. Please try again.');
                    });
                } else {
                    alert('Account deletion cancelled. You must type DELETE to confirm.');
                }
            }
        });
    }
});

