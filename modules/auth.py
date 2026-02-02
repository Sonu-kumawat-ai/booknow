"""
Authentication routes module
Handles user registration, login, and logout with OTP verification and Google OAuth
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from bson import ObjectId
import random
import string
import requests
import json
import os
from oauthlib.oauth2 import WebApplicationClient

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

auth_bp = Blueprint('auth', __name__)
mail = None
google_client = None
GOOGLE_CLIENT_ID = None
GOOGLE_CLIENT_SECRET = None
GOOGLE_DISCOVERY_URL = None

def init_auth(mongo, mail_instance, google_config=None):
    """Initialize auth blueprint with mongo, mail, and google oauth instances"""
    global mail, google_client, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_DISCOVERY_URL
    auth_bp.mongo = mongo
    mail = mail_instance
    
    if google_config:
        GOOGLE_CLIENT_ID = google_config.get('client_id')
        GOOGLE_CLIENT_SECRET = google_config.get('client_secret')
        GOOGLE_DISCOVERY_URL = google_config.get('discovery_url')
        google_client = WebApplicationClient(GOOGLE_CLIENT_ID)
    
    return auth_bp

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp, username):
    """Send OTP verification email"""
    try:
        msg = Message(
            subject='BookNow - Email Verification OTP',
            recipients=[email]
        )
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: #2b2d42; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Book<span style="color: #e63946;">Now</span></h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 5px;">
                        <h2 style="color: #2b2d42;">Welcome to BookNow, {username}!</h2>
                        <p>Thank you for registering with us. To complete your registration, please verify your email address.</p>
                        <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; text-align: center; border-radius: 5px;">
                            <p style="margin: 0; font-size: 14px; color: #666;">Your verification code is:</p>
                            <h1 style="margin: 10px 0; color: #e63946; font-size: 36px; letter-spacing: 5px;">{otp}</h1>
                        </div>
                        <p><strong>This OTP will expire in 10 minutes.</strong></p>
                        <p>If you didn't request this verification, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #666; text-align: center;">
                            This is an automated email. Please do not reply.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page route with inline OTP verification"""
    if request.method == 'POST':
        step = request.form.get('step', 'register')
        
        if step == 'register':
            # Step 1: Initial registration
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not username or not email or not password:
                flash('All fields are required!', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('register.html')
            
            # Check if user already exists
            existing_user = auth_bp.mongo.db.users.find_one({'$or': [{'email': email}, {'username': username}]})
            if existing_user:
                flash('Username or email already exists!', 'error')
                return render_template('register.html')
            
            # Generate OTP
            otp = generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Store temporary registration data in session
            session['pending_registration'] = {
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'otp': otp,
                'otp_expiry': otp_expiry.isoformat()
            }
            
            # Send OTP email
            if send_otp_email(email, otp, username):
                flash('OTP has been sent to your email. Please verify to complete registration.', 'success')
                return redirect(url_for('auth.register', verify='true'))
            else:
                flash('Failed to send verification email. Please try again.', 'error')
                return render_template('register.html')
        
        elif step == 'verify':
            # Step 2: OTP verification
            if 'pending_registration' not in session:
                flash('No pending registration found. Please register first.', 'error')
                return redirect(url_for('auth.register'))
            
            entered_otp = request.form.get('otp')
            pending_data = session['pending_registration']
            
            # Check if OTP expired
            otp_expiry = datetime.fromisoformat(pending_data['otp_expiry'])
            if datetime.utcnow() > otp_expiry:
                session.pop('pending_registration', None)
                flash('OTP has expired. Please register again.', 'error')
                return redirect(url_for('auth.register'))
            
            # Verify OTP
            if entered_otp == pending_data['otp']:
                # Create user account
                user_data = {
                    'username': pending_data['username'],
                    'email': pending_data['email'],
                    'password': pending_data['password'],
                    'role': 'user',
                    'created_at': datetime.utcnow(),
                    'email_verified': True
                }
                
                auth_bp.mongo.db.users.insert_one(user_data)
                session.pop('pending_registration', None)
                flash('Email verified successfully! You can now login.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Invalid OTP. Please try again.', 'error')
                return redirect(url_for('auth.register', verify='true'))
    
    # GET request - check if we should show OTP section
    verify = request.args.get('verify')
    if verify == 'true' and 'pending_registration' in session:
        # Pre-fill the form with session data for OTP verification
        return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to email"""
    if 'pending_registration' not in session:
        return jsonify({'success': False, 'message': 'No pending registration found'}), 400
    
    pending_data = session['pending_registration']
    
    # Generate new OTP
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Update session
    pending_data['otp'] = otp
    pending_data['otp_expiry'] = otp_expiry.isoformat()
    session['pending_registration'] = pending_data
    
    # Send OTP email
    if send_otp_email(pending_data['email'], otp, pending_data['username']):
        return jsonify({'success': True, 'message': 'New OTP has been sent to your email'}), 200
    else:
        return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if not email or not password:
            flash('Email and password are required!', 'error')
            return render_template('login.html')
        
        # Find user
        user = auth_bp.mongo.db.users.find_one({'email': email})
        
        if user:
            # Check if user has a password set (not just Google-only account)
            if user.get('password') and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                flash('Login successful!', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Invalid email or password!', 'error')
                return render_template('login.html')
        else:
            flash('Invalid email or password!', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

# Google OAuth Routes
def get_google_provider_cfg():
    """Get Google's provider configuration"""
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except Exception as e:
        print(f"Error fetching Google provider config: {str(e)}")
        return None

@auth_bp.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    if not google_client or not GOOGLE_CLIENT_ID:
        flash('Google sign-in is not configured.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get Google's provider configuration
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash('Unable to connect to Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Construct the request for Google login
    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('auth.google_callback', _external=True, _scheme='http'),
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@auth_bp.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    if not google_client or not GOOGLE_CLIENT_ID:
        flash('Google sign-in is not configured.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get authorization code from Google
    code = request.args.get("code")
    if not code:
        flash('Google sign-in failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get Google's provider configuration
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash('Unable to connect to Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Prepare token request
    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for('auth.google_callback', _external=True, _scheme='http'),
        code=code
    )
    
    # Get tokens from Google
    try:
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        # Parse the tokens
        google_client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = google_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        if userinfo_response.json().get("email_verified"):
            google_id = userinfo_response.json()["sub"]
            email = userinfo_response.json()["email"]
            name = userinfo_response.json().get("name", email.split('@')[0])
            picture = userinfo_response.json().get("picture")
            
            # Check if user exists by email
            user = auth_bp.mongo.db.users.find_one({'email': email})
            
            if user:
                # User exists - link Google account if not already linked
                update_data = {'last_login': datetime.utcnow()}
                
                if not user.get('google_id'):
                    # First time linking Google account to existing email/password account
                    update_data['google_id'] = google_id
                    update_data['profile_picture'] = picture
                    flash('Google account linked successfully! You can now login with either method.', 'success')
                else:
                    # Already linked - just logging in
                    flash('Welcome back!', 'success')
                
                auth_bp.mongo.db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': update_data}
                )
                
                # Log in the user
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
            else:
                # New user - create account with Google
                new_user = {
                    'username': name,
                    'email': email,
                    'password': generate_password_hash(google_id + email),  # Set a password for potential future use
                    'google_id': google_id,
                    'profile_picture': picture,
                    'role': 'user',
                    'created_at': datetime.utcnow(),
                    'last_login': datetime.utcnow(),
                    'email_verified': True
                }
                
                result = auth_bp.mongo.db.users.insert_one(new_user)
                
                # Log in the new user
                session['user_id'] = str(result.inserted_id)
                session['username'] = name
                flash('Account created successfully! Welcome to BookNow!', 'success')
            
            return redirect(url_for('main.index'))
        else:
            flash('Email not verified by Google. Please use a verified email.', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        flash('An error occurred during Google sign-in. Please try again.', 'error')
        return redirect(url_for('auth.login'))
