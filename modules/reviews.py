from flask import Blueprint, request, jsonify, session
from bson import ObjectId
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__)


def init_reviews(mongo):
    reviews_bp.mongo = mongo
    return reviews_bp


@reviews_bp.route('/reviews/add', methods=['POST'])
def add_review():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    movie_id = data.get('movie_id')
    rating = data.get('rating')
    text = data.get('text', '')

    if not movie_id or rating is None:
        return jsonify({'success': False, 'error': 'movie_id and rating required'}), 400

    try:
        rating = int(rating)
    except Exception:
        return jsonify({'success': False, 'error': 'rating must be integer'}), 400

    if rating < 0 or rating > 10:
        return jsonify({'success': False, 'error': 'rating must be between 0 and 10'}), 400

    user_id = str(session['user_id'])
    user = reviews_bp.mongo.db.users.find_one({'_id': ObjectId(user_id)})
    username = user.get('username') if user else 'Anonymous'

    # Ensure one review per user per movie
    existing = reviews_bp.mongo.db.reviews.find_one({'movie_id': movie_id, 'user_id': user_id})
    if existing:
        return jsonify({'success': False, 'error': 'User has already reviewed this movie'}), 400

    review = {
        'movie_id': movie_id,
        'user_id': user_id,
        'username': username,
        'rating': rating,
        'text': text,
        'created_at': datetime.utcnow()
    }

    res = reviews_bp.mongo.db.reviews.insert_one(review)
    review['_id'] = str(res.inserted_id)
    review['created_at'] = review['created_at'].isoformat()

    return jsonify({'success': True, 'review': review}), 201


@reviews_bp.route('/reviews/<movie_id>')
def get_reviews(movie_id):
    # Pagination
    try:
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 3))
    except Exception:
        skip = 0
        limit = 3

    user_id = session.get('user_id')
    query = {'movie_id': movie_id}

    # Compute average rating and total count
    pipeline = [
        {'$match': {'movie_id': movie_id}},
        {'$group': {'_id': '$movie_id', 'avg': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
    ]
    agg = list(reviews_bp.mongo.db.reviews.aggregate(pipeline))
    avg = round(agg[0]['avg'], 1) if agg else None
    total = agg[0]['count'] if agg else 0

    reviews = []
    user_review = None
    if user_id:
        user_review = reviews_bp.mongo.db.reviews.find_one({'movie_id': movie_id, 'user_id': str(user_id)})
        if user_review:
            user_review['_id'] = str(user_review['_id'])
            user_review['created_at'] = user_review['created_at'].isoformat()

    # Fetch other reviews, excluding user's review if present
    fetch_query = {'movie_id': movie_id}
    if user_review:
        fetch_query['user_id'] = {'$ne': str(user_id)}

    cursor = reviews_bp.mongo.db.reviews.find(fetch_query).sort('created_at', -1).skip(skip).limit(limit)
    for r in cursor:
        r['_id'] = str(r['_id'])
        r['created_at'] = r['created_at'].isoformat()
        reviews.append(r)

    # If user review exists, put it on top
    if user_review:
        reviews = [user_review] + reviews

    return jsonify({'success': True, 'reviews': reviews, 'total': total, 'avg_rating': avg})


@reviews_bp.route('/reviews/delete/<review_id>', methods=['POST'])
def delete_review(review_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    user_id = str(session['user_id'])
    review = reviews_bp.mongo.db.reviews.find_one({'_id': ObjectId(review_id)})
    if not review:
        return jsonify({'success': False, 'error': 'Review not found'}), 404

    # Only author or admin can delete
    user = reviews_bp.mongo.db.users.find_one({'_id': ObjectId(user_id)})
    is_admin = user and user.get('role') == 'admin'
    if review.get('user_id') != user_id and not is_admin:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403

    reviews_bp.mongo.db.reviews.delete_one({'_id': ObjectId(review_id)})
    return jsonify({'success': True})
