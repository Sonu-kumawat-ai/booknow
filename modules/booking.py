"""
Booking routes module
Handles seat selection and booking process
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Message
from datetime import datetime, timedelta
from bson import ObjectId
import razorpay
from modules.utils import format_date, format_time

booking_bp = Blueprint('booking', __name__)
mail = None

def init_booking(mongo, razorpay_client, razorpay_key_id, mail_instance):
    """Initialize booking blueprint with mongo, razorpay, and mail instances"""
    global mail
    booking_bp.mongo = mongo
    booking_bp.razorpay_client = razorpay_client
    booking_bp.razorpay_key_id = razorpay_key_id
    mail = mail_instance
    return booking_bp

def send_booking_confirmation_email(email, username, booking_details):
    """Send booking confirmation email with ticket details - ONLY called after payment success"""
    try:
        print(f"Sending booking confirmation email to {email} for booking {booking_details.get('booking_id')}")
        
        msg = Message(
            subject='🎟️ Booking Confirmed - BookNow',
            recipients=[email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .email-header {{
                    background-color: #E63946;
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .email-header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .email-body {{
                    padding: 30px;
                }}
                .booking-info {{
                    background-color: #f9f9f9;
                    border-left: 4px solid #FFD166;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .booking-info p {{
                    margin: 10px 0;
                    color: #333;
                }}
                .booking-info strong {{
                    color: #E63946;
                }}
                .seat-info {{
                    background-color: #fff4d9;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .footer {{
                    background-color: #2d3748;
                    color: white;
                    text-align: center;
                    padding: 20px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>🎟️ Booking Confirmed!</h1>
                </div>
                <div class="email-body">
                    <p>Dear {username},</p>
                    <p>Your movie ticket booking has been confirmed successfully. Here are your booking details:</p>
                    
                    <div class="booking-info">
                        <p><strong>Booking ID:</strong> {booking_details['booking_id']}</p>
                        <p><strong>Movie:</strong> {booking_details['movie_title']}</p>
                        <p><strong>Theatre:</strong> {booking_details['theatre_name']}</p>
                        <p><strong>Location:</strong> {booking_details['location']}</p>
                        <p><strong>Screen:</strong> {booking_details['screen_name']}</p>
                        <p><strong>Show Date:</strong> {format_date(booking_details['show_date'])}</p>
                        <p><strong>Show Time:</strong> {format_time(booking_details['show_time'])}</p>
                    </div>
                    
                    <div class="seat-info">
                        <p><strong>Seat Numbers:</strong> {booking_details['seats']}</p>
                        <p><strong>Total Tickets:</strong> {booking_details['total_tickets']}</p>
                        <p><strong>Total Amount Paid:</strong> ₹{booking_details['total_amount']}</p>
                    </div>
                    
                    <p>Please arrive at the theatre at least 15 minutes before the show time.</p>
                    <p>Show this email or your booking ID at the theatre counter to collect your tickets.</p>
                    
                    <p style="margin-top: 30px;">Thank you for choosing BookNow!</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                    <p>&copy; 2026 BookNow. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"✓ Booking confirmation email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"✗ Error sending booking confirmation email to {email}: {str(e)}")
        return False

@booking_bp.route('/book-seats/<showtime_id>')
def book_seats(showtime_id):
    """Seat selection page"""
    if 'user_id' not in session:
        flash('Please login to book tickets.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Try to convert to ObjectId
        try:
            obj_id = ObjectId(showtime_id)
        except Exception:
            flash('Invalid showtime ID format.', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch showtime details
        showtime = booking_bp.mongo.db.showtimes.find_one({'_id': obj_id})
        
        if not showtime:
            flash('Showtime not found.', 'error')
            return redirect(url_for('main.index'))
        
        if showtime.get('status') != 'active':
            flash('Showtime not found or inactive.', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch movie details
        movie = booking_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
        if not movie:
            flash('Movie not found.', 'error')
            return redirect(url_for('main.index'))
        
        # Get theatre and screen details
        theatre = booking_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
        screen = booking_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
        
        # Get user data
        user_data = booking_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        # Get already booked seats for this showtime
        booked_seats = list(booking_bp.mongo.db.booking_seats.find({
            'showtime_id': showtime_id,
            'status': 'booked'
        }))
        # Convert seat numbers to integers for consistent comparison in JavaScript
        booked_seat_numbers = []
        for seat in booked_seats:
            seat_num = seat['seat_number']
            # Convert to int if it's a string number, otherwise keep as is
            if isinstance(seat_num, str) and seat_num.isdigit():
                booked_seat_numbers.append(int(seat_num))
            elif isinstance(seat_num, int):
                booked_seat_numbers.append(seat_num)
            else:
                # Extract digits from string
                digits = ''.join(filter(str.isdigit, str(seat_num)))
                if digits:
                    booked_seat_numbers.append(int(digits))
        
        return render_template('seat_selection.html',
                             movie=movie,
                             showtime=showtime,
                             theatre=theatre,
                             screen=screen,
                             user_data=user_data,
                             logged_in=True,
                             username=session.get('username', ''),
                             booked_seats=booked_seat_numbers)
    except Exception:
        flash('Invalid showtime ID.', 'error')
        return redirect(url_for('main.index'))

@booking_bp.route('/payment/<showtime_id>')
def payment(showtime_id):
    """Payment page"""
    if 'user_id' not in session:
        flash('Please login to book tickets.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get seats from query parameters
    seats_str = request.args.get('seats', '')
    
    if not seats_str:
        flash('Invalid booking data.', 'error')
        return redirect(url_for('booking.book_seats', showtime_id=showtime_id))
    
    try:
        # Parse seats
        seats = seats_str.split(',')
        
        # Fetch showtime details
        showtime = booking_bp.mongo.db.showtimes.find_one({'_id': ObjectId(showtime_id)})
        
        if not showtime:
            flash('Showtime not found.', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch movie details
        movie = booking_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
        
        if not movie:
            flash('Movie not found.', 'error')
            return redirect(url_for('main.index'))
        
        # Get theatre and screen details
        theatre = booking_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
        screen = booking_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
        
        # Get user data
        user_data = booking_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        # Calculate amounts
        ticket_price = showtime.get('ticket_price', 200)
        vip_price = showtime.get('vip_price', 300)
        ticket_amount = 0
        
        # Calculate based on seat class (Normal 80%, VIP 20%)
        seating_capacity = screen.get('seating_capacity', 60) if screen else 60
        normal_seats_count = int(seating_capacity * 0.8)
        
        for seat in seats:
            # Extract seat number
            seat_num = int(''.join(filter(str.isdigit, seat)))
            
            # Normal seats (1 to normal_seats_count), VIP seats (after normal_seats_count)
            if seat_num <= normal_seats_count:
                ticket_amount += ticket_price
            else:
                ticket_amount += vip_price
        
        # Calculate convenience fee (5% of ticket amount)
        convenience_fee = int(ticket_amount * 0.05)
        total_amount = ticket_amount + convenience_fee
        
        return render_template('payment.html',
                             movie=movie,
                             showtime=showtime,
                             theatre=theatre,
                             screen=screen,
                             user_data=user_data,
                             logged_in=True,
                             username=session.get('username', ''),
                             seats=seats,
                             ticket_amount=ticket_amount,
                             convenience_fee=convenience_fee,
                             total_amount=total_amount)
    except Exception:
        flash('Invalid booking data.', 'error')
        return redirect(url_for('booking.book_seats', showtime_id=showtime_id))

@booking_bp.route('/create-order', methods=['POST'])
def create_order():
    """Create Razorpay order"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        amount = int(data['amount']) * 100  # Convert to paise
        showtime_id = data['showtime_id']
        seats = data['seats']
        offer_code = data.get('offer_code')
        discount = data.get('discount', 0)
        original_amount = data.get('original_amount', data['amount'])
        
        # Create Razorpay order
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        }
        
        razorpay_order = booking_bp.razorpay_client.order.create(data=order_data)
        
        # Prepare booking data
        booking_data = {
            'user_id': session['user_id'],
            'showtime_id': showtime_id,
            'seats': seats,
            'amount': amount // 100,
            'order_id': razorpay_order['id'],
            'offer_code': offer_code,
            'discount': discount,
            'original_amount': original_amount
        }
        
        return jsonify({
            'order_id': razorpay_order['id'],
            'amount': amount,
            'razorpay_key': booking_bp.razorpay_key_id,
            'booking_data': booking_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/verify-payment', methods=['POST'])
def verify_payment():
    """Verify Razorpay payment and create booking"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        
        # CRITICAL: Verify payment signature FIRST before any booking operations
        # This ensures Razorpay payment was successful and not tampered with
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        # This will throw an exception if signature verification fails
        # No booking or email will be created if this fails
        booking_bp.razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Payment verified successfully - proceed with booking creation
        
        # Payment verified, create booking in database
        booking_data = data['booking_data']
        showtime_id = booking_data['showtime_id']
        seats = booking_data['seats']
        
        # Get showtime details
        showtime = booking_bp.mongo.db.showtimes.find_one({'_id': ObjectId(showtime_id)})
        if not showtime:
            return jsonify({'success': False, 'error': 'Showtime not found'}), 404
        
        # Check if any of the selected seats are already booked
        already_booked = list(booking_bp.mongo.db.booking_seats.find({
            'showtime_id': showtime_id,
            'seat_number': {'$in': seats},
            'status': 'booked'
        }))
        
        if already_booked:
            booked_seat_nums = [seat['seat_number'] for seat in already_booked]
            return jsonify({
                'success': False, 
                'error': f"Seats {', '.join(map(str, booked_seat_nums))} are already booked. Please select different seats."
            }), 400
        
        # Create booking
        booking = {
            'user_id': booking_data['user_id'],
            'showtime_id': showtime_id,
            'total_seats': len(seats),
            'total_amount': booking_data['amount'],
            'original_amount': booking_data.get('original_amount', booking_data['amount']),
            'discount': booking_data.get('discount', 0),
            'offer_code': booking_data.get('offer_code'),
            'booking_date': datetime.utcnow(),
            'status': 'confirmed'
        }
        
        booking_id = booking_bp.mongo.db.bookings.insert_one(booking).inserted_id
        
        # Update offer usage count if offer was applied
        if booking_data.get('offer_code'):
            try:
                booking_bp.mongo.db.offers.update_one(
                    {'code': booking_data['offer_code']},
                    {'$inc': {'usage_count': 1}}
                )
            except Exception:
                pass  # Don't fail booking if offer update fails
        
        # Create individual seat records
        screen = booking_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
        seating_capacity = screen.get('seating_capacity', 60) if screen else 60
        
        # Calculate normal (80%) and vip (20%) seats
        normal_seats_count = int(seating_capacity * 0.8)
        
        for seat_number in seats:
            # Convert seat_number to int for comparison
            seat_num = int(seat_number) if isinstance(seat_number, str) and seat_number.isdigit() else int(''.join(filter(str.isdigit, str(seat_number))))
            
            # Normal seats (1 to normal_seats_count), VIP seats (after normal_seats_count)
            seat_type = 'normal' if seat_num <= normal_seats_count else 'vip'
            seat_price = showtime.get('ticket_price') if seat_type == 'normal' else showtime.get('vip_price')
            
            booking_seat = {
                'booking_id': str(booking_id),
                'showtime_id': showtime_id,
                'seat_number': seat_number,
                'seat_type': seat_type,
                'price': seat_price,
                'status': 'booked',
                'booked_date': datetime.utcnow()
            }
            booking_bp.mongo.db.booking_seats.insert_one(booking_seat)
        
        # Create payment record
        payment = {
            'booking_id': str(booking_id),
            'user_id': booking_data['user_id'],
            'amount': booking_data['amount'],
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'payment_method': 'razorpay',
            'payment_status': 'completed',
            'payment_date': datetime.utcnow(),
            'currency': 'INR'
        }
        payment_result = booking_bp.mongo.db.payments.insert_one(payment)
        
        # Send booking confirmation email ONLY after payment record is successfully created
        # This ensures email is sent only for completed and verified payments
        if payment_result.inserted_id:
            try:
                user = booking_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
                movie = booking_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
                theatre = booking_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
                screen = booking_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
                
                if user and user.get('email'):
                    booking_details = {
                        'booking_id': str(booking_id),
                        'movie_title': movie.get('title', 'N/A') if movie else 'N/A',
                        'theatre_name': theatre.get('name', 'N/A') if theatre else 'N/A',
                        'location': f"{theatre.get('city', '')}, {theatre.get('state', '')}" if theatre else 'N/A',
                        'screen_name': screen.get('name', 'N/A') if screen else 'N/A',
                        'show_date': showtime.get('show_date', 'N/A'),
                        'show_time': showtime.get('show_time', 'N/A'),
                        'seats': ', '.join([str(s) for s in seats]),
                        'total_tickets': len(seats),
                        'total_amount': booking_data['amount'],
                        'discount': booking_data.get('discount', 0),
                        'offer_code': booking_data.get('offer_code')
                    }
                    # Send email only after all validations and database operations succeed
                    send_booking_confirmation_email(user['email'], user.get('username', 'User'), booking_details)
                    print(f"Booking confirmation email sent to {user.get('email')} for booking {str(booking_id)}")
            except Exception as e:
                print(f"Error sending confirmation email: {str(e)}")
                # Don't fail the booking if email sending fails
        
        return jsonify({
            'success': True,
            'booking_id': str(booking_id),
            'redirect_url': url_for('booking.booking_confirmation', booking_id=str(booking_id))
        })
        
    except razorpay.errors.SignatureVerificationError as e:
        print(f"Payment signature verification FAILED: {str(e)}")
        print(f"No booking created, no email sent")
        return jsonify({'success': False, 'error': 'Payment signature verification failed'}), 400
    except Exception as e:
        print(f"Error during booking creation: {str(e)}")
        print(f"No email sent due to error")
        return jsonify({'success': False, 'error': str(e)}), 500

@booking_bp.route('/booking-confirmation/<booking_id>')
def booking_confirmation(booking_id):
    """Display booking confirmation ticket"""
    if 'user_id' not in session:
        flash('Please login to view your booking.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Fetch booking details
        booking = booking_bp.mongo.db.bookings.find_one({'_id': ObjectId(booking_id), 'user_id': session['user_id']})
        
        if not booking:
            flash('Booking not found.', 'error')
            return redirect(url_for('main.index'))
        
        # Fetch showtime details
        showtime = booking_bp.mongo.db.showtimes.find_one({'_id': ObjectId(booking['showtime_id'])})
        
        # Fetch movie details
        movie = booking_bp.mongo.db.movies.find_one({'_id': ObjectId(showtime['movie_id'])})
        
        # Get theatre and screen details
        theatre = booking_bp.mongo.db.theatres.find_one({'_id': ObjectId(showtime['theatre_id'])})
        screen = booking_bp.mongo.db.screens.find_one({'_id': ObjectId(showtime['screen_id'])})
        
        # Get booked seats for this booking
        booking_seats = list(booking_bp.mongo.db.booking_seats.find({'booking_id': str(booking['_id'])}))
        seats = [seat['seat_number'] for seat in booking_seats]
        
        # Get payment details
        payment = booking_bp.mongo.db.payments.find_one({'booking_id': str(booking['_id'])})
        
        # Add additional fields to booking for template compatibility
        booking['seats'] = seats
        booking['show_time'] = showtime.get('show_time')
        booking['show_date'] = showtime.get('show_date')
        booking['amount'] = booking.get('total_amount', 0)
        booking['payment_status'] = payment.get('payment_status', 'completed') if payment else 'completed'
        
        # Get user data for Google signup check
        user_data = None
        if 'user_id' in session:
            user_data = booking_bp.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

        # Build Google Calendar prefill URL
        try:
            from urllib.parse import quote_plus
            # Parse show start and end times
            try:
                start_dt = datetime.strptime(f"{booking['show_date']} {booking['show_time']}", '%Y-%m-%d %H:%M')
            except Exception:
                # Fallback: treat show_time as HH:MM or just use current time
                start_dt = datetime.utcnow()
            duration_min = int(movie.get('duration', 120)) if movie and movie.get('duration') else 120
            end_dt = start_dt + timedelta(minutes=duration_min)

            def fmt(dt):
                return dt.strftime('%Y%m%dT%H%M%S')

            dates = f"{fmt(start_dt)}/{fmt(end_dt)}"
            title = f"{movie.get('title', 'Movie')} - {theatre.get('name', '')}"
            details = f"Booking ID: {booking.get('_id')}\nSeats: {', '.join(booking.get('seats', []))}\nBooked via BookNow"
            location = f"{theatre.get('name', '')}, {theatre.get('city', '')}" if theatre else ''
            calendar_url = (
                'https://calendar.google.com/calendar/render?action=TEMPLATE&'
                f'text={quote_plus(title)}&dates={dates}&details={quote_plus(details)}&location={quote_plus(location)}&trp=false'
            )
        except Exception:
            calendar_url = None

        return render_template('booking_confirmation.html',
                             booking=booking,
                             movie=movie,
                             showtime=showtime,
                             theatre=theatre,
                             screen=screen,
                             username=session.get('username', ''),
                             user_data=user_data,
                             calendar_url=calendar_url)
    except Exception:
        flash('Invalid booking ID.', 'error')
        return redirect(url_for('main.index'))
