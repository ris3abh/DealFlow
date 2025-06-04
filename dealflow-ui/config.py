# config.py
import os

# API Configuration
API_URL = os.environ.get('DEALFLOW_API_URL', 'http://localhost:8000')

# Flask Configuration
DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dealflow_development_key')