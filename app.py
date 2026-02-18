from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def login():
	if request.is_json:
		data = request.get_json()
	else:
		data = request.form.to_dict()
	username = (data.get('username') or '').strip()
	password = (data.get('password') or '').strip()

	# Simple server-side check: both username and password must be 'admin'
	if username == 'admin' and password == 'admin':
		return jsonify({'success': True, 'target': '/data.html', 'username': username})
	else:
		return jsonify({'success': False, 'target': '/enter_data.html', 'username': username})


@app.route('/data.html')
def data_page():
	return render_template('data.html')


@app.route('/enter_data.html')
def enter_data_page():
	return render_template('enter_data.html')


if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='127.0.0.1', port=port, debug=True)