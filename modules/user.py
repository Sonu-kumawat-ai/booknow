"""
User routes module
Handles user profile and settings
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

user_bp = Blueprint('user', __name__)

def init_user(mongo):
    """Initialize user blueprint with mongo instance"""
    user_bp.mongo = mongo
    return user_bp

@user_bp.route('/profile')
def profile():
    """Profile page route"""
    if 'user_id' not in session:
        flash('Please login to view your profile.', 'error')
        return redirect(url_for('auth.login'))
    
    # Fetch user data
    user = user_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        flash('User not found. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Set default role if not present (for existing users)
    if 'role' not in user:
        default_role = 'user'
        if user.get('email') == 'kumawatsonu086@gmail.com':
            default_role = 'admin'
        elif user.get('is_theatre_owner'):
            default_role = 'theatre_owner'
        
        user_bp.mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'role': default_role}}
        )
        user['role'] = default_role
    
    # Fetch user bookings
    bookings = list(user_bp.mongo.db.bookings.find({'user_id': session['user_id']}).sort('booking_date', -1))
    
    # Fetch details for each booking
    for booking in bookings:
        # Get showtime details
        showtime = user_bp.mongo.db.showtimes.find_one({'_id': ObjectId(booking['showtime_id'])})
        if showtime:
            # Get movie details
            movie = user_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
            booking['movie'] = movie if movie else {}
            
            # Get theatre details
            theatre = user_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
            booking['theatre_info'] = {
                'theatre_name': theatre.get('name', 'Unknown') if theatre else 'Unknown',
                'city': theatre.get('city', '') if theatre else ''
            }
            
            # Get screen details
            screen = user_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
            booking['screen_name'] = screen.get('name', 'Unknown') if screen else 'Unknown'
            
            # Get seats for this booking
            booking_seats = list(user_bp.mongo.db.booking_seats.find({'booking_id': str(booking['_id'])}))
            booking['seats'] = [seat['seat_number'] for seat in booking_seats]
            booking['show_time'] = showtime.get('show_time')
    
    return render_template('profile.html', user=user, user_data=user, bookings=bookings)

@user_bp.route('/settings')
def settings():
    """Settings page route"""
    if 'user_id' not in session:
        flash('Please login to access settings.', 'error')
        return redirect(url_for('auth.login'))
    
    # Fetch user data
    user = user_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        flash('User not found. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Set default role if not present (for existing users)
    if 'role' not in user:
        default_role = 'user'
        if user.get('email') == 'kumawatsonu086@gmail.com':
            default_role = 'admin'
        elif user.get('is_theatre_owner'):
            default_role = 'theatre_owner'
        
        user_bp.mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'role': default_role}}
        )
        user['role'] = default_role
    
    # Check for pending theatre owner application
    pending_application = user_bp.mongo.db.theatre_owner_applications.find_one({
        'user_id': session['user_id'],
        'status': 'pending'
    })
    
    rejected_application = user_bp.mongo.db.theatre_owner_applications.find_one({
        'user_id': session['user_id'],
        'status': 'rejected'
    })
    
    return render_template('settings.html', 
                         user=user, 
                         user_data=user,
                         pending_application=pending_application,
                         rejected_application=rejected_application)

@user_bp.route('/update-email', methods=['POST'])
def update_email():
    """Update user email"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    new_email = request.form.get('email')
    
    if not new_email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    # Check if email already exists
    existing_user = user_bp.mongo.db.users.find_one({
        'email': new_email,
        '_id': {'$ne': ObjectId(session['user_id'])}
    })
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already in use'}), 400
    
    # Update email
    user_bp.mongo.db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'email': new_email}}
    )
    
    flash('Email updated successfully!', 'success')
    return jsonify({'success': True, 'message': 'Email updated successfully'}), 200

@user_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        flash('Please login to change password.', 'error')
        return redirect(url_for('auth.login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validation
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required!', 'error')
        return redirect(url_for('user.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match!', 'error')
        return redirect(url_for('user.settings'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long!', 'error')
        return redirect(url_for('user.settings'))
    
    # Fetch user
    user = user_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Verify current password
    if not check_password_hash(user['password'], current_password):
        flash('Current password is incorrect!', 'error')
        return redirect(url_for('user.settings'))
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    user_bp.mongo.db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'password': hashed_password}}
    )
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('user.settings'))

@user_bp.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete user account"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    # Delete user's bookings
    user_bp.mongo.db.bookings.delete_many({'user_id': user_id})
    
    # Delete user's booking seats
    bookings = list(user_bp.mongo.db.bookings.find({'user_id': user_id}))
    for booking in bookings:
        user_bp.mongo.db.booking_seats.delete_many({'booking_id': str(booking['_id'])})
    
    # Delete user's payments
    user_bp.mongo.db.payments.delete_many({'user_id': user_id})
    
    # Delete user's theatre owner applications
    user_bp.mongo.db.theatre_owner_applications.delete_many({'user_id': user_id})
    
    # Delete user
    user_bp.mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    
    # Clear session
    session.clear()
    
    flash('Your account has been deleted successfully.', 'success')
    return jsonify({'success': True, 'redirect': url_for('main.index')}), 200
