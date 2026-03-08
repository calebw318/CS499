from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# Temporary storage for submitted data (until database is connected)
submitted_data = []


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


@app.route('/api/submit_data', methods=['POST'])
def submit_data():
	"""
	Endpoint to receive research data (heart rate, test score, timestamp).
	Expects JSON with: timestamp, heartRate, testScore
	"""
	try:
		if request.is_json:
			data = request.get_json()
		else:
			return jsonify({'success': False, 'message': 'Request must be JSON'})
		
		heartRate = data.get('heartRate')
		testScore = data.get('testScore')
		timestamp = data.get('timestamp')
		
		# Validate data
		if heartRate is None or testScore is None or not timestamp:
			return jsonify({'success': False, 'message': 'Missing required fields'})
		
		try:
			heartRate = float(heartRate)
			testScore = float(testScore)
		except (ValueError, TypeError):
			return jsonify({'success': False, 'message': 'Invalid data format'})
		
		# Store data in memory (replace with database call when ready)
		data_entry = {
			'timestamp': timestamp,
			'heartRate': heartRate,
			'testScore': testScore
		}
		submitted_data.append(data_entry)
		
		# TODO: Insert into database here
		# db.insert_data(data_entry)
		
		return jsonify({'success': True, 'message': 'Data submitted successfully'})
	
	except Exception as e:
		return jsonify({'success': False, 'message': str(e)})


@app.route('/api/get_data', methods=['GET'])
def get_data():
	"""
	Endpoint to retrieve all submitted research data.
	Returns JSON array of data entries.
	"""
	try:
		# For now, return data from memory
		# TODO: Replace with database query when ready
		# data = db.query_all_data()
		
		# Return submitted data in reverse order (newest first)
		return jsonify({'success': True, 'data': submitted_data[::-1]})
	
	except Exception as e:
		return jsonify({'success': False, 'message': str(e), 'data': []})


@app.route('/data.html')
def data_page():
	return render_template('data.html')


@app.route('/enter_data.html')
def enter_data_page():
	return render_template('enter_data.html')


if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='127.0.0.1', port=port, debug=True)
