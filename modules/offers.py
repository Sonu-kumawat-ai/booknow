"""
Offers management module
Handles offer creation, validation, and application
"""
from flask import Blueprint, request, jsonify, session, flash, redirect, url_for, render_template
from datetime import datetime
from bson import ObjectId

offers_bp = Blueprint('offers', __name__)

def init_offers(mongo):
    """Initialize offers blueprint with mongo instance"""
    offers_bp.mongo = mongo
    return offers_bp

@offers_bp.route('/add-offer')
def add_offer_page():
    """Render the add offer page"""
    if 'user_id' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('auth.login'))
    
    user = offers_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    # Check if user is admin (by role or email) or theatre_owner
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    is_theatre_owner = user and user.get('role') == 'theatre_owner'
    
    if not user or not (is_admin or is_theatre_owner):
        flash('Not authorized to access this page', 'error')
        return redirect(url_for('main.index'))
    
    # Get user data for template
    user_data = {
        'username': user.get('username'),
        'email': user.get('email'),
        'role': user.get('role')
    }
    
    # Get theatres for admin
    theatres = []
    if is_admin:
        theatres = list(offers_bp.mongo.db.theatres.find({}, {'name': 1, 'location': 1}))
        for theatre in theatres:
            theatre['_id'] = str(theatre['_id'])
    
    # Get movies for dropdown
    movies = []
    if is_admin:
        movies = list(offers_bp.mongo.db.movies.find({'status': 'theatre'}, {'title': 1, 'release_date': 1}))
        for movie in movies:
            movie['_id'] = str(movie['_id'])
    elif is_theatre_owner:
        # Get theatre for owner
        theatre = offers_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
        if theatre:
            # Get movies showing in this theatre
            showtimes = offers_bp.mongo.db.showtimes.find({
                'theatre_id': str(theatre['_id']),
                'status': 'active'
            }, {'movie_id': 1})
            movie_ids = list(set([ObjectId(st['movie_id']) for st in showtimes]))
            movies = list(offers_bp.mongo.db.movies.find({'_id': {'$in': movie_ids}}, {'title': 1}))
            for movie in movies:
                movie['_id'] = str(movie['_id'])
    
    return render_template('add_offer.html', 
                         user_data=user_data, 
                         theatres=theatres,
                         movies=movies)

