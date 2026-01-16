"""
Main Flask application file
Imports and registers all route blueprints
"""
from flask import Flask
from flask_pymongo import PyMongo
from flask_mail import Mail
import razorpay
from modules.config import Config
from modules.utils import format_date, format_time, format_datetime

# Import route blueprints
from modules.auth import init_auth
from modules.main import init_main
from modules.user import init_user
from modules.theatre import init_theatre
from modules.admin import init_admin
from modules.movie import init_movie
from modules.booking import init_booking

# Import database initialization
from modules.database_init import initialize_database

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Register custom Jinja2 filters
app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['format_time'] = format_time
app.jinja_env.filters['format_datetime'] = format_datetime

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))

# Google OAuth configuration
google_config = {
    'client_id': Config.GOOGLE_CLIENT_ID,
    'client_secret': Config.GOOGLE_CLIENT_SECRET,
    'discovery_url': Config.GOOGLE_DISCOVERY_URL
}

# Initialize and register blueprints
auth_blueprint = init_auth(mongo, mail, google_config)
main_blueprint = init_main(mongo)
user_blueprint = init_user(mongo)
theatre_blueprint = init_theatre(mongo)
admin_blueprint = init_admin(mongo)
movie_blueprint = init_movie(mongo)
booking_blueprint = init_booking(mongo, razorpay_client, Config.RAZORPAY_KEY_ID, mail)

# Register blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(theatre_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(movie_blueprint)
app.register_blueprint(booking_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
