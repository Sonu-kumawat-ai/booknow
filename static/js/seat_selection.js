// Seat Selection page functionality

// Load data from JSON
const bookingDataElement = document.getElementById('booking-data');
if (!bookingDataElement) {
    console.error('Booking data not found!');
}

const bookingData = bookingDataElement ? JSON.parse(bookingDataElement.textContent) : {};
const totalSeats = bookingData.totalSeats || 60;
const normalTicketPrice = bookingData.normalTicketPrice || 200;
const vipTicketPrice = bookingData.vipTicketPrice || 300;
const movieId = bookingData.movieId || '';
const showtimeId = bookingData.showtimeId || '';
// Convert booked seats to numbers for consistent comparison
const bookedSeats = (bookingData.bookedSeats || []).map(seat => {
    // Handle both string and number formats
    if (typeof seat === 'string') {
        return parseInt(seat);
    }
    return seat;
});

console.log('Booked seats:', bookedSeats);

let selectedSeats = [];
let selectedShowTime = bookingData.showDate && bookingData.showTime ? `${bookingData.showDate} ${bookingData.showTime}` : 'Selected';
let maxTickets = 4;

// Setup event listeners when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Display the selected showtime
    const selectedTimeElement = document.getElementById('selectedTime');
    if (selectedTimeElement && selectedShowTime) {
        selectedTimeElement.textContent = selectedShowTime;
    }
    
    // Setup event listeners
    setupEventListeners();
    
    // Generate seats
    if (document.getElementById('vipSeatsContainer') && document.getElementById('normalSeatsContainer')) {
        generateSeats();
    }
});

function setupEventListeners() {
    // Ticket count buttons
    const decreaseBtn = document.querySelector('.ticket-decrease');
    const increaseBtn = document.querySelector('.ticket-increase');
    if (decreaseBtn) {
        decreaseBtn.addEventListener('click', () => changeTicketCount(-1));
    }
    if (increaseBtn) {
        increaseBtn.addEventListener('click', () => changeTicketCount(1));
    }
    
    // Proceed button
    const proceedBtn = document.getElementById('proceedBtn');
    if (proceedBtn) {
        proceedBtn.addEventListener('click', proceedToPayment);
    }
}

function changeTicketCount(delta) {
    maxTickets = Math.max(1, Math.min(10, maxTickets + delta));
    const maxTicketsElement = document.getElementById('maxTickets');
    if (maxTicketsElement) {
        maxTicketsElement.textContent = maxTickets;
    }
    
    // Deselect seats if over limit
    if (selectedSeats.length > maxTickets) {
        const seatsToRemove = selectedSeats.slice(maxTickets);
        seatsToRemove.forEach(seatData => {
            const seatEl = document.querySelector(`[data-seat="${seatData.number}"][data-class="${seatData.class}"]`);
            if (seatEl) {
                seatEl.classList.remove('selected');
                seatEl.classList.add('available');
            }
        });
        selectedSeats = selectedSeats.slice(0, maxTickets);
        updateSummary();
    }
}

// Generate seats dynamically
function generateSeats() {
    // Calculate Normal (80%) and VIP (20%) seats
    const normalSeats = Math.floor(totalSeats * 0.8);
    const vipSeats = totalSeats - normalSeats;
    
    // Normal seats near screen (start from 1)
    generateSeatSection('normalSeatsContainer', normalSeats, 1, 'normal', normalTicketPrice);
    // VIP seats far from screen (after normal seats)
    generateSeatSection('vipSeatsContainer', vipSeats, normalSeats + 1, 'vip', vipTicketPrice);
}