@offers_bp.route('/create-offer', methods=['POST'])
def create_offer():
    """Create a new offer (Admin or Theatre Owner)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user = offers_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    # Check if user is admin (by role or email) or theatre_owner
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    is_theatre_owner = user and user.get('role') == 'theatre_owner'
    
    if not user or not (is_admin or is_theatre_owner):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['code', 'description', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'applicable_to']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing field: {field}'}), 400
        
        # Convert code to uppercase
        code = data['code'].upper().strip()
        
        # Check if code already exists
        existing = offers_bp.mongo.db.offers.find_one({'code': code})
        if existing:
            return jsonify({'success': False, 'message': 'Offer code already exists'}), 400
        
        # Validate discount value
        discount_value = float(data['discount_value'])
        if discount_value <= 0:
            return jsonify({'success': False, 'message': 'Discount value must be positive'}), 400
        
        if data['discount_type'] == 'percentage' and discount_value > 100:
            return jsonify({'success': False, 'message': 'Percentage discount cannot exceed 100%'}), 400
        
        # Validate dates
        valid_from = datetime.strptime(data['valid_from'], '%Y-%m-%d')
        valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%d')
        
        if valid_until < valid_from:
            return jsonify({'success': False, 'message': 'End date must be after start date'}), 400
        
        # Build offer document
        offer = {
            'code': code,
            'description': data['description'],
            'discount_type': data['discount_type'],  # 'percentage' or 'fixed'
            'discount_value': discount_value,
            'min_purchase': float(data.get('min_purchase', 0)),
            'max_discount': float(data.get('max_discount', 0)) if data['discount_type'] == 'percentage' else 0,
            'usage_limit': int(data.get('usage_limit', 0)),  # 0 = unlimited
            'usage_count': 0,
            'valid_from': data['valid_from'],
            'valid_until': data['valid_until'],
            'applicable_to': data['applicable_to'],  # 'all', 'theatre', 'theatres', 'movies', 'theatre_movies'
            'status': 'active',
            'created_by': session['user_id'],
            'created_at': datetime.utcnow()
        }
        
        # For theatre owners, add theatre/movie restrictions
        if is_theatre_owner:
            theatre = offers_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
            if not theatre:
                return jsonify({'success': False, 'message': 'Theatre not found'}), 404
            
            offer['theatre_id'] = str(theatre['_id'])
            
            # If movie-specific, validate movies are showing in this theatre
            if data['applicable_to'] == 'movies' and 'movie_ids' in data and data['movie_ids']:
                movie_ids = data['movie_ids'].split(',') if isinstance(data['movie_ids'], str) else data['movie_ids']
                # Validate all movies are in this theatre
                for movie_id in movie_ids:
                    showtime = offers_bp.mongo.db.showtimes.find_one({
                        'movie_id': movie_id,
                        'theatre_id': str(theatre['_id']),
                        'status': 'active'
                    })
                    if not showtime:
                        return jsonify({'success': False, 'message': f'One or more movies not showing in your theatre'}), 400
                offer['movie_ids'] = movie_ids
        else:
            # Admin can set theatre/movie specific offers
            if data['applicable_to'] == 'theatres' and 'theatre_ids' in data and data['theatre_ids']:
                theatre_ids = data['theatre_ids'].split(',') if isinstance(data['theatre_ids'], str) else data['theatre_ids']
                offer['theatre_ids'] = theatre_ids
            
            if (data['applicable_to'] == 'movies' or data['applicable_to'] == 'theatre_movies') and 'movie_ids' in data and data['movie_ids']:
                movie_ids = data['movie_ids'].split(',') if isinstance(data['movie_ids'], str) else data['movie_ids']
                offer['movie_ids'] = movie_ids
            
            if data['applicable_to'] == 'theatre_movies' and 'theatre_id' in data and data['theatre_id']:
                offer['theatre_id'] = data['theatre_id']
        
        # Insert offer
        result = offers_bp.mongo.db.offers.insert_one(offer)
        
        return jsonify({
            'success': True,
            'message': 'Offer created successfully',
            'offer_id': str(result.inserted_id)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/get-theatre-movies/<theatre_id>')
def get_theatre_movies(theatre_id):
    """Get movies showing in a specific theatre"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        # Get active showtimes for this theatre
        showtimes = offers_bp.mongo.db.showtimes.find({
            'theatre_id': theatre_id,
            'status': 'active'
        })
        
        # Get unique movie IDs
        movie_ids = list(set([st['movie_id'] for st in showtimes]))
        
        # Get movie details
        movies = []
        for movie_id in movie_ids:
            movie = offers_bp.mongo.db.movies.find_one({'_id': ObjectId(movie_id)})
            if movie:
                movies.append({
                    '_id': str(movie['_id']),
                    'title': movie.get('title')
                })
        
        return jsonify({'success': True, 'movies': movies})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/get-offers')
