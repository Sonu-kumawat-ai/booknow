// Payment Page JavaScript

// Load payment data
const paymentDataElement = document.getElementById('payment-data');
const paymentData = paymentDataElement ? JSON.parse(paymentDataElement.textContent) : {};

// Offer management variables
let availableOffers = [];
let appliedOffer = null;
let discount = 0;
let originalAmount = paymentData.totalAmount;
let finalAmount = originalAmount;

// Setup event listeners
document.addEventListener('DOMContentLoaded', function() {
    const payButton = document.getElementById('payButton');
    if (payButton) {
        payButton.addEventListener('click', initiatePayment);
    }
    
    // Offer management listeners
    document.getElementById('viewOffersBtn').addEventListener('click', toggleOfferList);
    document.getElementById('applyOfferBtn').addEventListener('click', applyOfferCode);
    
    // Load available offers
    loadAvailableOffers();
});

function toggleOfferList() {
    const container = document.getElementById('offerListContainer');
    const btn = document.getElementById('viewOffersBtn');
    if (container.style.display === 'none') {
        container.style.display = 'block';
        btn.textContent = 'Hide Offers';
        if (availableOffers.length === 0) {
            loadAvailableOffers();
        }
    } else {
        container.style.display = 'none';
        btn.textContent = 'View All Offers';
    }
}

function loadAvailableOffers() {
    fetch('/get-applicable-offers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            showtime_id: paymentData.showtimeId,
            amount: originalAmount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            availableOffers = data.offers;
            displayOfferList();
        } else {
            document.getElementById('offerList').innerHTML = '<p style="text-align: center; color: #666;">No offers available</p>';
        }
    })
    .catch(error => {
        console.error('Error loading offers:', error);
        document.getElementById('offerList').innerHTML = '<p style="text-align: center; color: #dc3545;">Failed to load offers</p>';
    });
}

function displayOfferList() {
    const offerList = document.getElementById('offerList');
    if (availableOffers.length === 0) {
        offerList.innerHTML = '<p style="text-align: center; color: #666;">No offers available at this time</p>';
        return;
    }
    
    offerList.innerHTML = availableOffers.map(offer => `
        <div class="offer-item ${offer.is_eligible ? '' : 'ineligible'}" onclick="${offer.is_eligible ? `selectOffer('${offer.code}')` : 'return false;'}">
            <div class="offer-header-row">
                <div class="offer-code">${offer.code}</div>
                ${offer.is_eligible ? '<span class="eligible-badge">✓ Eligible</span>' : '<span class="ineligible-badge">Not Eligible</span>'}
            </div>
            <div class="offer-description">${offer.description}</div>
            <div class="offer-discount">
                ${offer.is_eligible ? 
                    `Save ₹${offer.calculated_discount} | ${offer.discount_type === 'percentage' ? offer.discount_value + '% OFF' : '₹' + offer.discount_value + ' OFF'}${offer.min_purchase > 0 ? ' (Min: ₹' + offer.min_purchase + ')' : ''}` 
                    : 
                    `<span class="ineligible-reason">${offer.ineligible_reason}</span>`
                }
            </div>
            ${!offer.is_eligible ? '<div class="offer-overlay"></div>' : ''}
        </div>
    `).join('');
}

function selectOffer(code) {
    // Find the offer to check eligibility
    const offer = availableOffers.find(o => o.code === code);
    if (offer && !offer.is_eligible) {
        showMessage(offer.ineligible_reason || 'This offer is not eligible for your booking', 'error');
        return;
    }
    
    document.getElementById('offerCodeInput').value = code;
    applyOfferCode();
}

function applyOfferCode() {
    const code = document.getElementById('offerCodeInput').value.trim();
    if (!code) {
        showMessage('Please enter an offer code', 'error');
        return;
    }
    
    fetch('/validate-offer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            code: code,
            showtime_id: paymentData.showtimeId,
            amount: originalAmount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            appliedOffer = data.offer;
            discount = data.discount;
            finalAmount = data.final_amount;
            updatePaymentSummary();
            showAppliedOffer();
            showMessage('Offer applied successfully!', 'success');
            // Hide offer list after applying
            document.getElementById('offerListContainer').style.display = 'none';
            document.getElementById('viewOffersBtn').textContent = 'View All Offers';
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error validating offer:', error);
        showMessage('Failed to apply offer. Please try again.', 'error');
    });
}

function removeOffer() {
    appliedOffer = null;
    discount = 0;
    finalAmount = originalAmount;
    updatePaymentSummary();
    document.getElementById('appliedOfferContainer').style.display = 'none';
    document.getElementById('offerCodeInput').value = '';
    showMessage('Offer removed', 'success');
}

function showAppliedOffer() {
    const container = document.getElementById('appliedOfferContainer');
    container.innerHTML = `
        <div class="applied-offer">
            <div class="applied-offer-header">
                <div>
                    <strong>${appliedOffer.code}</strong> applied!
                    <div style="font-size: 12px; color: #155724; margin-top: 3px;">
                        You saved ₹${discount}
                    </div>
                </div>
                <button class="remove-offer-btn" onclick="removeOffer()">Remove</button>
            </div>
        </div>
    `;
    container.style.display = 'block';
}

function updatePaymentSummary() {
    const discountRow = document.getElementById('discountRow');
    const discountAmount = document.getElementById('discountAmount');
    const finalAmountEl = document.getElementById('finalAmount');
    const payButtonAmount = document.getElementById('payButtonAmount');
    
    if (discount > 0) {
        discountRow.style.display = 'flex';
        discountAmount.textContent = `- ₹${discount}`;
    } else {
        discountRow.style.display = 'none';
    }
    
    finalAmountEl.textContent = `₹${finalAmount}`;
    payButtonAmount.textContent = `₹${finalAmount}`;
    
    // Update payment data
    paymentData.totalAmount = finalAmount;
    paymentData.discount = discount;
    paymentData.appliedOfferCode = appliedOffer ? appliedOffer.code : null;
    paymentData.appliedOfferId = appliedOffer ? appliedOffer._id : null;
}

function showMessage(message, type) {
    const messageDiv = document.getElementById('offerMessage');
    messageDiv.innerHTML = `<div class="offer-message ${type}">${message}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 5000);
}

function initiatePayment() {
    // Create order via API with discount info
    fetch('/create-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: paymentData.totalAmount,
            showtime_id: paymentData.showtimeId,
            seats: paymentData.seats,
            offer_code: paymentData.appliedOfferCode,
            discount: paymentData.discount,
            original_amount: originalAmount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error creating order: ' + data.error);
            return;
        }

        // Initialize Razorpay payment
        const options = {
            key: data.razorpay_key,
            amount: data.amount,
            currency: 'INR',
            name: 'BookNow',
            description: `Booking for ${paymentData.movieTitle}`,
            order_id: data.order_id,
            handler: function(response) {
                // Verify payment
                verifyPayment(response, data.booking_data);
            },
            prefill: {
                name: paymentData.username,
                email: paymentData.email
            },
            theme: {
                color: '#e91e63'
            }
        };

        const razorpay = new Razorpay(options);
        razorpay.open();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to initiate payment. Please try again.');
    });
}

function verifyPayment(response, bookingData) {
    fetch('/verify-payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            booking_data: bookingData
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Redirect to booking confirmation page
            window.location.href = data.redirect_url;
        } else {
            alert('Payment verification failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Payment verification failed. Please contact support.');
    });
}
