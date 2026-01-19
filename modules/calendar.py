"""
Google Calendar integration blueprint
Handles OAuth for calendar scope, token storage, and server-side event creation
"""
from flask import Blueprint, request, redirect, url_for, session, flash, jsonify, current_app
from oauthlib.oauth2 import WebApplicationClient
import requests
from datetime import datetime, timedelta
from bson import ObjectId

calendar_bp = Blueprint('calendar', __name__)

def init_calendar(mongo, google_config=None):
    """Initialize calendar blueprint with mongo and google config"""
    calendar_bp.mongo = mongo
    calendar_bp.GOOGLE_CLIENT_ID = google_config.get('client_id') if google_config else None
    calendar_bp.GOOGLE_CLIENT_SECRET = google_config.get('client_secret') if google_config else None
    calendar_bp.GOOGLE_DISCOVERY_URL = google_config.get('discovery_url') if google_config else None
    if calendar_bp.GOOGLE_CLIENT_ID:
        calendar_bp.client = WebApplicationClient(calendar_bp.GOOGLE_CLIENT_ID)
    else:
        calendar_bp.client = None
    return calendar_bp


def get_google_provider_cfg(discovery_url):
    try:
        return requests.get(discovery_url).json()
    except Exception:
        return None


@calendar_bp.route('/calendar/connect')
def calendar_connect():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))

    # Ensure the user originally signed in with Google (has google_id)
    try:
        user = calendar_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    except Exception:
        user = None

    if not user or not user.get('google_id'):
        flash('Please sign in with Google to connect your calendar. Use "Sign in with Google" in Settings.', 'error')
        return redirect(url_for('user.settings'))

    if not calendar_bp.client or not calendar_bp.GOOGLE_DISCOVERY_URL:
        flash('Google Calendar is not configured.', 'error')
        return redirect(url_for('main.index'))

    google_cfg = get_google_provider_cfg(calendar_bp.GOOGLE_DISCOVERY_URL)
    if not google_cfg:
        flash('Unable to reach Google.', 'error')
        return redirect(url_for('main.index'))

    authorization_endpoint = google_cfg['authorization_endpoint']
    request_uri = calendar_bp.client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('calendar.calendar_callback', _external=True, _scheme='http'),
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar.events"],
        access_type='offline',
        prompt='consent'
    )


@calendar_bp.route('/calendar/oauth2callback')
def calendar_callback():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))

    if not calendar_bp.client or not calendar_bp.GOOGLE_DISCOVERY_URL:
        flash('Google Calendar is not configured.', 'error')
        return redirect(url_for('main.index'))

    code = request.args.get('code')
    if not code:
        flash('Google authorization failed.', 'error')
        return redirect(url_for('main.index'))

    google_cfg = get_google_provider_cfg(calendar_bp.GOOGLE_DISCOVERY_URL)
    token_endpoint = google_cfg['token_endpoint']

    token_url, headers, body = calendar_bp.client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for('calendar.calendar_callback', _external=True, _scheme='http'),
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(calendar_bp.GOOGLE_CLIENT_ID, calendar_bp.GOOGLE_CLIENT_SECRET),
    )
    token_json = token_response.json()

    access_token = token_json.get('access_token')
    refresh_token = token_json.get('refresh_token')
    expires_in = token_json.get('expires_in')

    if not access_token:
        flash('Failed to obtain access token from Google.', 'error')
        return redirect(url_for('main.index'))

    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else datetime.utcnow() + timedelta(hours=1)

    # Store tokens in user's document
    try:
        user = calendar_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            token_store = {
                'access_token': access_token,
                'refresh_token': refresh_token or user.get('google_tokens', {}).get('refresh_token'),
                'expires_at': expires_at
            }
            calendar_bp.mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'google_tokens': token_store}})
            flash('Google Calendar connected successfully.', 'success')
    except Exception:
        flash('Failed to save Google tokens.', 'error')

    return redirect(url_for('main.index'))


