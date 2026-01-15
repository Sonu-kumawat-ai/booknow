// Theatre Owner Registration page functionality

// Generate screen capacity inputs based on total screens
function generateScreenInputs() {
    const totalScreens = document.getElementById('total_screens').value;
    const container = document.getElementById('screensContainer');
    const inputsDiv = document.getElementById('screenInputs');
    
    if (totalScreens && container && inputsDiv) {
        container.style.display = 'block';
        inputsDiv.innerHTML = '';
        
        for (let i = 1; i <= parseInt(totalScreens); i++) {
            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'screen-input-wrapper';
            inputWrapper.innerHTML = `
                <label for="screen_${i}">Screen ${i} Capacity:</label>
                <input type="number" name="screen_capacity[]" class="screen-capacity-input" placeholder="e.g., 150" min="1" required>
            `;
            inputsDiv.appendChild(inputWrapper);
        }
    } else if (container && inputsDiv) {
        container.style.display = 'none';
        inputsDiv.innerHTML = '';
    }
}

// Setup event listeners on page load
window.addEventListener('DOMContentLoaded', function() {
    const totalScreensInput = document.getElementById('total_screens');
    if (totalScreensInput) {
        totalScreensInput.addEventListener('change', generateScreenInputs);
        totalScreensInput.addEventListener('input', generateScreenInputs);
    }
});

console.log('Theatre registration page loaded! 📝');
