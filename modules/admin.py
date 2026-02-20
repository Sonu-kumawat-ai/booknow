"""
Admin routes module
Handles admin panel and theatre owner approvals
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)

def init_admin(mongo):
    """Initialize admin blueprint with mongo instance"""
    admin_bp.mongo = mongo
    return admin_bp

@admin_bp.route('/admin')
def admin():
    """Admin dashboard - only for kumawatsonu086@gmail.com"""
    if 'user_id' not in session:
        flash('Please login to access admin panel.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is admin (check both email and role for backward compatibility)
    user = admin_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    
    if not is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.index'))
    
    # Set admin role if not already set (auto-migration)
    if user.get('email') == 'kumawatsonu086@gmail.com' and user.get('role') != 'admin':
        admin_bp.mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'role': 'admin'}}
        )
        user['role'] = 'admin'
    
    # Fetch pending theatre owner applications
    pending_requests = list(admin_bp.mongo.db.theatre_owner_applications.find({'status': 'pending'}))
    
    # Fetch all active theatres
    all_theatres = list(admin_bp.mongo.db.theatres.find({'status': 'active'}))
    for theatre in all_theatres:
        owner = admin_bp.mongo.db.users.find_one({'_id': ObjectId(theatre['owner_id'])})
        theatre['owner_name'] = owner.get('username', 'Unknown') if owner else 'Unknown'
        theatre['owner_email'] = owner.get('email', 'Unknown') if owner else 'Unknown'
        # normalize id to string for templates and further queries
        theatre_id_str = str(theatre['_id'])
        theatre['_id'] = theatre_id_str
        # count screens for display
        try:
            theatre['screens_count'] = admin_bp.mongo.db.screens.count_documents({'theatre_id': theatre_id_str})
        except Exception:
            theatre['screens_count'] = 0
        # attach upcoming showtimes (limit 3) for hover preview
        try:
            current_dt = datetime.now()
            current_date = current_dt.strftime('%Y-%m-%d')
            current_time = current_dt.strftime('%H:%M')
            upcoming = list(admin_bp.mongo.db.showtimes.find({
                'theatre_id': theatre_id_str,
                'status': 'active',
                '$or': [
                    {'show_date': {'$gt': current_date}},
                    {
                        'show_date': current_date,
                        'show_time': {'$gte': current_time}
                    }
                ]
            }).sort([('show_date', 1), ('show_time', 1)]).limit(3))
            theatre['next_shows'] = []
            for st in upcoming:
                try:
                    movie = admin_bp.mongo.db.movies.find_one({'_id': ObjectId(st['movie_id'])})
                except Exception:
                    movie = None
                try:
                    screen = admin_bp.mongo.db.screens.find_one({'_id': ObjectId(st['screen_id'])})
                except Exception:
                    screen = None
                theatre['next_shows'].append({
                    'movie_title': movie.get('title') if movie else 'Unknown',
                    'show_date': st.get('show_date', ''),
                    'show_time': st.get('show_time', ''),
                    'screen_name': screen.get('name') if screen else ''
                })
        except Exception:
            theatre['next_shows'] = []
    
    # Fetch all movies and enrich with useful display data
    all_movies_raw = list(admin_bp.mongo.db.movies.find())
    all_movies = []
    for mv in all_movies_raw:
        try:
            movie_id_str = str(mv['_id'])
        except Exception:
            movie_id_str = mv.get('_id')
        mv['_id'] = movie_id_str
        mv.setdefault('poster_url', '')
        mv.setdefault('genre', '')
        mv.setdefault('language', '')
        mv.setdefault('duration', 0)
        mv.setdefault('release_date', '')

        # average rating and review count
        try:
            reviews = list(admin_bp.mongo.db.reviews.find({'movie_id': movie_id_str}))
            if reviews:
                avg = sum([r.get('rating', 0) for r in reviews]) / len(reviews)
                mv['avg_rating'] = round(avg, 1)
                mv['reviews_count'] = len(reviews)
            else:
                mv['avg_rating'] = None
                mv['reviews_count'] = 0
        except Exception:
            mv['avg_rating'] = None
            mv['reviews_count'] = 0

        # count future showtimes for this movie
        try:
            current_dt = datetime.now()
            current_date = current_dt.strftime('%Y-%m-%d')
            current_time = current_dt.strftime('%H:%M')
            mv['showtimes_count'] = admin_bp.mongo.db.showtimes.count_documents({
                'movie_id': movie_id_str,
                'status': 'active',
                '$or': [
                    {'show_date': {'$gt': current_date}},
                    {'show_date': current_date, 'show_time': {'$gte': current_time}}
                ]
            })
        except Exception:
            mv['showtimes_count'] = 0

        # preview list of theatres showing this movie (up to 3)
        try:
            theatres_preview = []
            sts = admin_bp.mongo.db.showtimes.find({'movie_id': movie_id_str, 'status': 'active'}).sort([('show_date', 1), ('show_time', 1)])
            for st in sts:
                tid = st.get('theatre_id')
                if not tid:
                    continue
                if tid in theatres_preview:
                    continue
                theatres_preview.append(tid)
                if len(theatres_preview) >= 3:
                    break
            # resolve theatre names
            theatre_names = []
            for tid in theatres_preview:
                try:
                    th = admin_bp.mongo.db.theatres.find_one({'_id': ObjectId(tid)})
                    theatre_names.append(th.get('name') if th else 'Unknown')
                except Exception:
                    theatre_names.append('Unknown')
            mv['theatres_preview'] = theatre_names
        except Exception:
            mv['theatres_preview'] = []

        all_movies.append(mv)
    
    # Fetch all users count
    total_users = admin_bp.mongo.db.users.count_documents({})
    total_bookings = admin_bp.mongo.db.bookings.count_documents({})
    
    # Count movies by status
    theatre_movies_count = admin_bp.mongo.db.movies.count_documents({'status': 'theatre'})
    upcoming_movies_count = admin_bp.mongo.db.movies.count_documents({'status': 'upcoming'})
    
    return render_template('admin.html', 
                         user=user,
                         user_data=user,
                         pending_requests=pending_requests,
                         theatre_owners=all_theatres,  # For backward compatibility with template
                         all_theatres=all_theatres,
                         all_movies=all_movies,
                         total_users=total_users,
                         total_bookings=total_bookings,
                         theatre_movies_count=theatre_movies_count,
                         upcoming_movies_count=upcoming_movies_count)

@admin_bp.route('/admin/approve-theatre-owner/<application_id>', methods=['POST'])
def approve_theatre_owner(application_id):
    """Approve theatre owner request"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is admin
    admin_user = admin_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    is_admin = admin_user and (admin_user.get('role') == 'admin' or admin_user.get('email') == 'kumawatsonu086@gmail.com')
    if not is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.index'))
    
    # Get the application
    application = admin_bp.mongo.db.theatre_owner_applications.find_one({'_id': ObjectId(application_id)})
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('admin.admin'))
    
    # Update user role to theatre_owner
    admin_bp.mongo.db.users.update_one(
        {'_id': ObjectId(application['user_id'])},
        {'$set': {'role': 'theatre_owner'}}
    )
    
    # Create theatre record
    theatre = {
        'owner_id': application['user_id'],
        'name': application['theatre_name'],
        'address': application['theatre_address'],
        'city': application['city'],
        'state': application['state'],
        'pincode': application['pincode'],
        'phone': application['phone'],
        'theatre_type': application['theatre_type'],
        'parking_capacity': application.get('parking_capacity', 0),
        'amenities': application.get('amenities', []),
        'license_number': application.get('license_number', ''),
        'established_year': application.get('established_year'),
        'website': application.get('website', ''),
        'operating_hours': application.get('operating_hours', ''),
        'status': 'active',
        'created_date': datetime.utcnow()
    }
    theatre_id = admin_bp.mongo.db.theatres.insert_one(theatre).inserted_id
    
    # Create screens for the theatre with individual capacities
    total_screens = application.get('total_screens', 1)
    screen_capacities = application.get('screen_capacities', [])
    
    # If no individual capacities, use default
    if not screen_capacities:
        default_capacity = application.get('seating_capacity', 100)
        screen_capacities = [default_capacity] * total_screens
    
    for screen_num in range(1, total_screens + 1):
        # Use individual capacity for each screen
        capacity = screen_capacities[screen_num - 1] if screen_num <= len(screen_capacities) else 100
        screen = {
            'theatre_id': str(theatre_id),
            'screen_number': screen_num,
            'name': f'Screen {screen_num}',
            'seating_capacity': capacity,
            'screen_type': '2D',
            'sound_system': 'Dolby Digital',
            'features': ['Air Conditioned', 'Wheelchair Accessible'],
            'status': 'active',
            'created_date': datetime.utcnow()
        }
        admin_bp.mongo.db.screens.insert_one(screen)
    
    # Update application status
    admin_bp.mongo.db.theatre_owner_applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$set': {
            'status': 'approved',
            'reviewed_by': session['user_id'],
            'reviewed_date': datetime.utcnow()
        }}
    )
    # Delete the application document after processing
    try:
        admin_bp.mongo.db.theatre_owner_applications.delete_one({'_id': ObjectId(application_id)})
    except Exception:
        pass

    flash('Theatre owner request approved successfully!', 'success')
    return redirect(url_for('admin.admin'))

