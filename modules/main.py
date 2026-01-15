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
    user_logged_in = 'user_id' in session
    username = session.get('username', '')
    # Fetch movies from database
    movies = list(main_bp.mongo.db.movies.find())
    
    # Convert ObjectId to string for URLs
    for movie in movies:
        movie['_id'] = str(movie['_id'])
    
    # Get user data if logged in
    user_data = None
    if user_logged_in:
        user_data = main_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    return render_template('index.html', logged_in=user_logged_in, username=username, movies=movies, user_data=user_data)
