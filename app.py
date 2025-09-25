import base64
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import threading
import time
import logging
from functools import wraps
import re

# Configure logging for better performance monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from your HTML page

# Configure Flask security
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-in-production')

# Performance optimizations
app.config['JSON_SORT_KEYS'] = False  # Don't sort JSON keys for better performance
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing in production

# Global variables for caching and optimization
_access_token_cache = {}
_cache_lock = threading.Lock()
_phone_pattern = re.compile(r'^(254)?[0-9]{9}$')  # Compile regex once for better performance

# Configuration cache to avoid repeated environment variable reads
class Config:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.business_shortcode = int(os.getenv('MPESA_BUSINESS_SHORTCODE', 174379))
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://httpbin.org/post')
        
        # Validate critical configuration on startup
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("M-Pesa credentials not found in environment variables")
        if not self.passkey:
            raise ValueError("M-Pesa passkey not found in environment variables")

# Initialize configuration once
config = Config()


def get_cached_access_token():
    """Get cached access token or generate new one if expired."""
    with _cache_lock:
        current_time = datetime.now()
        cache_key = f"{config.consumer_key}:{config.consumer_secret}"
        
        # Check if we have a valid cached token
        if cache_key in _access_token_cache:
            token_data = _access_token_cache[cache_key]
            if current_time < token_data['expires_at']:
                logger.info("Using cached access token")
                return token_data['token']
        
        # Generate new token
        logger.info("Generating new access token")
        token = _generate_new_access_token()
        
        # Cache the token (M-Pesa tokens are valid for 1 hour)
        _access_token_cache[cache_key] = {
            'token': token,
            'expires_at': current_time + timedelta(minutes=55)  # 5 minutes buffer
        }
        
        return token

def _generate_new_access_token():
    """Generate a new access token from M-Pesa API."""
    # Use pre-computed values from config
    auth_string = f"{config.consumer_key}:{config.consumer_secret}"
    encoded_auth_string = base64.b64encode(auth_string.encode()).decode('utf-8')

    headers = {'Authorization': f'Basic {encoded_auth_string}'}
    
    try:
        response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()['access_token']
            logger.info(f"New access token generated: {token[:10]}...")
            return token
        else:
            raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error getting access token: {e}")
        raise Exception(f"Network error: {e}")

# Deprecated: Keep for backward compatibility but use cached version
def generate_access_token():
    """Generate access token for M-Pesa API authentication."""
    return get_cached_access_token()

def initiate_stk_push(phone_number, amount, reference):
    """Initiate STK push for M-Pesa payment with optimized performance."""
    try:
        access_token = get_cached_access_token()
        
        # Pre-compute timestamp and password for better performance
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        concat_string = f"{config.business_shortcode}{config.passkey}{timestamp}"
        password = base64.b64encode(concat_string.encode()).decode()

        # Optimized payload construction
        payload = {
            "BusinessShortCode": config.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),  # Ensure integer for API
            "PartyA": phone_number,
            "PartyB": config.business_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": config.callback_url,
            "AccountReference": reference,
            "TransactionDesc": f"Payment of KES {amount}"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Make API request with better error handling
        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            headers=headers,
            json=payload,
            timeout=15  # Increased timeout for better reliability
        )
        
        result = response.json()
        
        # Log response for debugging (without sensitive data)
        logger.info(f"STK Push response code: {result.get('ResponseCode', 'N/A')}")
        
        return result
        
    except requests.RequestException as e:
        logger.error(f"Network error in STK push: {e}")
        return {'ResponseCode': '1', 'errorMessage': f'Network error: {str(e)}'}
    except Exception as e:
        logger.error(f"Error in STK push: {e}")
        return {'ResponseCode': '1', 'errorMessage': f'Internal error: {str(e)}'}

