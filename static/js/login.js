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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: password })
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.success) {
          window.location.href = data.target || '/data.html';
        } else {
          window.location.href = data.target || '/enter_data.html';
          
          // show inline error; still provide a link to enter_data.html
          //const msg = (data && data.message) ? data.message : 'Login failed';
         // errorDiv.textContent = msg;
          //errorDiv.style.display = 'block';
          // optionally show a link to enter_data page after a short delay
          //const link = document.createElement('a');
          //link.href = data && data.target ? data.target : '/enter_data.html';
          //link.textContent = ' Proceed to data entry';
          //link.style.marginLeft = '8px';
          //errorDiv.appendChild(link);
        }
      })
      .catch(err => {
        errorDiv.textContent = 'Network error';
        errorDiv.style.display = 'block';
      });
  });
});