def get_offers():
    """Get all offers (for management)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user = offers_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    # Check if user is admin (by role or email) or theatre_owner
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    is_theatre_owner = user and user.get('role') == 'theatre_owner'
    
    if not user or not (is_admin or is_theatre_owner):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    try:
        # Build query based on user role
        query = {}
        if is_theatre_owner:
            theatre = offers_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
            if theatre:
                query['theatre_id'] = str(theatre['_id'])
        
        offers = list(offers_bp.mongo.db.offers.find(query).sort('created_at', -1))
        
        # Convert ObjectId to string and enrich data
        for offer in offers:
            offer['_id'] = str(offer['_id'])
            
            # Get theatre names if applicable
            if 'theatre_id' in offer:
                theatre = offers_bp.mongo.db.theatres.find_one({'_id': ObjectId(offer['theatre_id'])})
                offer['theatre_name'] = theatre.get('name') if theatre else 'Unknown'
            elif 'theatre_ids' in offer:
                theatre_names = []
                for theatre_id in offer['theatre_ids']:
                    theatre = offers_bp.mongo.db.theatres.find_one({'_id': ObjectId(theatre_id)})
                    if theatre:
                        theatre_names.append(theatre.get('name'))
                offer['theatre_names'] = ', '.join(theatre_names) if theatre_names else 'Multiple Theatres'
            
            # Get movie names if applicable
            if 'movie_id' in offer:
                movie = offers_bp.mongo.db.movies.find_one({'_id': ObjectId(offer['movie_id'])})
                offer['movie_name'] = movie.get('title') if movie else 'Unknown'
            elif 'movie_ids' in offer:
                movie_names = []
                for movie_id in offer['movie_ids']:
                    movie = offers_bp.mongo.db.movies.find_one({'_id': ObjectId(movie_id)})
                    if movie:
                        movie_names.append(movie.get('title'))
                offer['movie_names'] = ', '.join(movie_names) if movie_names else 'Multiple Movies'
        
        return jsonify({'success': True, 'offers': offers})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/get-applicable-offers', methods=['POST'])
def get_applicable_offers():
    """Get offers applicable to a specific booking (for users at payment)"""
    try:
        data = request.get_json()
        showtime_id = data.get('showtime_id')
        amount = float(data.get('amount', 0))
        
        if not showtime_id:
            return jsonify({'success': False, 'message': 'Showtime ID required'}), 400
        
        # Get showtime details
        showtime = offers_bp.mongo.db.showtimes.find_one({'_id': ObjectId(showtime_id)})
        if not showtime:
            return jsonify({'success': False, 'message': 'Showtime not found'}), 404
        
        movie_id = showtime['movie_id']
        theatre_id = showtime['theatre_id']
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Build query for applicable offers
        offers_query = {
            'status': 'active',
            'valid_from': {'$lte': current_date},
            'valid_until': {'$gte': current_date},
            '$or': [
                # All offers
                {'applicable_to': 'all'},
                # Theatre-specific offers (single or multiple)
                {'applicable_to': 'theatre', 'theatre_id': theatre_id},
                {'applicable_to': 'theatres', 'theatre_ids': theatre_id},
                # Movie-specific offers (single or multiple)
                {'applicable_to': 'movies', 'movie_ids': movie_id},
                # Theatre's movie-specific offers
                {'applicable_to': 'theatre_movies', 'theatre_id': theatre_id, 'movie_ids': movie_id}
            ]
        }
        
        offers = list(offers_bp.mongo.db.offers.find(offers_query))
        
        # Filter by min_purchase and usage_limit
        applicable_offers = []
        for offer in offers:
            # Check minimum purchase
            if offer.get('min_purchase', 0) > amount:
                continue
            
            # Check usage limit
            if offer.get('usage_limit', 0) > 0 and offer.get('usage_count', 0) >= offer.get('usage_limit', 0):
                continue
            
            # Convert ObjectId to string
            offer['_id'] = str(offer['_id'])
            
            # Calculate potential discount
            if offer['discount_type'] == 'percentage':
                discount = (amount * offer['discount_value']) / 100
                if offer.get('max_discount', 0) > 0:
                    discount = min(discount, offer['max_discount'])
            else:  # fixed
                discount = offer['discount_value']
            
            offer['calculated_discount'] = round(discount, 2)
            offer['final_amount'] = round(amount - discount, 2)
            
            applicable_offers.append(offer)
        
        return jsonify({'success': True, 'offers': applicable_offers})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/validate-offer', methods=['POST'])
def validate_offer():
    """Validate and calculate discount for an offer code"""
    try:
        data = request.get_json()
        code = data.get('code', '').upper().strip()
        showtime_id = data.get('showtime_id')
        amount = float(data.get('amount', 0))
        
        if not code or not showtime_id:
            return jsonify({'success': False, 'message': 'Code and showtime required'}), 400
        
        # Get offer by code
        offer = offers_bp.mongo.db.offers.find_one({'code': code})
        if not offer:
            return jsonify({'success': False, 'message': 'Invalid offer code'}), 400
        
        # Check if offer is active
        if offer.get('status') != 'active':
            return jsonify({'success': False, 'message': 'Offer is not active'}), 400
        
        # Check validity dates
        current_date = datetime.now().strftime('%Y-%m-%d')
        if offer['valid_from'] > current_date:
            return jsonify({'success': False, 'message': 'Offer not yet valid'}), 400
        if offer['valid_until'] < current_date:
            return jsonify({'success': False, 'message': 'Offer has expired'}), 400
        
        # Check usage limit
        if offer.get('usage_limit', 0) > 0 and offer.get('usage_count', 0) >= offer.get('usage_limit', 0):
            return jsonify({'success': False, 'message': 'Offer usage limit reached'}), 400
        
        # Check minimum purchase
        if offer.get('min_purchase', 0) > amount:
            return jsonify({'success': False, 'message': f'Minimum purchase of ₹{offer["min_purchase"]} required'}), 400
        
        # Get showtime details
        showtime = offers_bp.mongo.db.showtimes.find_one({'_id': ObjectId(showtime_id)})
        if not showtime:
            return jsonify({'success': False, 'message': 'Showtime not found'}), 404
        
        movie_id = showtime['movie_id']
        theatre_id = showtime['theatre_id']
        
        # Check applicability
        is_applicable = False
        
        # 'all' - applies to everything
        if offer['applicable_to'] == 'all':
            is_applicable = True
        
        # 'theatre' - single theatre (theatre owner or old format)
        elif offer['applicable_to'] == 'theatre' and offer.get('theatre_id') == theatre_id:
            is_applicable = True
        
        # 'theatres' - multiple theatres (admin multi-select)
        elif offer['applicable_to'] == 'theatres' and 'theatre_ids' in offer:
            if theatre_id in offer['theatre_ids']:
                is_applicable = True
        
        # 'movies' - multiple movies (can be in any theatre)
        elif offer['applicable_to'] == 'movies' and 'movie_ids' in offer:
            if movie_id in offer['movie_ids']:
                is_applicable = True
        
        # 'theatre_movies' - specific movies in a specific theatre
        elif offer['applicable_to'] == 'theatre_movies':
            if offer.get('theatre_id') == theatre_id and 'movie_ids' in offer:
                if movie_id in offer['movie_ids']:
                    is_applicable = True
        
        if not is_applicable:
            return jsonify({'success': False, 'message': 'Offer not applicable to this booking'}), 400
        
        # Calculate discount
        if offer['discount_type'] == 'percentage':
            discount = (amount * offer['discount_value']) / 100
            if offer.get('max_discount', 0) > 0:
                discount = min(discount, offer['max_discount'])
        else:  # fixed
            discount = min(offer['discount_value'], amount)  # Can't discount more than total
        
        final_amount = amount - discount
        
        return jsonify({
            'success': True,
            'offer': {
                '_id': str(offer['_id']),
                'code': offer['code'],
                'description': offer['description'],
                'discount_type': offer['discount_type'],
                'discount_value': offer['discount_value']
            },
            'discount': round(discount, 2),
            'final_amount': round(final_amount, 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/delete-offer/<offer_id>', methods=['POST'])
def delete_offer(offer_id):
    """Delete an offer"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user = offers_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    # Check if user is admin (by role or email) or theatre_owner
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    is_theatre_owner = user and user.get('role') == 'theatre_owner'
    
    if not user or not (is_admin or is_theatre_owner):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    try:
        offer = offers_bp.mongo.db.offers.find_one({'_id': ObjectId(offer_id)})
        if not offer:
            return jsonify({'success': False, 'message': 'Offer not found'}), 404
        
        # Theatre owners can only delete their own offers
        if is_theatre_owner:
            theatre = offers_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
            if not theatre or offer.get('theatre_id') != str(theatre['_id']):
                return jsonify({'success': False, 'message': 'Not authorized to delete this offer'}), 403
        
        offers_bp.mongo.db.offers.delete_one({'_id': ObjectId(offer_id)})
        
        return jsonify({'success': True, 'message': 'Offer deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@offers_bp.route('/toggle-offer-status/<offer_id>', methods=['POST'])
def toggle_offer_status(offer_id):
    """Toggle offer status between active and inactive"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user = offers_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    # Check if user is admin (by role or email) or theatre_owner
    is_admin = user and (user.get('role') == 'admin' or user.get('email') == 'kumawatsonu086@gmail.com')
    is_theatre_owner = user and user.get('role') == 'theatre_owner'
    
    if not user or not (is_admin or is_theatre_owner):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    try:
        offer = offers_bp.mongo.db.offers.find_one({'_id': ObjectId(offer_id)})
        if not offer:
            return jsonify({'success': False, 'message': 'Offer not found'}), 404
        
        # Theatre owners can only toggle their own offers
        if is_theatre_owner:
            theatre = offers_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
            if not theatre or offer.get('theatre_id') != str(theatre['_id']):
                return jsonify({'success': False, 'message': 'Not authorized to modify this offer'}), 403
        
        new_status = 'inactive' if offer.get('status') == 'active' else 'active'
        offers_bp.mongo.db.offers.update_one(
            {'_id': ObjectId(offer_id)},
            {'$set': {'status': new_status}}
        )
        
        return jsonify({'success': True, 'message': f'Offer {new_status}', 'status': new_status})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
