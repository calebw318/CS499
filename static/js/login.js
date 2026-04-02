document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('login');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorDiv = document.getElementById('login-error');
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';

    // POST credentials to server for validation
    fetch('/api/login', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: password })
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          window.location.href = data.target;
        } else {
          const message = data && data.message ? data.message : 'Login failed';
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