function generateSeatSection(containerId, totalSeats, startNumber, seatClass, price) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear existing seats
    container.innerHTML = '';
    
    const seatsPerRow = 10; // 10 seats per row: 2-6-2 layout with aisles
    const totalRows = Math.ceil(totalSeats / seatsPerRow);
    
    let seatNumber = startNumber;
    const rowLabels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    
    for (let row = 0; row < totalRows; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'seat-row';
        
        // Add row label
        const rowLabel = document.createElement('div');
        rowLabel.className = 'row-label';
        rowLabel.textContent = rowLabels[row] || row + 1;
        rowDiv.appendChild(rowLabel);
        
        const seatsInThisRow = Math.min(seatsPerRow, totalSeats - (row * seatsPerRow));
        
        for (let col = 0; col < seatsInThisRow; col++) {
            // Add aisle gap after 2 seats and after 8 seats (2-6-2 pattern)
            if (col === 2 || col === 8) {
                const aisle = document.createElement('div');
                aisle.className = 'aisle-gap';
                rowDiv.appendChild(aisle);
            }
            
            const seat = document.createElement('div');
            const currentSeatNumber = seatNumber;
            
            // Check if seat is already booked
            const isBooked = bookedSeats.includes(currentSeatNumber);
            seat.className = isBooked ? 'seat booked' : 'seat available';
            
            seat.dataset.seat = currentSeatNumber;
            seat.dataset.class = seatClass;
            seat.dataset.price = price;
            seat.textContent = currentSeatNumber; // Show continuous seat number
            
            if (!isBooked) {
                seat.onclick = () => toggleSeat(seat, currentSeatNumber, seatClass, price);
            }
            
            rowDiv.appendChild(seat);
            seatNumber++;
        }
        
        // Add row label on right side too
        const rowLabelRight = document.createElement('div');
        rowLabelRight.className = 'row-label';
        rowLabelRight.textContent = rowLabels[row] || row + 1;
        rowDiv.appendChild(rowLabelRight);
        
        container.appendChild(rowDiv);
    }
}

function toggleSeat(seatElement, seatNumber, seatClass, price) {
    if (seatElement.classList.contains('booked')) return;
    
    if (seatElement.classList.contains('selected')) {
        seatElement.classList.remove('selected');
        seatElement.classList.add('available');
        selectedSeats = selectedSeats.filter(s => s.number !== seatNumber);
    } else {
        if (selectedSeats.length >= maxTickets) {
            alert(`You can only select up to ${maxTickets} tickets. Change the ticket count to select more.`);
            return;
        }
        
        seatElement.classList.remove('available');
        seatElement.classList.add('selected');
        selectedSeats.push({number: seatNumber, class: seatClass, price: price});
    }
    
    updateSummary();
}

function updateSummary() {
    const count = selectedSeats.length;
    const total = selectedSeats.reduce((sum, seat) => sum + seat.price, 0);
    
    const seatNumbers = selectedSeats.map(s => s.number).sort((a, b) => a - b);
    
    const selectedSeatsDisplay = document.getElementById('selectedSeatsDisplay');
    if (selectedSeatsDisplay) {
        selectedSeatsDisplay.textContent = seatNumbers.length > 0 ? seatNumbers.join(', ') : 'None';
    }
    
    const ticketCount = document.getElementById('ticketCount');
    if (ticketCount) {
        ticketCount.textContent = count;
    }
    
    const proceedBtn = document.getElementById('proceedBtn');
    if (proceedBtn) {
        proceedBtn.disabled = count === 0;
    }
}

function proceedToPayment() {
    if (selectedSeats.length === 0) {
        alert('Please select at least one seat!');
        return;
    }
    
    // Get seat numbers
    const seatNumbers = selectedSeats.map(seat => seat.number);
    
    // Redirect to payment page
    const queryParams = new URLSearchParams({
        seats: seatNumbers.join(',')
    });
    
    window.location.href = `/payment/${showtimeId}?${queryParams.toString()}`;
}

// Initialize seats when page loads
if (document.getElementById('vipSeatsContainer') && document.getElementById('normalSeatsContainer')) {
    generateSeats();
}

console.log('Seat selection page loaded! 🎫');

