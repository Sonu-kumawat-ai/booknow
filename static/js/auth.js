// Authentication pages (login/register) functionality

// OTP Verification for Registration
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    const stepInput = document.getElementById('step');
    const registrationFields = document.getElementById('registrationFields');
    const otpSection = document.getElementById('otpSection');
    const submitBtn = document.getElementById('submitBtn');
    const formTitle = document.getElementById('formTitle');
    const formSubtitle = document.getElementById('formSubtitle');
    const otpInputs = document.querySelectorAll('.otp-digit');
    const otpHidden = document.getElementById('otpHidden');
    const resendBtn = document.getElementById('resendBtn');
    
    // Check if we should show OTP section (from server-side redirect)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('verify') === 'true') {
        // Restore form data from session storage
        const savedEmail = sessionStorage.getItem('reg_email');
        const savedUsername = sessionStorage.getItem('reg_username');
        
        if (savedEmail) {
            document.getElementById('email').value = savedEmail;
            document.getElementById('username').value = savedUsername || '';
            showOTPSection();
        }
    }
    
    function showOTPSection() {
        registrationFields.style.display = 'none';
        otpSection.style.display = 'block';
        stepInput.value = 'verify';
        submitBtn.textContent = 'Verify Email';
        formTitle.textContent = 'Verify Your Email';
        formSubtitle.textContent = 'Enter the code we sent to your email';
        
        // Disable registration fields and remove validation
        const usernameField = document.getElementById('username');
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirm_password');
        const termsField = document.getElementById('terms');
        
        usernameField.disabled = true;
        emailField.disabled = true;
        passwordField.disabled = true;
        confirmPasswordField.disabled = true;
        termsField.disabled = true;
        
        // Remove required attribute to prevent validation
        usernameField.removeAttribute('required');
        emailField.removeAttribute('required');
        passwordField.removeAttribute('required');
        confirmPasswordField.removeAttribute('required');
        termsField.removeAttribute('required');
        
        // Set email display
        document.getElementById('userEmail').textContent = emailField.value;
        
        // Focus first OTP input
        setTimeout(() => otpInputs[0].focus(), 100);
    }
    
    // OTP input handling
    if (otpInputs.length > 0) {
        otpInputs.forEach((input, index) => {
            input.addEventListener('input', function(e) {
                const value = e.target.value;
                
                if (!/^\d$/.test(value)) {
                    e.target.value = '';
                    return;
                }
                
                if (value && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
                
                updateOTPValue();
            });
            
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpInputs[index - 1].focus();
                }
            });
            
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const pastedData = e.clipboardData.getData('text').trim();
                
                if (/^\d{6}$/.test(pastedData)) {
                    pastedData.split('').forEach((digit, i) => {
                        if (otpInputs[i]) {
                            otpInputs[i].value = digit;
                        }
                    });
                    otpInputs[5].focus();
                    updateOTPValue();
                }
            });
        });
    }
    
    function updateOTPValue() {
        const otp = Array.from(otpInputs).map(input => input.value).join('');
        otpHidden.value = otp;
    }
    
    // Resend OTP
    if (resendBtn) {
        resendBtn.addEventListener('click', function() {
            resendBtn.disabled = true;
            resendBtn.textContent = 'Sending...';
            
            fetch('/resend-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('New OTP has been sent to your email');
                    otpInputs.forEach(input => input.value = '');
                    otpInputs[0].focus();
                } else {
                    alert(data.message || 'Failed to send OTP');
                }
            })
            .catch(error => {
                alert('Error sending OTP. Please try again.');
            })
            .finally(() => {
                resendBtn.disabled = false;
                resendBtn.textContent = 'Resend OTP';
            });
        });
    }
    
    // Form validation
    registerForm.addEventListener('submit', function(e) {
        if (stepInput && stepInput.value === 'register') {
            // Registration step validation
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');
            
            if (!password || !confirmPassword) return;
            
            if (password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
                return false;
            }
            
            if (password.value.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters long!');
                return false;
            }
            
            // Save form data before OTP is sent
            sessionStorage.setItem('reg_email', document.getElementById('email').value);
            sessionStorage.setItem('reg_username', document.getElementById('username').value);
        } else if (stepInput && stepInput.value === 'verify') {
            // OTP verification step
            updateOTPValue();
            if (otpHidden.value.length !== 6) {
                e.preventDefault();
                alert('Please enter all 6 digits of the OTP');
                return false;
            }
        }
    });
    
    // Clear session storage on successful login redirect
    if (window.location.pathname === '/login') {
        sessionStorage.removeItem('reg_email');
        sessionStorage.removeItem('reg_username');
    }
}

// Password visibility toggle
function addPasswordToggle() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.innerHTML = '👁️';
        toggleBtn.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2rem;
        `;
        
        toggleBtn.addEventListener('click', () => {
            if (input.type === 'password') {
                input.type = 'text';
                toggleBtn.innerHTML = '🙈';
            } else {
                input.type = 'password';
                toggleBtn.innerHTML = '👁️';
            }
        });
        
        wrapper.appendChild(toggleBtn);
    });
}

// Initialize password toggle on auth pages
if (document.querySelector('.auth-form')) {
    addPasswordToggle();
}

console.log('Auth page loaded! 🔐');
