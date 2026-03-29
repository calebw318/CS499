from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client
from types import SimpleNamespace
import os
from datetime import datetime

ADMIN_EMAIL = 'jenahinds@uky.edu'
load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SECRET_KEY")  # IMPORTANT: secret key

supabase: Client = create_client(url, key)


from types import SimpleNamespace

def get_authenticated_user(access_token):
    if not access_token:
        return None

    try:
        user_response = supabase.auth.get_user(access_token)
        return getattr(user_response, 'user', None)
    except Exception:
        return None


def get_current_user():
    email = session.get('user_email')
    if not email:
        return None
    return SimpleNamespace(email=email)


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('username')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'})

    try:
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })

        user = getattr(response, 'user', None)
        session_info = getattr(response, 'session', None)

        if not user or not session_info:
            return jsonify({'success': False, 'message': 'Login failed'})

        target = '/data.html' if user.email == ADMIN_EMAIL else '/enter_data.html'

        session.permanent = True
        session['user_email'] = user.email
        session['access_token'] = session_info.access_token
        session['is_admin'] = user.email == ADMIN_EMAIL

        return jsonify({
            'success': True,
            'user': {'email': user.email},
            'target': target
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')

    if not email or not password or not confirm_password:
        return jsonify({'success': False, 'message': 'Email, password, and confirm password are required'})
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})

    try:
        response = supabase.auth.sign_up({
            'email': email,
            'password': password
        })

        user = getattr(response, 'user', None)
        session_info = getattr(response, 'session', None)

        if not user:
            message = getattr(response, 'error', {}).get('message', 'Sign up failed') if hasattr(response, 'error') else 'Sign up failed'
            return jsonify({'success': False, 'message': message})

        if session_info and getattr(session_info, 'access_token', None):
            session.permanent = True
            session['user_email'] = user.email
            session['access_token'] = session_info.access_token
            session['is_admin'] = user.email == ADMIN_EMAIL
            target = '/data.html' if user.email == ADMIN_EMAIL else '/enter_data.html'
            return jsonify({'success': True, 'message': 'Sign up successful', 'target': target})

        return jsonify({'success': True, 'message': 'Sign up successful. Please check your email to confirm your account and then log in.', 'target': '/'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/logout')
def logout_page():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/current_user', methods=['GET'])
def current_user():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    return jsonify({'success': True, 'user': {'email': user.email, 'is_admin': user.email == ADMIN_EMAIL}})


@app.route('/api/submit_data', methods=['POST'])
def submit_data():
	if request.is_json:
		data = request.get_json()
	else:
		return jsonify({'success': False, 'message': 'Request must be JSON'})

	user = get_current_user()
	if not user:
		return jsonify({'success': False, 'message': 'Authentication required'}), 401

	baselineHeartRate = data.get('baselineHeartRate')
	newHeartRate = data.get('newHeartRate')
	testScore = data.get('testScore')
	timestamp = data.get('timestamp') or datetime.utcnow().isoformat()

	if baselineHeartRate is None and newHeartRate is None and testScore is None:
		return jsonify({'success': False, 'message': 'At least one numeric field is required'})

	payload = {
		'user_email': user.email,
		'timestamp': timestamp
	}

	try:
		if baselineHeartRate is not None:
			payload['baseline_heart_rate'] = float(baselineHeartRate)
		if newHeartRate is not None:
			payload['new_heart_rate'] = float(newHeartRate)
		if testScore is not None:
			payload['test_score'] = float(testScore)
	except (ValueError, TypeError):
		return jsonify({'success': False, 'message': 'Invalid numeric values'})

	# Use existing row for this user if it exists, otherwise insert new row.
	try:
		existing = supabase.table('research_data').select('*').eq('user_email', user.email).limit(1).execute()
		row = existing.data[0] if existing.data else None

		if row:
			supabase.table('research_data').update(payload).eq('id', row['id']).execute()
		else:
			supabase.table('research_data').insert(payload).execute()

		return jsonify({'success': True, 'message': 'Data submitted successfully'})
	except Exception as e:
		return jsonify({'success': False, 'message': str(e)})


@app.route('/api/get_data', methods=['GET'])
def get_data():
	user = get_current_user()

	if not user:
		return jsonify({'success': False, 'message': 'Authentication required', 'data': []}), 401

	try:
		if user.email == ADMIN_EMAIL:
			response = supabase.table('research_data').select('*').execute()
		else:
			response = supabase.table('research_data').select('*').eq('user_email', user.email).execute()

		return jsonify({'success': True, 'data': response.data or []})
	except Exception as e:
		return jsonify({'success': False, 'message': str(e), 'data': []})


@app.route('/data.html')
def data_page():
	if not get_current_user():
		return redirect(url_for('index'))
	return render_template('data.html')


@app.route('/enter_data.html')
def enter_data_page():
	if not get_current_user():
		return redirect(url_for('index'))
	return render_template('enter_data.html')


if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='127.0.0.1', port=port, debug=True)