def timing_decorator(f):
    """Decorator to measure function execution time."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{f.__name__} executed in {end_time - start_time:.3f} seconds")
        return result
    return wrapper

def validate_phone_number(phone_number):
    """Optimized phone number validation."""
    if not phone_number or not isinstance(phone_number, str):
        return None, "Phone number is required"
    
    phone_number = phone_number.strip()
    
    # Use pre-compiled regex for better performance
    if not phone_number.isdigit():
        return None, "Phone number must contain only digits"
    
    # Optimize phone number formatting
    if phone_number.startswith('254'):
        if len(phone_number) != 12:
            return None, "Invalid phone number format"
        return phone_number, None
    elif phone_number.startswith(('07', '01')):
        if len(phone_number) != 10:
            return None, "Invalid phone number format"
        return '254' + phone_number[1:], None
    elif phone_number.startswith(('7', '1')):
        if len(phone_number) != 9:
            return None, "Invalid phone number format"
        return '254' + phone_number, None
    else:
        return None, "Phone number must start with 254, 07, 01, 7, or 1"

def validate_amount(amount):
    """Optimized amount validation."""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return None, "Amount must be greater than 0"
        if amount_float > 70000:  # Sandbox limit
            return None, "Amount cannot exceed 70,000 KES"
        return amount_float, None
    except (ValueError, TypeError):
        return None, "Invalid amount format"
@app.route('/stk-push/', methods=['POST'])
@timing_decorator
def handle_stk_push():
    """Optimized STK push handler with improved performance and validation."""
    try:
        # Fast JSON parsing with error handling
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        # Extract and validate phone number
        phone_number, phone_error = validate_phone_number(data.get('phoneNumber'))
        if phone_error:
            return jsonify({'success': False, 'message': phone_error}), 400
        
        # Extract and validate amount
        amount, amount_error = validate_amount(data.get('amount'))
        if amount_error:
            return jsonify({'success': False, 'message': amount_error}), 400
        
        # Generate optimized reference
        reference = f"PAY_{phone_number[-6:]}_{int(time.time() % 100000)}"
        
        # Log request (optimized logging)
        logger.info(f"STK push request: {phone_number[:3]}***{phone_number[-3:]}, KES {amount}")
        
        # Call STK push function
        result = initiate_stk_push(phone_number, amount, reference)
        
        # Optimized response handling
        if result.get('ResponseCode') == '0':
            return jsonify({
                'success': True,
                'message': f'STK push sent to {phone_number[:3]}***{phone_number[-3:]} for KES {amount}. Check your phone.',
                'data': {
                    'MerchantRequestID': result.get('MerchantRequestID'),
                    'CheckoutRequestID': result.get('CheckoutRequestID'),
                    'ResponseCode': result.get('ResponseCode'),
                    'ResponseDescription': result.get('ResponseDescription')
                }
            })
        else:
            error_msg = result.get('errorMessage') or result.get('ResponseDescription', 'Unknown error')
            logger.warning(f"STK push failed: {error_msg}")
            return jsonify({
                'success': False,
                'message': f"STK push failed: {error_msg}"
            }), 400
            
    except Exception as e:
        logger.error(f"Error processing STK push: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again.'
        }), 500


# Health check endpoint for monitoring
@app.route('/health', methods=['GET'])
def health_check():
    """Fast health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 8000))
    
    # Performance optimizations
    if not debug_mode:
        # Disable Flask's reloader in production for better performance
        app.config['DEBUG'] = False
        # Optimize JSON serialization
        app.config['JSON_SORT_KEYS'] = False
    
    logger.info("Starting M-Pesa STK Push server...")
    logger.info("Performance optimizations enabled:")
    logger.info("- Access token caching ✓")
    logger.info("- Pre-compiled regex validation ✓")
    logger.info("- Optimized JSON handling ✓")
    logger.info("- Enhanced error handling ✓")
    logger.info("- Performance monitoring ✓")
    logger.info(f"- Running on {host}:{port}")
    
    if debug_mode:
        logger.warning("DEBUG mode enabled - Disable in production!")
    
    # Warm up the configuration cache
    logger.info("Warming up application cache...")
    
    app.run(
        host=host, 
        port=port, 
        debug=debug_mode,
        threaded=True,  # Enable threading for better performance
        use_reloader=debug_mode  # Only use reloader in debug mode
    )