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
    
    # Fetch all movies
    all_movies = list(admin_bp.mongo.db.movies.find())
    
    # Fetch all users count
    total_users = admin_bp.mongo.db.users.count_documents({})
    total_bookings = admin_bp.mongo.db.bookings.count_documents({})
    
    return render_template('admin.html', 
                         user=user,
                         user_data=user,
                         pending_requests=pending_requests,
                         theatre_owners=all_theatres,  # For backward compatibility with template
                         all_theatres=all_theatres,
                         all_movies=all_movies,
                         total_users=total_users,
                         total_bookings=total_bookings)

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
    
    # Create screens for the theatre
    total_screens = application.get('total_screens', 1)
    seating_capacity_per_screen = application.get('seating_capacity', 100)
    
    for screen_num in range(1, total_screens + 1):
        screen = {
            'theatre_id': str(theatre_id),
            'screen_number': screen_num,
            'name': f'Screen {screen_num}',
            'seating_capacity': seating_capacity_per_screen,
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
