# BookNow - Movie Booking Website

A modern movie booking website built with Flask, MongoDB Atlas, and responsive frontend design.

## Features

- 🎬 Modern and responsive UI with smooth animations
- 🔐 User authentication (Register & Login)
- 📱 Mobile-friendly design
- 🎨 Custom color theme with red and yellow accents
- 🔄 Auto-rotating hero carousel
- 💾 MongoDB Atlas database integration
- 🎟️ Movie browsing section
- ⭐ Feature showcase section

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB Atlas
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Werkzeug Security

## Project Structure

```
Book/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   └── register.html     # Registration page
└── static/               # Static files
    ├── css/
    │   └── style.css     # Main stylesheet
    └── js/
        └── main.js       # JavaScript functionality
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (free tier available at https://www.mongodb.com/cloud/atlas)

### Step 1: Create Virtual Environment

```powershell
# Navigate to the project directory
cd e:\sonu\Book

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
# Install required packages
pip install -r requirements.txt
```

### Step 3: Configure MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Create a database user with username and password
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get your connection string

### Step 4: Update Database Configuration

Open `app.py` and update the MongoDB connection string on line 11:

```python
app.config["MONGO_URI"] = "mongodb+srv://<username>:<password>@<cluster-url>/<database>?retryWrites=true&w=majority"
```

Replace:
- `<username>` with your MongoDB username
- `<password>` with your MongoDB password
- `<cluster-url>` with your cluster URL
- `<database>` with your database name (e.g., "booknow")

Example:
```python
app.config["MONGO_URI"] = "mongodb+srv://myuser:mypassword@cluster0.mongodb.net/booknow?retryWrites=true&w=majority"
```

### Step 5: Run the Application

```powershell
# Make sure virtual environment is activated
python app.py
```

The application will start at `http://127.0.0.1:5000/`

## User Flow

1. **Home Page** (`/`) - Browse movies and features
2. **Register** (`/register`) - Create a new account
3. **Login** (`/login`) - Sign in with credentials
4. **Authenticated Home** - Access personalized features

## Color Theme

The website uses a vibrant color palette:

- **Primary Red**: #E63946
- **Primary Yellow**: #FFD166
- **Dark Red**: #D62828
- **Light Yellow**: #FFF4D9
- **Text Dark**: #2B2D42
- **Success Green**: #06D6A0
- **Info Blue**: #118AB2

## Development

### File Descriptions

- **app.py**: Main Flask application with routes for home, login, register, and logout
- **templates/index.html**: Home page with navbar, hero carousel, movies section, features, and footer
- **templates/login.html**: User login page with form validation
- **templates/register.html**: User registration page with password confirmation
- **static/css/style.css**: Complete styling with CSS variables and responsive design
- **static/js/main.js**: Interactive features including carousel, smooth scrolling, and form validation

### Security Notes

- Change the `app.secret_key` in `app.py` before deploying to production
- Never commit your MongoDB credentials to version control
- Use environment variables for sensitive data in production

## Deployment

For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server like Gunicorn
3. Set up environment variables for sensitive data
4. Configure proper security headers
5. Use HTTPS

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is for educational purposes.

## Support

For issues or questions, please check the code comments or Flask documentation at https://flask.palletsprojects.com/
