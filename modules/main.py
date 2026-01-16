"""
Main routes module
Handles home page and basic pages
"""
from flask import Blueprint, render_template, session
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
    
    user_logged_in = 'user_id' in session
    username = session.get('username', '')
    
    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')
    
    # Fetch all movies
    all_movies = list(main_bp.mongo.db.movies.find())
    
    # Filter movies that have at least one future showtime
    movies = []
    for movie in all_movies:
        # Check if this movie has any future showtimes
        future_showtimes_count = main_bp.mongo.db.showtimes.count_documents({
            'movie_id': str(movie['_id']),
            'status': 'active',
            '$or': [
                {'show_date': {'$gt': current_date}},
                {
                    'show_date': current_date,
                    'show_time': {'$gte': current_time}
                }
            ]
        })
        
        if future_showtimes_count > 0:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
    
    # Limit to 3 latest movies for home page
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
    
    user_logged_in = 'user_id' in session
    username = session.get('username', '')
    
    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')
    
    # Fetch all movies
    all_movies_list = list(main_bp.mongo.db.movies.find())
    
    # Filter movies that have at least one future showtime
    movies = []
    for movie in all_movies_list:
        # Check if this movie has any future showtimes
        future_showtimes_count = main_bp.mongo.db.showtimes.count_documents({
            'movie_id': str(movie['_id']),
            'status': 'active',
            '$or': [
                {'show_date': {'$gt': current_date}},
                {
                    'show_date': current_date,
                    'show_time': {'$gte': current_time}
                }
            ]
        })
        
        if future_showtimes_count > 0:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
    
    # Get user data if logged in
    user_data = None
    if user_logged_in:
        user_data = main_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    return render_template('movies.html', logged_in=user_logged_in, username=username, movies=movies, user_data=user_data)