@admin_bp.route('/admin/reject-theatre-owner/<application_id>', methods=['POST'])
def reject_theatre_owner(application_id):
    """Reject theatre owner request"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is admin
    admin_user = admin_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    is_admin = admin_user and (admin_user.get('role') == 'admin' or admin_user.get('email') == 'kumawatsonu086@gmail.com')
    if not is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.index'))
    
    # Update application status
    admin_bp.mongo.db.theatre_owner_applications.update_one(
        {'_id': ObjectId(application_id)},
        {'$set': {
            'status': 'rejected',
            'reviewed_by': session['user_id'],
            'reviewed_date': datetime.utcnow()
        }}
    )
    # Delete the application document after processing
    try:
        admin_bp.mongo.db.theatre_owner_applications.delete_one({'_id': ObjectId(application_id)})
    except Exception:
        pass

    flash('Theatre owner request rejected.', 'error')
    return redirect(url_for('admin.admin'))

@admin_bp.route('/admin/remove-theatre-owner/<theatre_id>', methods=['POST'])
def remove_theatre_owner(theatre_id):
    """Remove theatre and revoke theatre owner status"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is admin
    admin_user = admin_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    is_admin = admin_user and (admin_user.get('role') == 'admin' or admin_user.get('email') == 'kumawatsonu086@gmail.com')
    if not is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.index'))
    
    # Get theatre
    theatre = admin_bp.mongo.db.theatres.find_one({'_id': ObjectId(theatre_id)})
    if theatre:
        # Update user role back to user
        admin_bp.mongo.db.users.update_one(
            {'_id': ObjectId(theatre['owner_id'])},
            {'$set': {'role': 'user'}}
        )
        
        # Delete theatre
        admin_bp.mongo.db.theatres.delete_one({'_id': ObjectId(theatre_id)})
        
        # Delete all screens for this theatre
        admin_bp.mongo.db.screens.delete_many({'theatre_id': theatre_id})
        
        # Delete all showtimes for this theatre
        admin_bp.mongo.db.showtimes.delete_many({'theatre_id': theatre_id})
        
        # Delete theatre owner application if exists
        admin_bp.mongo.db.theatre_owner_applications.delete_many({'user_id': theatre['owner_id']})
    
    flash('Theatre and all related data deleted successfully.', 'success')
    return redirect(url_for('admin.admin'))
