document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('signup');
  const errorDiv = document.getElementById('signup-error');
  const successDiv = document.getElementById('signup-success');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';
    successDiv.style.display = 'none';
    successDiv.textContent = '';

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const confirmPassword = document.getElementById('confirmPassword').value.trim();

    fetch('/api/signup', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, confirmPassword })
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          if (data.target && data.target !== '/') {
            window.location.href = data.target;
          } else {
            successDiv.textContent = data.message || 'Account created. Please verify your email and log in.';
            successDiv.style.display = 'block';
          }
        } else {
          const message = data && data.message ? data.message : 'Sign up failed';
          errorDiv.textContent = message;
          errorDiv.style.display = 'block';
        }
      })
      .catch(err => {
        errorDiv.textContent = 'Network error';
        errorDiv.style.display = 'block';
      });
  });
});
