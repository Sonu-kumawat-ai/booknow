"""
Theatre owner routes module
Handles theatre owner registration and management
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from bson import ObjectId

theatre_bp = Blueprint('theatre', __name__)

def init_theatre(mongo):
    """Initialize theatre blueprint with mongo instance"""
    theatre_bp.mongo = mongo
    return theatre_bp

@theatre_bp.route('/theatre-owner-registration')
def theatre_owner_registration():
    """Theatre owner registration form page"""
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('auth.login'))
    
    # Fetch user data
    user = theatre_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        flash('User not found. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if already a theatre owner
    if user.get('role') == 'theatre_owner':
        flash('You are already a theatre owner.', 'error')
        return redirect(url_for('user.settings'))
    
    # Check if already has a pending request
    existing_application = theatre_bp.mongo.db.theatre_owner_applications.find_one({
        'user_id': session['user_id'],
        'status': 'pending'
    })
    if existing_application:
        flash('Your request is already pending admin approval.', 'error')
        return redirect(url_for('user.settings'))
    
    return render_template('theatre_owner_registration.html', user=user, user_data=user)

@theatre_bp.route('/become-theatre-owner', methods=['POST'])
def become_theatre_owner():
    """Request to become a theatre owner - needs admin approval"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if already has a pending request
    user = theatre_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Check if already has pending application
    existing_application = theatre_bp.mongo.db.theatre_owner_applications.find_one({
        'user_id': session['user_id'],
        'status': 'pending'
    })
    if existing_application:
        flash('Your request is already pending admin approval.', 'error')
        return redirect(url_for('user.settings'))
    
    # Check if already a theatre owner
    if user.get('role') == 'theatre_owner':
        flash('You are already a theatre owner.', 'error')
        return redirect(url_for('user.settings'))
    
    # Get form data
    theatre_name = request.form.get('theatre_name')
    theatre_address = request.form.get('theatre_address')
    city = request.form.get('city')
    state = request.form.get('state')
    pincode = request.form.get('pincode')
    phone = request.form.get('phone')
    theatre_type = request.form.get('theatre_type')
    total_screens = request.form.get('total_screens')
    screen_capacities = request.form.getlist('screen_capacity[]')
    parking_capacity = request.form.get('parking_capacity', '0')
    amenities = request.form.getlist('amenities')
    license_number = request.form.get('license_number', '')
    established_year = request.form.get('established_year', '')
    website = request.form.get('website', '')
    operating_hours = request.form.get('operating_hours', '')
    
    # Validation
    if not all([theatre_name, theatre_address, city, state, pincode, phone, theatre_type, total_screens]):
        flash('All required fields must be filled!', 'error')
        return redirect(url_for('theatre.theatre_owner_registration'))
    
    if not screen_capacities or len(screen_capacities) != int(total_screens):
        flash('Please provide seating capacity for all screens!', 'error')
        return redirect(url_for('theatre.theatre_owner_registration'))
    
    # Create theatre owner application
    application = {
        'user_id': session['user_id'],
        'username': user.get('username'),
        'email': user.get('email'),
        'theatre_name': theatre_name,
        'theatre_address': theatre_address,
        'city': city,
        'state': state,
        'pincode': pincode,
        'phone': phone,
        'theatre_type': theatre_type,
        'total_screens': int(total_screens),
        'screen_capacities': [int(cap) for cap in screen_capacities],
        'parking_capacity': int(parking_capacity) if parking_capacity else 0,
        'amenities': amenities,
        'license_number': license_number,
        'established_year': int(established_year) if established_year else None,
        'website': website,
        'operating_hours': operating_hours,
        'status': 'pending',
        'applied_date': datetime.utcnow(),
        'reviewed_by': None,
        'reviewed_date': None
    }
    
    # Insert application
    theatre_bp.mongo.db.theatre_owner_applications.insert_one(application)
    
    flash('Your request has been submitted! Please wait for admin approval.', 'success')
    return redirect(url_for('user.settings'))

@theatre_bp.route('/theatre-dashboard')
def theatre_dashboard():
    """Theatre owner dashboard to view their movies"""
    if 'user_id' not in session:
        flash('Please login to access dashboard.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is theatre owner
    user = theatre_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('role') != 'theatre_owner':
        flash('You need to be a theatre owner to access dashboard.', 'error')
        return redirect(url_for('user.settings'))
    
    # Get theatre details from theatres collection
    theatre = theatre_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
    if not theatre:
        flash('Theatre information not found.', 'error')
        return redirect(url_for('user.settings'))
    
    # Get all screens for this theatre
    screens = list(theatre_bp.mongo.db.screens.find({'theatre_id': str(theatre['_id'])}))
    
    # Fetch all showtimes for this theatre with movie and screen details
    from datetime import datetime, timedelta
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')
    
    all_showtimes = list(theatre_bp.mongo.db.showtimes.find({
        'theatre_id': str(theatre['_id']),
        'status': 'active',
        '$or': [
            {'show_date': {'$gt': current_date}},
            {
                'show_date': current_date,
                'show_time': {'$gte': current_time}
            }
        ]
    }))
    
    # Enrich showtimes with movie and screen data
    shows = []
    for showtime in all_showtimes:
        movie = theatre_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
        screen = theatre_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
        
        if movie and screen:
            show = {
                'showtime_id': str(showtime['_id']),
                'movie_title': movie.get('title', 'Unknown'),
                'movie_poster': movie.get('poster_url', ''),
                'movie_duration': movie.get('duration', 0),
                'screen_name': screen.get('name', 'Unknown'),
                'show_date': showtime.get('show_date', ''),
                'show_time': showtime.get('show_time', ''),
                'ticket_price': showtime.get('ticket_price', 0),
                'vip_price': showtime.get('vip_price', 0),
                'available_seats': showtime.get('available_seats', 0)
            }
            shows.append(show)
    
    # Calculate statistics
    total_shows = len(shows)
    total_screens = len(screens)
    total_movies = len(set([s['movie_title'] for s in shows])) if shows else 0
    
    # Get recent bookings for this theatre
    showtime_ids = [str(st['_id']) for st in all_showtimes]
    booking_count = theatre_bp.mongo.db.bookings.count_documents({
        'showtime_id': {'$in': showtime_ids}
    }) if showtime_ids else 0
    
    return render_template('theatre_dashboard.html', 
                         user=user, 
                         user_data=user,
                         theatre=theatre,
                         screens=screens,
                         my_shows=shows,
                         total_shows=total_shows,
                         total_screens=total_screens,
                         total_movies=total_movies,
                         total_bookings=booking_count)
