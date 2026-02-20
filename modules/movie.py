"""
Movie routes module
Handles movie addition, details, and listing
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from bson import ObjectId

movie_bp = Blueprint('movie', __name__)

def init_movie(mongo):
    """Initialize movie blueprint with mongo instance"""
    movie_bp.mongo = mongo
    return movie_bp

@movie_bp.route('/add-movie', methods=['GET', 'POST'])
def add_movie():
    """Add movie page route - For theatre owners and admins"""
    if 'user_id' not in session:
        flash('Please login to add movies.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user is theatre owner or admin
    user = movie_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or (user.get('role') != 'theatre_owner' and user.get('role') != 'admin'):
        flash('You need to be a theatre owner or admin to add movies.', 'error')
        return redirect(url_for('user.settings'))
    
    # For admin: get all theatres, for theatre owner: get their theatre
    if user.get('role') == 'admin':
        all_theatres = list(movie_bp.mongo.db.theatres.find({'status': 'active'}))
        theatre = None
        screens = []
        # If theatre selected in form, get its screens
        selected_theatre_id = request.form.get('theatre_id') or request.args.get('theatre_id')
        if selected_theatre_id:
            theatre = movie_bp.mongo.db.theatres.find_one({'_id': ObjectId(selected_theatre_id)})
            screens = list(movie_bp.mongo.db.screens.find({'theatre_id': selected_theatre_id, 'status': 'active'}))
    else:
        # Get theatre for theatre owner
        theatre = movie_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
        if not theatre:
            flash('Theatre information not found.', 'error')
            return redirect(url_for('user.settings'))
        screens = list(movie_bp.mongo.db.screens.find({'theatre_id': str(theatre['_id']), 'status': 'active'}))
        all_theatres = None
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        poster_url = request.form.get('poster_url')
        director = request.form.get('director')
        cast = request.form.get('cast')
        duration = request.form.get('duration')
        release_date = request.form.get('release_date')
        language = request.form.get('language')
        # allow multiple genres
        genre_list = request.form.getlist('genre')
        # normalize to comma-separated string for storage
        genre = ', '.join([g for g in genre_list if g]) if genre_list else ''
        certificate = request.form.get('certificate', '')
        trailer_url = request.form.get('trailer_url', '')
        
        show_dates = request.form.getlist('show_date[]')
        show_times = request.form.getlist('show_time[]')
        screen_ids = request.form.getlist('screen_id[]')
        ticket_prices = request.form.getlist('ticket_price[]')
        vip_prices = request.form.getlist('vip_price[]')

        # Basic required fields validation
        if not all([title, description, poster_url, director, cast, duration, release_date, language, genre]):
            flash('All required fields must be filled!', 'error')
            return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

        # Convert title to uppercase
        title = title.upper()

        # Check if movie already exists (based on title, duration, release_date, and director)
        existing_movie = movie_bp.mongo.db.movies.find_one({
            'title': title,
            'duration': int(duration),
            'release_date': release_date,
            'director': director
        })

        if existing_movie:
            movie_id = existing_movie['_id']
            # message differs based on role
            if user.get('role') == 'theatre_owner':
                flash(f'Movie "{title}" already exists. Adding showtimes to existing movie.', 'success')
            else:
                flash(f'Movie "{title}" already exists.', 'success')
        else:
            # Determine movie status based on release date and user role
            movie_status = 'theatre'  # default
            if user.get('role') == 'admin':
                # Admin can explicitly set status or it's calculated from release date
                release_date_obj = datetime.strptime(release_date, '%Y-%m-%d').date()
                current_date = datetime.now().date()
                days_until_release = (release_date_obj - current_date).days
                
                # If release date is more than 7 days away, mark as upcoming
                if days_until_release > 7:
                    movie_status = 'upcoming'
                else:
                    movie_status = 'theatre'
            else:
                # Theatre owners can only add movies that are releasing now
                movie_status = 'theatre'
            
            movie_data = {
                'title': title,
                'description': description,
                'poster_url': poster_url,
                'director': director,
                'cast': cast,
                'duration': int(duration),
                'release_date': release_date,
                'language': language,
                'genre': genre,
                'certificate': certificate,
                'trailer_url': trailer_url,
                'status': movie_status,
                'created_at': datetime.utcnow()
            }
            movie_id = movie_bp.mongo.db.movies.insert_one(movie_data).inserted_id

        # If the requester is a theatre owner, require and create showtimes
        if user.get('role') == 'theatre_owner':
            # Check if the movie is in theatre status (not upcoming)
            movie_doc = movie_bp.mongo.db.movies.find_one({'_id': movie_id})
            if movie_doc and movie_doc.get('status') == 'upcoming':
                flash('Cannot add showtimes for upcoming movies. Please wait until it releases.', 'error')
                return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)
            
            if not show_dates or not show_times or not screen_ids or not ticket_prices or not vip_prices:
                flash('Please provide valid show details including screens, dates, times, and prices!', 'error')
                return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

            if len(show_dates) != len(show_times) or len(show_dates) != len(screen_ids) or len(show_dates) != len(ticket_prices) or len(show_dates) != len(vip_prices):
                flash('Please provide screen and prices for all showtimes!', 'error')
                return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

            # Validate show dates are not before release date
            release_date_obj = datetime.strptime(release_date, '%Y-%m-%d').date()
            for show_date in show_dates:
                show_date_obj = datetime.strptime(show_date, '%Y-%m-%d').date()
                if show_date_obj < release_date_obj:
                    flash(f'Show date ({show_date}) cannot be before the release date ({release_date})!', 'error')
                    return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

            # Create showtimes for this movie
            movie_duration = int(duration)
            for i in range(len(show_dates)):
                show_date = show_dates[i]
                show_time = show_times[i]
                screen_id = screen_ids[i]

                # Get screen details
                screen = movie_bp.mongo.db.screens.find_one({'_id': ObjectId(screen_id)})
                if not screen:
                    flash(f'Invalid screen selected for show {i+1}', 'error')
                    return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

                screen_theatre_id = screen.get('theatre_id')

                # Calculate end time for this show (add buffer of 30 minutes for cleaning)
                show_datetime = datetime.strptime(f"{show_date} {show_time}", '%Y-%m-%d %H:%M')
                show_end_datetime = show_datetime + timedelta(minutes=movie_duration + 30)

                # Check for conflicting shows in the same screen on the same date
                existing_showtimes = list(movie_bp.mongo.db.showtimes.find({
                    'screen_id': screen_id,
                    'show_date': show_date,
                    'status': 'active'
                }))

                has_conflict = False
                for existing in existing_showtimes:
                    existing_movie = movie_bp.mongo.db.movies.find_one({'_id': ObjectId(existing['movie_id'])})
                    if not existing_movie:
                        continue

                    existing_duration = existing_movie.get('duration', 120)
                    existing_datetime = datetime.strptime(f"{existing['show_date']} {existing['show_time']}", '%Y-%m-%d %H:%M')
                    existing_end_datetime = existing_datetime + timedelta(minutes=existing_duration + 30)

                    if (show_datetime < existing_end_datetime and show_end_datetime > existing_datetime):
                        has_conflict = True
                        existing_movie_title = existing_movie.get('title', 'Unknown')
                        flash(f'Show conflict! Screen is occupied from {existing["show_time"]} to {existing_end_datetime.strftime("%H:%M")} by "{existing_movie_title}" on {show_date}. Please choose a different time.', 'error')
                        break

                if has_conflict:
                    return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

                # No conflict, create the showtime
                showtime = {
                    'movie_id': str(movie_id),
                    'theatre_id': screen_theatre_id,
                    'screen_id': screen_id,
                    'show_date': show_date,
                    'show_time': show_time,
                    'ticket_price': int(ticket_prices[i]),
                    'vip_price': int(vip_prices[i]),
                    'available_seats': screen.get('seating_capacity', 100),
                    'status': 'active',
                    'created_date': datetime.utcnow(),
                    'created_by': session.get('user_id')
                }
                movie_bp.mongo.db.showtimes.insert_one(showtime)

            flash('Movie and showtimes added successfully!', 'success')
            return redirect(url_for('theatre.theatre_dashboard'))

        # Admin adds movie only (no showtimes)
        flash('Movie added successfully!', 'success')
        return redirect(url_for('admin.admin'))
    
    return render_template('add_movie.html', user=user, user_data=user, theatre=theatre, screens=screens, all_theatres=all_theatres)

@movie_bp.route('/debug_movies')
def debug_movies():
    """Debug route to check movies in database"""
    movies = list(movie_bp.mongo.db.movies.find({}, {'title': 1, '_id': 1}).limit(10))
    result = "<h1>Movies in Database:</h1><ul>"
    for movie in movies:
        result += f"<li>Title: {movie.get('title', 'No title')} | ID: {movie['_id']} | Type: {type(movie['_id'])}</li>"
    result += "</ul>"
    return result


@movie_bp.route('/movies-for-form')
def movies_for_form():
    """Return movies for the Add Movie form (JSON)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user = movie_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('role') not in ('theatre_owner', 'admin'):
        return jsonify({'error': 'Not authorized'}), 403

    try:
        movies = list(movie_bp.mongo.db.movies.find({}))
        result = []
        for m in movies:
            genre_list = [g.strip() for g in m.get('genre', '').split(',') if g.strip()]
            result.append({
                '_id': str(m.get('_id')),
                'title': m.get('title', ''),
                'description': m.get('description', ''),
                'poster_url': m.get('poster_url', ''),
                'director': m.get('director', ''),
                'cast': m.get('cast', ''),
                'duration': m.get('duration', ''),
                'release_date': m.get('release_date', ''),
                'language': m.get('language', ''),
                'genre': genre_list,
                'certificate': m.get('certificate', ''),
                'trailer_url': m.get('trailer_url', '')
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch movies', 'detail': str(e)}), 500

@movie_bp.route('/movie/<movie_id>')
def movie_details(movie_id):
    """Movie details page"""
    try:
        # Try to convert to ObjectId
        try:
            obj_id = ObjectId(movie_id)
        except Exception as e:
            flash('Invalid movie ID format.', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch movie details
        movie = movie_bp.mongo.db.movies.find_one({'_id': obj_id})
        
        if not movie:
            flash('Movie not found.', 'error')
            return redirect(url_for('main.index'))
        
        # Get current date and time
        current_datetime = datetime.now()
        current_date = current_datetime.strftime('%Y-%m-%d')
        current_time = current_datetime.strftime('%H:%M')
        
        # Get showtimes for this movie (only future showtimes)
        showtimes = list(movie_bp.mongo.db.showtimes.find({
            'movie_id': str(movie['_id']),
            'status': 'active',
            '$or': [
                {'show_date': {'$gt': current_date}},
                {
                    'show_date': current_date,
                    'show_time': {'$gte': current_time}
                }
            ]
        }))
        
        # Group showtimes by theatre
        theatres_dict = {}
        for showtime in showtimes:
            try:
                theatre_id = showtime['theatre_id']
                if theatre_id not in theatres_dict:
                    theatre = movie_bp.mongo.db.theatres.find_one({'_id': ObjectId(theatre_id)})
                    if theatre:
                        theatres_dict[theatre_id] = {
                            'theatre_id': theatre_id,
                            'theatre_name': theatre.get('name', 'Unknown'),
                            'theatre_city': theatre.get('city', ''),
                            'theatre_address': theatre.get('address', ''),
                            'showtimes': []
                        }
                
                if theatre_id in theatres_dict:
                    screen = movie_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
                    # Get actual capacity from screen, fallback to showtime's available_seats
                    screen_capacity = screen.get('seating_capacity', showtime.get('available_seats', 100)) if screen else showtime.get('available_seats', 100)
                    
                    theatres_dict[theatre_id]['showtimes'].append({
                        '_id': str(showtime['_id']),
                        'show_date': showtime['show_date'],
                        'show_time': showtime['show_time'],
                        'ticket_price': showtime['ticket_price'],
                        'vip_price': showtime['vip_price'],
                        'available_seats': showtime['available_seats'],
                        'total_capacity': screen_capacity,
                        'screen_name': screen.get('name', 'Unknown') if screen else 'Unknown'
                    })
            except Exception:
                pass
        
        # Convert to list for template
        theatres = list(theatres_dict.values())
        
        # Get user data if logged in
        user_data = None
        if 'user_id' in session:
            user_data = movie_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        # Fetch related movies (same genre)
        related_movies = list(movie_bp.mongo.db.movies.find({
            'genre': movie['genre'],
            '_id': {'$ne': movie['_id']}
        }).limit(4))
        
        # Convert ObjectId to string for URLs
        for related in related_movies:
            related['_id'] = str(related['_id'])
        
        # Convert movie _id to string
        movie['_id'] = str(movie['_id'])
        
        # Determine if reviews should be enabled (movie released)
        can_review = True
        try:
            release_str = movie.get('release_date', '')
            if release_str:
                release_date_obj = datetime.strptime(release_str, '%Y-%m-%d').date()
                can_review = release_date_obj <= current_datetime.date()
        except Exception:
            can_review = True

        return render_template('movie_details.html', 
                             movie=movie,
                             theatres=theatres,
                             user_data=user_data,
                             logged_in='user_id' in session,
                             username=session.get('username', ''),
                             related_movies=related_movies,
                             can_review=can_review)
    except Exception:
        flash('Invalid movie ID.', 'error')
        return redirect(url_for('main.index'))

@movie_bp.route('/get_theatre_screens/<theatre_id>')
def get_theatre_screens(theatre_id):
    """Get screens for a theatre - for admin when adding movies"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = movie_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Not authorized'}), 403
    
    screens = list(movie_bp.mongo.db.screens.find({'theatre_id': theatre_id, 'status': 'active'}))
    for screen in screens:
        screen['_id'] = str(screen['_id'])
    
    return jsonify(screens)

@movie_bp.route('/delete-movie/<movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """Delete a movie and all its showtimes"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user is theatre owner or admin
    user = movie_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or (user.get('role') != 'theatre_owner' and user.get('role') != 'admin'):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    try:
        # Get the movie (try ObjectId first, fallback to string id)
        mv = None
        try:
            mv = movie_bp.mongo.db.movies.find_one({'_id': ObjectId(movie_id)})
        except Exception:
            mv = movie_bp.mongo.db.movies.find_one({'_id': movie_id})

        if not mv:
            return jsonify({'success': False, 'message': 'Movie not found'}), 404

        # If theatre owner, only allow deleting showtimes belonging to their theatre
        if user.get('role') == 'theatre_owner':
            theatre = movie_bp.mongo.db.theatres.find_one({'owner_id': session['user_id']})
            if not theatre:
                return jsonify({'success': False, 'message': 'Theatre not found'}), 404

            # Delete showtimes for this theatre only
            movie_bp.mongo.db.showtimes.delete_many({'movie_id': movie_id, 'theatre_id': str(theatre['_id'])})

            # If no remaining showtimes for this movie, remove the movie as well (and its reviews)
            remaining = movie_bp.mongo.db.showtimes.count_documents({'movie_id': movie_id})
            if remaining == 0:
                try:
                    movie_bp.mongo.db.reviews.delete_many({'movie_id': movie_id})
                except Exception:
                    pass
                movie_bp.mongo.db.movies.delete_one({'_id': mv['_id']})

            return jsonify({'success': True, 'message': 'Showtimes for your theatre deleted'}), 200

        # Admin flow: delete all related data for the movie
        # 1) Gather showtimes for this movie
        showtimes = list(movie_bp.mongo.db.showtimes.find({'movie_id': movie_id}))
        showtime_ids = [str(st.get('_id')) for st in showtimes if st.get('_id')]

        # 2) Delete booking seats tied to these showtimes
        try:
            if showtime_ids:
                movie_bp.mongo.db.booking_seats.delete_many({'showtime_id': {'$in': showtime_ids}})
        except Exception:
            pass

        # 3) Find bookings for these showtimes and delete payments + bookings
        booking_ids = []
        try:
            if showtime_ids:
                bookings = list(movie_bp.mongo.db.bookings.find({'showtime_id': {'$in': showtime_ids}}))
                booking_ids = [str(b.get('_id')) for b in bookings if b.get('_id')]
                if booking_ids:
                    # delete payments related to these bookings
                    try:
                        movie_bp.mongo.db.payments.delete_many({'booking_id': {'$in': booking_ids}})
                    except Exception:
                        pass
                    # delete bookings
                    movie_bp.mongo.db.bookings.delete_many({'_id': {'$in': [ObjectId(bid) for bid in booking_ids]}})
        except Exception:
            pass

        # 4) As a safety, also delete booking_seats by booking_id
        try:
            if booking_ids:
                movie_bp.mongo.db.booking_seats.delete_many({'booking_id': {'$in': booking_ids}})
        except Exception:
            pass

        # 5) Delete reviews for the movie
        try:
            movie_bp.mongo.db.reviews.delete_many({'movie_id': movie_id})
        except Exception:
            pass

        # 6) Delete showtimes
        try:
            movie_bp.mongo.db.showtimes.delete_many({'movie_id': movie_id})
        except Exception:
            pass

        # 7) Finally delete the movie document
        try:
            movie_bp.mongo.db.movies.delete_one({'_id': mv['_id']})
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Movie and all related data deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    try:
        screens = list(movie_bp.mongo.db.screens.find({'theatre_id': theatre_id, 'status': 'active'}))
        return jsonify([{'_id': str(s['_id']), 'name': s.get('name'), 'seating_capacity': s.get('seating_capacity')} for s in screens])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch screens'}), 500
