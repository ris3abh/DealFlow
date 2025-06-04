# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import requests
import os
import json
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dealflow_secret_key'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Import configuration
from config import API_URL

# Add template context processor to provide current date
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        try:
            # Extract form data
            form_data = {
                'salesperson_name': request.form['salesperson_name'],
                'salesperson_role': request.form['salesperson_role'],
                'company_name': request.form['company_name'],
                'company_business': request.form['company_business'],
                'company_values': request.form['company_values'],
                'conversation_purpose': request.form['conversation_purpose'],
                'conversation_type': request.form['conversation_type'],
                'model_type': request.form['model_type']
            }
            
            # Handle file upload
            files = {}
            if 'product_catalog' in request.files and request.files['product_catalog'].filename:
                product_catalog = request.files['product_catalog']
                filename = secure_filename(product_catalog.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                product_catalog.save(file_path)
                files = {'product_catalog': (filename, open(file_path, 'rb'))}
            
            # Make API request to create agent
            response = requests.post(
                f"{API_URL}/agents/create",
                data=form_data,
                files=files
            )
            
            # Close file if it was opened
            if files and 'product_catalog' in files:
                files['product_catalog'][1].close()
            
            if response.status_code != 200:
                flash(f"Error creating agent: {response.json().get('detail', 'Unknown error')}", 'error')
                return render_template('config.html', form_data=form_data)
            
            # Store agent information in session
            agent_data = response.json()
            session['agent_id'] = agent_data['agent_id']
            session['agent_details'] = {
                'salesperson_name': agent_data['salesperson_name'],
                **form_data
            }
            
            flash('Agent created successfully!', 'success')
            return redirect(url_for('chat'))
            
        except requests.RequestException as e:
            flash(f"Connection error: {str(e)}", 'error')
            return render_template('config.html', form_data=request.form)
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", 'error')
            return render_template('config.html', form_data=request.form)
    
    # GET request - show configuration form
    return render_template('config.html')

@app.route('/chat')
def chat():
    # Check if agent is configured
    if 'agent_id' not in session:
        flash('Please configure your agent first', 'warning')
        return redirect(url_for('config'))
    
    return render_template('chat.html', 
                          agent_id=session['agent_id'], 
                          agent_details=session['agent_details'])

@app.route('/api/messages', methods=['GET'])
def get_messages():
    agent_id = session.get('agent_id')
    if not agent_id:
        return jsonify({'error': 'No agent configured'}), 400
    
    try:
        response = requests.get(f"{API_URL}/agents/{agent_id}/conversation")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def send_message():
    agent_id = session.get('agent_id')
    if not agent_id:
        return jsonify({'error': 'No agent configured'}), 400
    
    data = request.json
    message = data.get('message', '')
    
    if not message.strip():
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        response = requests.post(
            f"{API_URL}/agents/{agent_id}/chat",
            json={
                'agent_id': agent_id,
                'message': message
            }
        )
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_agent():
    # Clear session data
    session.pop('agent_id', None)
    session.pop('agent_details', None)
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)