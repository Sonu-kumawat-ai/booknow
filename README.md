# 🎬 BookNow - Movie Ticket Booking Platform

A comprehensive movie ticket booking web application built with Flask, MongoDB, and modern web technologies. BookNow provides a seamless experience for users to browse movies, select seats, and book tickets online.

## ✨ Features

### For Users
- 🔐 **User Authentication** - Registration with OTP verification, Login, and Google OAuth integration
- 🎥 **Movie Browsing** - Browse movies in two categories:
  - **🎬 In Theatres** - Movies currently available for booking
  - **🔜 Coming Soon** - Upcoming movie releases with release dates
- 💺 **Interactive Seat Selection** - Visual seat map with Normal (80%) and VIP (20%) sections
- 🎟️ **Online Booking** - Real-time seat availability and instant booking confirmation
- 💳 **Razorpay Payment Integration** - Secure payment processing
- 📧 **Email Notifications** - Booking confirmation emails with ticket details
- 👤 **User Profile** - View booking history and manage account settings

### For Theatre Owners
- 🏢 **Theatre Registration** - Apply to become a theatre owner with detailed information
- 🎬 **Movie Management** - Add showtimes to movies with "in theatre" status
  - Cannot add showtimes to upcoming movies (releases in >7 days)
- 📊 **Dashboard** - View all upcoming shows, screens, and booking statistics
- ⏰ **Smart Scheduling** - Automatic conflict detection prevents overlapping shows
- 💰 **Dynamic Pricing** - Set different prices for Normal and VIP seats per showtime
- 📺 **Multi-Screen Support** - Manage multiple screens with individual capacities

### For Admins
- 🛡️ **Admin Panel** - Manage theatre owner applications and approvals
- 🎭 **Movie Management** - Add movies as "upcoming" or "in theatre" based on release date
  - Movies with release dates >7 days away are automatically marked as "upcoming"
  - Movies automatically switch to "in theatre" status 7 days before release
- 📈 **Analytics** - View platform statistics including theatre/upcoming movie counts

## 🛠️ Technologies Used

### Backend
- **Flask 3.0.0** - Python web framework
- **MongoDB** - NoSQL database with MongoDB Atlas
- **PyMongo** - MongoDB driver for Python
- **Flask-Mail** - Email functionality for OTP and confirmations
- **Razorpay** - Payment gateway integration
- **Google OAuth 2.0** - Social login integration

### Frontend
- **HTML5 & CSS3** - Modern, responsive design
- **JavaScript (Vanilla)** - Interactive features without frameworks
- **CSS Variables** - Theme customization
- **Responsive Design** - Mobile-friendly interface

### Key Libraries
```
Flask==3.0.0
Flask-PyMongo==2.3.0
Flask-Mail==0.9.1
razorpay==1.4.2
python-dotenv==1.0.1
requests==2.31.0
oauthlib==3.2.2
pyOpenSSL==24.0.0
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB Atlas account (or local MongoDB)
- Gmail account (for SMTP)
- Razorpay account (for payments)
- Google Cloud Console project (for OAuth)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/booknow.git
cd booknow
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# MongoDB Configuration
MONGODB_URI=your-mongodb-atlas-connection-string

# Razorpay Configuration
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Email Configuration (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Allow OAuth over HTTP for local development
OAUTHLIB_INSECURE_TRANSPORT=1
```

### Step 5: Set Up Gmail App Password
1. Enable 2-Factor Authentication on your Gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password
4. Use this password in `MAIL_PASSWORD` in `.env`

### Step 6: Set Up Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:5000/login/google/callback`
6. Copy Client ID and Client Secret to `.env`

### Step 7: Set Up Razorpay
1. Sign up at [Razorpay](https://razorpay.com/)
2. Get your Test API Keys
3. Add them to `.env` file

### Step 8: Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.


## 🎯 Key Features Explained

### Seat Selection System
- **Layout**: 2-6-2 pattern with aisles (2 seats - aisle - 6 seats - aisle - 2 seats)
- **Pricing**: Normal seats (first 80% of capacity), VIP seats (last 20%)
- **Row Labels**: A-Z labels on both sides
- **Real-time Availability**: Booked seats are disabled and grayed out

### Show Scheduling
- **Smart Conflict Detection**: Prevents overlapping shows in the same screen
- **Buffer Time**: Automatic 30-minute buffer after each show for cleaning
- **Multi-Screen Support**: Each show can be assigned to different screens
- **Dynamic Pricing**: Different prices for each showtime

### Payment Flow
1. User selects seats
2. Proceeds to payment
3. Razorpay payment gateway
4. Payment verification
5. Booking confirmation
6. Email ticket sent

### Authentication
- **Email/Password**: Traditional registration with OTP verification
- **Google OAuth**: One-click sign-in with Google
- **Session Management**: Secure session handling

## 🔒 Security Features

- Password hashing with Werkzeug
- OTP expiry (10 minutes)
- Session-based authentication
- CSRF protection
- Input validation
- Secure payment processing

## 📊 Database Collections

- **users** - User accounts and profiles
- **movies** - Movie information
- **theatres** - Theatre details
- **screens** - Theatre screens
- **showtimes** - Movie showtimes
- **bookings** - Ticket bookings
- **booking_seats** - Individual seat bookings
- **payments** - Payment records
- **theatre_owner_applications** - Theatre owner requests
- **sessions** - User sessions

## 🎨 Design Features

- Modern gradient design with red (#E63946) and yellow (#FFD166) theme
- Responsive layout for all devices
- Interactive hero rotator
- Smooth animations and transitions
- Consistent footer across all pages
- Flash messages for user feedback

## 🚦 Usage

### As a User
1. Register/Login to your account
2. Browse available movies
3. Select a movie and showtime
4. Choose your seats
5. Proceed to payment
6. Receive booking confirmation via email

### As a Theatre Owner
1. Apply for theatre owner account
2. Wait for admin approval
3. Add movies with showtimes
4. Manage shows from dashboard
5. View booking statistics

### As an Admin
1. Login with admin credentials
2. Review theatre owner applications
3. Approve/reject applications
4. Add movies to any theatre
5. Monitor platform activity

## 🔮 Future Enhancements

- [ ] Revenue analytics for theatre owners
- [ ] Movie ratings and reviews
- [ ] Mobile app (React Native)
- [ ] Multiple payment gateways
- [ ] Seat map customization
- [ ] QR code tickets
- [ ] Push notifications
- [ ] Loyalty program

## 👨‍💻 Author

**Sonu Kumawat**
- Email: kumawatsonu086@gmail.com
- GitHub: [@yourusername](https://github.com/yourusername)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Flask documentation and community
- MongoDB Atlas for cloud database
- Razorpay for payment integration
- Google for OAuth services
- Unsplash for placeholder images

## 📞 Support

For support, email kumawatsonu086@gmail.com or create an issue in the repository.

---

Made with ❤️ by Sonu Kumawat
