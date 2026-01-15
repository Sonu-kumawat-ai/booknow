"""
Database initialization and migration script
Sets up proper collections and indexes for the BookNow application
"""
from datetime import datetime
from bson import ObjectId

def initialize_database(mongo):
    """Initialize database collections and indexes"""
    db = mongo.db
    
    # Create indexes for better query performance
    
    # Users collection
    db.users.create_index('email', unique=True)
    db.users.create_index('username')
    db.users.create_index('role')
    
    # Theatres collection  
    db.theatres.create_index('owner_id')
    db.theatres.create_index([('city', 1), ('state', 1)])
    db.theatres.create_index('name')
    
    # Screens collection
    db.screens.create_index('theatre_id')
    db.screens.create_index([('theatre_id', 1), ('screen_number', 1)], unique=True)
    
    # Movies collection
    db.movies.create_index('title')
    db.movies.create_index('genre')
    db.movies.create_index('release_date')
    
    # Showtimes collection
    db.showtimes.create_index('movie_id')
    db.showtimes.create_index('screen_id')
    db.showtimes.create_index('theatre_id')
    db.showtimes.create_index([('screen_id', 1), ('show_date', 1), ('show_time', 1)])
    db.showtimes.create_index('show_date')
    
    # Bookings collection
    db.bookings.create_index('user_id')
    db.bookings.create_index('showtime_id')
    db.bookings.create_index('booking_date')
    db.bookings.create_index('status')
    
    # Booking seats collection
    db.booking_seats.create_index('booking_id')
    db.booking_seats.create_index('showtime_id')
    db.booking_seats.create_index([('showtime_id', 1), ('seat_number', 1)])
    
    # Payments collection
    db.payments.create_index('booking_id')
    db.payments.create_index('user_id')
    db.payments.create_index('razorpay_payment_id', unique=True, sparse=True)
    db.payments.create_index('payment_date')
    
    # Theatre owner applications collection
    db.theatre_owner_applications.create_index('user_id')
    db.theatre_owner_applications.create_index('status')
    db.theatre_owner_applications.create_index('applied_date')
    
    print("✅ Database collections and indexes created successfully!")


