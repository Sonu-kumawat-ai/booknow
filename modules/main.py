"""
Main routes module
Handles home page and basic pages
"""
from flask import Blueprint, render_template, session, request
import difflib
from bson import ObjectId

main_bp = Blueprint('main', __name__)

def init_main(mongo):
    """Initialize main blueprint with mongo instance"""
    main_bp.mongo = mongo
    return main_bp

@main_bp.route('/')
def index():
    """Home page route"""
    from datetime import datetime, timedelta
    from modules.database_init import update_movie_status
    
    # Auto-update movie status before displaying
    try:
        update_movie_status(main_bp.mongo)
    except Exception:
        pass  # Continue even if update fails
    
    user_logged_in = 'user_id' in session
    username = session.get('username', '')
    
    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')
    
    # Fetch only theatre movies (not upcoming) for home page
    all_movies = list(main_bp.mongo.db.movies.find({'status': 'theatre'}))

    movies = []
    for movie in all_movies:
        movie_id_str = str(movie['_id'])

        # Check if this movie has any future showtimes
        future_showtimes_count = main_bp.mongo.db.showtimes.count_documents({
            'movie_id': movie_id_str,
            'status': 'active',
            '$or': [
                {'show_date': {'$gt': current_date}},
                {
                    'show_date': current_date,
                    'show_time': {'$gte': current_time}
                }
            ]
        })

        # Prepare movie data for template
        movie['_id'] = movie_id_str

        # compute average rating from reviews collection
        agg = list(main_bp.mongo.db.reviews.aggregate([
            {'$match': {'movie_id': movie_id_str}},
            {'$group': {'_id': '$movie_id', 'avg': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
        ]))
        movie['avg_rating'] = round(agg[0]['avg'], 1) if agg else None
        movie['reviews_count'] = agg[0]['count'] if agg else 0

        # flag whether this movie has upcoming shows
        movie['has_show'] = future_showtimes_count > 0

        movies.append(movie)

    # Sort movies: 1) Latest first (today/tomorrow/upcoming shows), 2) Released movies, 3) Future releases
    def get_movie_sort_key(m):
        rd = m.get('release_date')
        try:
            release_date = datetime.strptime(rd, '%Y-%m-%d').date() if rd else datetime.max.date()
        except Exception:
            release_date = datetime.max.date()
        
        today = datetime.now().date()
        days_diff = (release_date - today).days
        
        # Category 1: Movies with shows in next 3 days (priority: 0-2)
        if 0 <= days_diff <= 2:
            return (0, days_diff, release_date)  # Latest first (today=0, tomorrow=1, day after=2)
        # Category 2: Already released movies (priority: 1)
        elif days_diff < 0:
            return (1, -days_diff, release_date)  # Most recent releases first
        # Category 3: Future releases (priority: 2)
        else:
            return (2, days_diff, release_date)  # Nearest future releases first
    
    movies.sort(key=get_movie_sort_key)
    movies = movies[:3]
    
    # Get user data if logged in
    user_data = None
    if user_logged_in:
        user_data = main_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    return render_template('index.html', logged_in=user_logged_in, username=username, movies=movies, user_data=user_data)

@main_bp.route('/movies')
def all_movies():
    """All movies page route"""
    from datetime import datetime
    from modules.database_init import update_movie_status
    
    # Auto-update movie status before displaying
    try:
        update_movie_status(main_bp.mongo)
    except Exception:
        pass  # Continue even if update fails
    
    user_logged_in = 'user_id' in session
    username = session.get('username', '')
    
    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')
    
    # Get status filter from query parameter (default: theatre)
    status_filter = request.args.get('status', 'theatre')
    if status_filter not in ['theatre', 'upcoming']:
        status_filter = 'theatre'
    
    # Fetch movies based on status filter
    movie_query = {'status': status_filter} if status_filter else {}
    all_movies_list = list(main_bp.mongo.db.movies.find(movie_query))

    # Handle search query (supports typo-tolerant matching)
    q = (request.args.get('q') or '').strip()
    search_query = q

    # prepare a mapping of title -> movie for fuzzy lookup
    title_map = {}
    for mv in all_movies_list:
        try:
            title_map[str(mv.get('title','')).lower()] = mv
        except Exception:
            pass

    matched_movies = []
    if q:
        q_low = q.lower()
        # 1) exact substring matches on title, genre, director, cast
        for movie in all_movies_list:
            movie_id_str = str(movie['_id'])
            title = movie.get('title','').lower()
            genre = movie.get('genre','').lower()
            director = movie.get('director','').lower() if movie.get('director') else ''
            cast = movie.get('cast','').lower() if movie.get('cast') else ''
            if q_low in title or q_low in genre or q_low in director or q_low in cast:
                matched_movies.append(movie)

        # 2) fuzzy fallback on titles if no substring matches
        if not matched_movies:
            titles = list(title_map.keys())
            close = difflib.get_close_matches(q_low, titles, n=10, cutoff=0.6)
            for t in close:
                mv = title_map.get(t)
                if mv:
                    matched_movies.append(mv)
    else:
        matched_movies = all_movies_list

    movies = []
    for movie in matched_movies:
        movie_id_str = str(movie['_id'])

        # Check if this movie has any future showtimes (for display purposes)
        future_showtimes_count = main_bp.mongo.db.showtimes.count_documents({
            'movie_id': movie_id_str,
            'status': 'active',
            '$or': [
                {'show_date': {'$gt': current_date}},
                {
                    'show_date': current_date,
                    'show_time': {'$gte': current_time}
                }
            ]
        })

        # Basic movie fields for template
        movie['_id'] = movie_id_str

        # Compute average rating and review count
        agg = list(main_bp.mongo.db.reviews.aggregate([
            {'$match': {'movie_id': movie_id_str}},
            {'$group': {'_id': '$movie_id', 'avg': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
        ]))
        movie['avg_rating'] = round(agg[0]['avg'], 1) if agg else None
        movie['reviews_count'] = agg[0]['count'] if agg else 0

        # Mark whether movie currently has upcoming shows
        movie['has_show'] = future_showtimes_count > 0

        movies.append(movie)
    
    # Sort movies: 1) Latest first (today/tomorrow/upcoming shows), 2) Released movies, 3) Future releases
    def get_movie_sort_key(m):
        rd = m.get('release_date')
        try:
            release_date = datetime.strptime(rd, '%Y-%m-%d').date() if rd else datetime.max.date()
        except Exception:
            release_date = datetime.max.date()
        
        today = datetime.now().date()
        days_diff = (release_date - today).days
        
        # Category 1: Movies with shows in next 3 days (priority: 0-2)
        if 0 <= days_diff <= 2:
            return (0, days_diff, release_date)  # Latest first (today=0, tomorrow=1, day after=2)
        # Category 2: Already released movies (priority: 1)
        elif days_diff < 0:
            return (1, -days_diff, release_date)  # Most recent releases first
        # Category 3: Future releases (priority: 2)
        else:
            return (2, days_diff, release_date)  # Nearest future releases first
    
    movies.sort(key=get_movie_sort_key)
    # If a search was performed but returned no matches, prepare suggestions
    suggestions = []
    no_results = False
    if q and not movies:
        no_results = True
        # suggest close title matches even if cutoff low
        try:
            titles = list(title_map.keys())
            close = difflib.get_close_matches(q_low, titles, n=5, cutoff=0.5)
            for t in close:
                mv = title_map.get(t)
                if mv:
                    suggestions.append(mv.get('title'))
        except Exception:
            suggestions = []
    
    # Get user data if logged in
    user_data = None
    if user_logged_in:
        user_data = main_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    return render_template('movies.html', logged_in=user_logged_in, username=username, movies=movies, user_data=user_data, search_query=search_query, suggestions=suggestions, no_results=no_results, status_filter=status_filter)


@main_bp.route('/about')
def about():
    """About page route"""
    user_logged_in = 'user_id' in session
    username = session.get('username', '')

    user_data = None
    if user_logged_in:
        user_data = main_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

    return render_template('about.html', logged_in=user_logged_in, username=username, user_data=user_data)