def refresh_access_token(user_tokens):
    # If refresh token not available, cannot refresh
    if not user_tokens or not user_tokens.get('refresh_token'):
        return None
    google_cfg = get_google_provider_cfg(calendar_bp.GOOGLE_DISCOVERY_URL)
    token_endpoint = google_cfg['token_endpoint']
    resp = requests.post(
        token_endpoint,
        data={
            'client_id': calendar_bp.GOOGLE_CLIENT_ID,
            'client_secret': calendar_bp.GOOGLE_CLIENT_SECRET,
            'refresh_token': user_tokens.get('refresh_token'),
            'grant_type': 'refresh_token'
        }
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    access_token = data.get('access_token')
    expires_in = data.get('expires_in')
    if access_token:
        user_tokens['access_token'] = access_token
        user_tokens['expires_at'] = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else datetime.utcnow() + timedelta(hours=1)
        return user_tokens
    return None


@calendar_bp.route('/calendar/add_event/<booking_id>', methods=['POST'])
def add_event(booking_id):
    # Add event to user's Google Calendar
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    user = calendar_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    tokens = user.get('google_tokens')
    if not tokens:
        return jsonify({'success': False, 'error': 'Google Calendar not connected'}), 400

    # Refresh token if expired or near expiry
    try:
        expires_at = tokens.get('expires_at')
        if isinstance(expires_at, str):
            # stored as ISO string
            expires_at_dt = datetime.fromisoformat(expires_at)
        elif isinstance(expires_at, datetime):
            expires_at_dt = expires_at
        else:
            expires_at_dt = None
    except Exception:
        expires_at_dt = None

    if not expires_at_dt or (expires_at_dt - datetime.utcnow()).total_seconds() < 60:
        refreshed = refresh_access_token(tokens)
        if not refreshed:
            return jsonify({'success': False, 'error': 'Failed to refresh Google tokens. Please reconnect.'}), 400
        # save refreshed tokens
        calendar_bp.mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'google_tokens': refreshed}})
        tokens = refreshed

    access_token = tokens.get('access_token')
    if not access_token:
        return jsonify({'success': False, 'error': 'No access token available'}), 400

    # Fetch booking details
    booking = calendar_bp.mongo.db.bookings.find_one({'_id': ObjectId(booking_id), 'user_id': session['user_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    # Use showtime's stored date/time for event start; fall back to booking fields if needed
    showtime = None
    try:
        showtime = calendar_bp.mongo.db.showtimes.find_one({'_id': ObjectId(booking.get('showtime_id'))})
    except Exception:
        showtime = None

    movie = None
    theatre = None
    if showtime:
        try:
            movie = calendar_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
        except Exception:
            movie = None
        try:
            theatre = calendar_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
        except Exception:
            theatre = None

    # Prepare event start datetime using showtime if available, otherwise try booking fields, otherwise now
    start_dt = None
    if showtime and showtime.get('show_date') and showtime.get('show_time'):
        try:
            start_dt = datetime.strptime(f"{showtime['show_date']} {showtime['show_time']}", '%Y-%m-%d %H:%M')
        except Exception:
            start_dt = None

    if not start_dt:
        try:
            start_dt = datetime.strptime(f"{booking.get('show_date', '')} {booking.get('show_time', '')}", '%Y-%m-%d %H:%M')
        except Exception:
            start_dt = datetime.utcnow()
    duration_min = int(movie.get('duration', 120)) if movie and movie.get('duration') else 120
    end_dt = start_dt + timedelta(minutes=duration_min)

    event = {
        'summary': f"{movie.get('title','Movie')} - {theatre.get('name','')}",
        'location': f"{theatre.get('name','')}, {theatre.get('city','')}" if theatre else '',
        'description': f"Booking ID: {booking.get('_id')}\nSeats: {', '.join(booking.get('seats', []))}\nBooked via BookNow",
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60},
                {'method': 'popup', 'minutes': 10}
            ]
        }
    }

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    resp = requests.post('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, json=event)
    if resp.status_code in (200, 201):
        data = resp.json()
        # Save event id on booking so button remains disabled across reloads
        try:
            event_id = data.get('id')
            html_link = data.get('htmlLink')
            calendar_bp.mongo.db.bookings.update_one({'_id': ObjectId(booking_id)}, {'$set': {'calendar_event_id': event_id, 'calendar_html_link': html_link}})
        except Exception:
            pass
        return jsonify({'success': True, 'event_id': data.get('id'), 'htmlLink': data.get('htmlLink')}), 200
    else:
        return jsonify({'success': False, 'error': 'Google API error', 'details': resp.text}), resp.status_code


@calendar_bp.route('/calendar/disconnect', methods=['POST'])
def calendar_disconnect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    try:
        calendar_bp.mongo.db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$unset': {'google_tokens': ''}})
        return jsonify({'success': True}), 200
    except Exception:
        return jsonify({'success': False, 'error': 'Failed to disconnect'}), 500