def migrate_existing_data(mongo):
    """Migrate data from old schema to new schema"""
    db = mongo.db
    
    print("Starting data migration...")
    
    # Migrate users - update role field
    users = db.users.find()
    for user in users:
        role = 'user'
        if user.get('email') == 'kumawatsonu086@gmail.com':
            role = 'admin'
        elif user.get('is_theatre_owner'):
            role = 'theatre_owner'
        
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'role': role}}
        )
    
    # Migrate theatre owner applications from users
    pending_users = db.users.find({'theatre_owner_status': 'pending'})
    for user in pending_users:
        theatre_info = user.get('theatre_info', {})
        if theatre_info:
            application = {
                'user_id': str(user['_id']),
                'username': user.get('username'),
                'email': user.get('email'),
                'theatre_name': theatre_info.get('theatre_name'),
                'theatre_address': theatre_info.get('theatre_address'),
                'city': theatre_info.get('city'),
                'state': theatre_info.get('state'),
                'pincode': theatre_info.get('pincode'),
                'phone': theatre_info.get('phone'),
                'theatre_type': theatre_info.get('theatre_type'),
                'total_screens': theatre_info.get('total_screens', 1),
                'seating_capacity': theatre_info.get('seating_capacity', 100),
                'parking_capacity': theatre_info.get('parking_capacity', 0),
                'amenities': theatre_info.get('amenities', []),
                'license_number': theatre_info.get('license_number'),
                'established_year': theatre_info.get('established_year'),
                'website': theatre_info.get('website'),
                'operating_hours': theatre_info.get('operating_hours'),
                'status': 'pending',
                'applied_date': user.get('request_date', datetime.utcnow()),
                'reviewed_by': None,
                'reviewed_date': None
            }
            db.theatre_owner_applications.insert_one(application)
    
    # Migrate approved theatre owners to theatres collection
    approved_owners = db.users.find({'is_theatre_owner': True})
    for user in approved_owners:
        theatre_info = user.get('theatre_info', {})
        if theatre_info and not db.theatres.find_one({'owner_id': str(user['_id'])}):
            theatre = {
                'owner_id': str(user['_id']),
                'name': theatre_info.get('theatre_name', 'Default Theatre'),
                'address': theatre_info.get('theatre_address', ''),
                'city': theatre_info.get('city', ''),
                'state': theatre_info.get('state', ''),
                'pincode': theatre_info.get('pincode', ''),
                'phone': theatre_info.get('phone', ''),
                'theatre_type': theatre_info.get('theatre_type', 'multiplex'),
                'parking_capacity': theatre_info.get('parking_capacity', 0),
                'amenities': theatre_info.get('amenities', []),
                'license_number': theatre_info.get('license_number', ''),
                'established_year': theatre_info.get('established_year'),
                'website': theatre_info.get('website', ''),
                'operating_hours': theatre_info.get('operating_hours', ''),
                'status': 'active',
                'created_date': datetime.utcnow()
            }
            theatre_id = db.theatres.insert_one(theatre).inserted_id
            
            # Create screens for this theatre with individual capacities
            total_screens = theatre_info.get('total_screens', 1)
            screen_capacities = theatre_info.get('screen_capacities', [])
            
            # If no individual capacities, use default seating capacity
            if not screen_capacities:
                default_capacity = theatre_info.get('seating_capacity', 100)
                screen_capacities = [default_capacity] * total_screens
            
            for screen_num in range(1, total_screens + 1):
                capacity = screen_capacities[screen_num - 1] if screen_num <= len(screen_capacities) else 100
                screen = {
                    'theatre_id': str(theatre_id),
                    'screen_number': screen_num,
                    'name': f'Screen {screen_num}',
                    'seating_capacity': capacity,
                    'screen_type': '2D',
                    'sound_system': 'Dolby Digital',
                    'features': ['Air Conditioned', 'Wheelchair Accessible'],
                    'status': 'active',
                    'created_date': datetime.utcnow()
                }
                db.screens.insert_one(screen)
    
    # Migrate movies to create showtimes
    movies = db.movies.find()
    for movie in movies:
        # Find the theatre for this movie owner
        theatre = db.theatres.find_one({'owner_id': movie.get('added_by')})
        if theatre:
            # Get first screen of this theatre
            screen = db.screens.find_one({'theatre_id': str(theatre['_id'])})
            if screen:
                # Create showtimes for this movie
                show_times = movie.get('show_times', ['09:00 AM', '12:30 PM', '03:45 PM', '06:30 PM', '09:15 PM'])
                for show_time in show_times:
                    showtime = {
                        'movie_id': str(movie['_id']),
                        'theatre_id': str(theatre['_id']),
                        'screen_id': str(screen['_id']),
                        'show_date': datetime.utcnow().date().isoformat(),
                        'show_time': show_time,
                        'ticket_price': movie.get('ticket_price', 200),
                        'vip_price': int(movie.get('ticket_price', 200) * 1.5),
                        'available_seats': screen.get('seating_capacity', 100),
                        'status': 'active',
                        'created_date': datetime.utcnow()
                    }
                    db.showtimes.insert_one(showtime)
    
    # Migrate bookings to use showtimes and separate booking_seats
    bookings = db.bookings.find()
    for booking in bookings:
        # Try to find matching showtime
        movie_id = booking.get('movie_id')
        show_time = booking.get('show_time')
        
        showtime = db.showtimes.find_one({
            'movie_id': movie_id,
            'show_time': show_time
        })
        
        if showtime:
            # Update booking with showtime_id
            db.bookings.update_one(
                {'_id': booking['_id']},
                {'$set': {'showtime_id': str(showtime['_id'])}}
            )
            
            # Create payment record
            if booking.get('razorpay_payment_id'):
                payment = {
                    'booking_id': str(booking['_id']),
                    'user_id': booking.get('user_id'),
                    'amount': booking.get('amount', 0),
                    'razorpay_order_id': booking.get('razorpay_order_id'),
                    'razorpay_payment_id': booking.get('razorpay_payment_id'),
                    'payment_method': 'razorpay',
                    'payment_status': booking.get('payment_status', 'completed'),
                    'payment_date': booking.get('booking_date', datetime.utcnow()),
                    'currency': 'INR'
                }
                db.payments.insert_one(payment)
            
            # Create booking_seats records
            seats = booking.get('seats', [])
            for seat_number in seats:
                booking_seat = {
                    'booking_id': str(booking['_id']),
                    'showtime_id': str(showtime['_id']),
                    'seat_number': seat_number,
                    'seat_type': 'vip' if int(''.join(filter(str.isdigit, str(seat_number)))) <= 20 else 'normal',
                    'price': showtime.get('vip_price') if int(''.join(filter(str.isdigit, str(seat_number)))) <= 20 else showtime.get('ticket_price'),
                    'status': 'booked',
                    'booked_date': booking.get('booking_date', datetime.utcnow())
                }
                db.booking_seats.insert_one(booking_seat)
    
    print("✅ Data migration completed successfully!")


if __name__ == '__main__':
    print("This script should be run from the main application")
    print("Import and call initialize_database(mongo) and migrate_existing_data(mongo)")
