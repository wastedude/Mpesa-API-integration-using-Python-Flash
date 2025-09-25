# M-Pesa STK Push Callback Setup Guide

This guide explains how to properly configure and implement M-Pesa STK Push callbacks for your forked repository.

## 🔄 What is a Callback URL?

A callback URL is an endpoint that M-Pesa calls to notify your application about the payment status after a user completes (or cancels) an STK Push transaction.

### The Payment Flow:
```
1. Your App → M-Pesa API: "Charge user KES 100"
2. M-Pesa → User's Phone: "Enter PIN to pay"
3. User → M-Pesa: Enters PIN or cancels
4. M-Pesa → Your Callback URL: "Payment successful/failed"
5. Your App → Database/User: Update records, send notifications
```

## 🚀 Quick Start

### Step 1: Configure Your Environment

Create/update your `.env` file:
```env
# M-Pesa API Credentials
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_PASSKEY=your_passkey_here
MPESA_BUSINESS_SHORTCODE=174379

# Your Domain (change this!)
CALLBACK_BASE_URL=https://yourdomain.com
# For local testing: CALLBACK_BASE_URL=http://127.0.0.1:8000
```

### Step 2: Update Callback URL in Code

**For app.py (monolithic version):**
```python
# Find this line in the initiate_stk_push function:
callback_url = "https://httpbin.org/post"  # ❌ Remove this

# Replace with:
callback_url = f"{os.getenv('CALLBACK_BASE_URL', 'http://127.0.0.1:8000')}/mpesa/callback"
```

**For app_oop.py (object-oriented version):**
```python
# In src/services/mpesa_service.py, find:
callback_url = "https://httpbin.org/post"  # ❌ Remove this

# Replace with:
callback_url = f"{os.getenv('CALLBACK_BASE_URL', 'http://127.0.0.1:8000')}/mpesa/callback"
```

## 📡 Callback Implementation

### Option A: Basic Callback Handler

Add this to your main app file:

```python
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa STK Push callback."""
    try:
        callback_data = request.get_json()
        
        # Extract callback information
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        if result_code == 0:
            # Payment successful
            metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            
            # Extract transaction details
            transaction = {}
            for item in metadata:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'Amount':
                    transaction['amount'] = value
                elif name == 'MpesaReceiptNumber':
                    transaction['receipt'] = value
                elif name == 'PhoneNumber':
                    transaction['phone'] = value
                elif name == 'TransactionDate':
                    transaction['date'] = value
            
            print(f"✅ Payment Success: {transaction}")
            # TODO: Save to database, send notifications
            
        else:
            print(f"❌ Payment Failed: {result_desc}")
            # TODO: Update transaction status, notify user
        
        # Always respond with success
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
        
    except Exception as e:
        print(f"Callback error: {e}")
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
```

### Option B: Advanced Callback Handler with Database

```python
import sqlite3
from datetime import datetime

# Database setup (run once)
def init_database():
    conn = sqlite3.connect('transactions.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            checkout_request_id TEXT UNIQUE,
            merchant_request_id TEXT,
            phone_number TEXT,
            amount REAL,
            mpesa_receipt TEXT,
            transaction_date TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Advanced callback handler with database storage."""
    try:
        callback_data = request.get_json()
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        conn = sqlite3.connect('transactions.db')
        
        if result_code == 0:
            # Payment successful - extract details
            metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            transaction_data = {'status': 'success'}
            
            for item in metadata:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'Amount':
                    transaction_data['amount'] = value
                elif name == 'MpesaReceiptNumber':
                    transaction_data['mpesa_receipt'] = value
                elif name == 'PhoneNumber':
                    transaction_data['phone_number'] = value
                elif name == 'TransactionDate':
                    transaction_data['transaction_date'] = str(value)
            
            # Save to database
            conn.execute('''
                INSERT OR REPLACE INTO transactions 
                (checkout_request_id, merchant_request_id, phone_number, amount, 
                 mpesa_receipt, transaction_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (checkout_request_id, merchant_request_id, 
                  transaction_data.get('phone_number'),
                  transaction_data.get('amount'),
                  transaction_data.get('mpesa_receipt'),
                  transaction_data.get('transaction_date'),
                  'completed'))
            
            print(f"✅ Payment completed: Receipt {transaction_data.get('mpesa_receipt')}")
            
            # TODO: Send success email/SMS
            # send_payment_confirmation(transaction_data)
            
        else:
            # Payment failed
            conn.execute('''
                INSERT OR REPLACE INTO transactions 
                (checkout_request_id, merchant_request_id, status)
                VALUES (?, ?, ?)
            ''', (checkout_request_id, merchant_request_id, 'failed'))
            
            print(f"❌ Payment failed: {result_desc}")
            
            # TODO: Send failure notification
            # send_payment_failure_notification(checkout_request_id)
        
        conn.commit()
        conn.close()
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
        
    except Exception as e:
        print(f"Callback processing error: {e}")
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200

# Initialize database on app start
init_database()
```

## 🌐 Production Deployment

### 1. Domain Requirements

M-Pesa requires a **publicly accessible HTTPS URL**. You cannot use:
- ❌ `http://localhost:8000/callback`
- ❌ `http://127.0.0.1:8000/callback`
- ❌ HTTP (must be HTTPS)

You need:
- ✅ `https://yourdomain.com/mpesa/callback`
- ✅ Valid SSL certificate
- ✅ Publicly accessible server

### 2. Deployment Options

#### Option A: Cloud Platforms
```bash
# Heroku
git push heroku main
# Set environment variables in Heroku dashboard

# DigitalOcean App Platform
# Deploy via GitHub integration

# Railway
railway deploy

# Render
# Connect GitHub repository
```

#### Option B: VPS with Nginx
```nginx
# /etc/nginx/sites-available/mpesa-app
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Option C: Ngrok (Testing Only)
```bash
# Install ngrok
npm install -g ngrok

# Run your app
python app.py

# In another terminal, expose it
ngrok http 8000

# Use the ngrok URL as your callback
# Example: https://abc123.ngrok.io/mpesa/callback
```

### 3. Environment Configuration

**Production .env:**
```env
MPESA_CONSUMER_KEY=your_production_consumer_key
MPESA_CONSUMER_SECRET=your_production_consumer_secret
MPESA_PASSKEY=your_production_passkey
MPESA_BUSINESS_SHORTCODE=your_production_shortcode
CALLBACK_BASE_URL=https://yourdomain.com
FLASK_ENV=production
```

**Development .env:**
```env
MPESA_CONSUMER_KEY=your_sandbox_consumer_key
MPESA_CONSUMER_SECRET=your_sandbox_consumer_secret
MPESA_PASSKEY=your_sandbox_passkey
MPESA_BUSINESS_SHORTCODE=174379
CALLBACK_BASE_URL=http://127.0.0.1:8000
FLASK_ENV=development
```

## 🔧 Testing Your Callback

### 1. Local Testing with Ngrok

```bash
# Terminal 1: Run your app
python app.py

# Terminal 2: Expose with ngrok
ngrok http 8000

# Update your .env with ngrok URL
CALLBACK_BASE_URL=https://abc123.ngrok.io
```

### 2. Callback Response Format

M-Pesa sends this JSON to your callback URL:

```json
{
  "Body": {
    "stkCallback": {
      "MerchantRequestID": "29115-34620561-1",
      "CheckoutRequestID": "ws_CO_191220191020363925",
      "ResultCode": 0,
      "ResultDesc": "The service request is processed successfully.",
      "CallbackMetadata": {
        "Item": [
          {
            "Name": "Amount",
            "Value": 100.00
          },
          {
            "Name": "MpesaReceiptNumber", 
            "Value": "NLJ7RT61SV"
          },
          {
            "Name": "PhoneNumber",
            "Value": 254712345678
          },
          {
            "Name": "TransactionDate",
            "Value": 20191219102115
          }
        ]
      }
    }
  }
}
```

### 3. Result Codes

- **0**: Success
- **1**: Insufficient Funds
- **1032**: Request cancelled by user
- **1037**: Timeout. No MPin entered
- **1025**: Request timeout
- **1001**: Unable to lock subscriber
- **2001**: Wrong PIN entered

### 4. Test Callback Manually

```bash
# Test your callback endpoint
curl -X POST https://yourdomain.com/mpesa/callback \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "test-123",
        "CheckoutRequestID": "test-456", 
        "ResultCode": 0,
        "ResultDesc": "Success",
        "CallbackMetadata": {
          "Item": [
            {"Name": "Amount", "Value": 100},
            {"Name": "MpesaReceiptNumber", "Value": "TEST123"},
            {"Name": "PhoneNumber", "Value": 254712345678}
          ]
        }
      }
    }
  }'
```

## 🔒 Security Best Practices

### 1. Validate Callbacks
```python
def is_valid_mpesa_callback(request):
    """Validate that callback is from M-Pesa."""
    # Check IP whitelist (M-Pesa IPs)
    allowed_ips = ['196.201.214.200', '196.201.214.206']  # M-Pesa IPs
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    
    if client_ip not in allowed_ips:
        return False
    
    # Validate required fields
    data = request.get_json()
    if not data or 'Body' not in data:
        return False
        
    return True
```

### 2. Idempotency
```python
# Prevent duplicate processing
processed_callbacks = set()

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    callback_data = request.get_json()
    stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    
    # Check if already processed
    if checkout_request_id in processed_callbacks:
        return jsonify({"ResultCode": 0, "ResultDesc": "Already processed"}), 200
    
    # Process callback...
    
    # Mark as processed
    processed_callbacks.add(checkout_request_id)
```

### 3. Error Handling
```python
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    try:
        # Process callback
        pass
    except Exception as e:
        # Log error but still return success to M-Pesa
        logger.error(f"Callback processing failed: {e}")
        # Don't return error - M-Pesa will retry
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
```

## 📊 Monitoring and Logging

### 1. Structured Logging
```python
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mpesa_callbacks.log'),
        logging.StreamHandler()
    ]
)

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    callback_data = request.get_json()
    
    # Log every callback
    logging.info(f"Callback received: {json.dumps(callback_data, indent=2)}")
    
    # Process...
```

### 2. Health Check for Callbacks
```python
@app.route('/mpesa/callback/health', methods=['GET'])
def callback_health():
    """Health check for callback endpoint."""
    return jsonify({
        "status": "healthy",
        "endpoint": "/mpesa/callback",
        "timestamp": datetime.now().isoformat()
    })
```

## 🚨 Troubleshooting

### Common Issues:

1. **Callback not received**
   - ❌ URL not publicly accessible
   - ❌ No SSL certificate
   - ❌ Firewall blocking requests
   - ❌ Wrong callback URL in STK push

2. **Callback received but processing fails**
   - ❌ JSON parsing error
   - ❌ Missing required fields
   - ❌ Database connection issues

3. **Multiple callbacks for same transaction**
   - ✅ Implement idempotency checks
   - ✅ Use checkout_request_id as unique key

### Debug Steps:

```python
# Add debug logging
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    # Log raw request
    print("Raw callback data:", request.get_data())
    print("Headers:", dict(request.headers))
    print("JSON:", request.get_json())
    
    # Your processing code...
```

## 📝 Summary Checklist

- [ ] Update callback URL in code
- [ ] Set CALLBACK_BASE_URL in .env
- [ ] Implement callback handler
- [ ] Add database storage (optional)
- [ ] Deploy to public HTTPS domain
- [ ] Test callback with ngrok
- [ ] Add proper error handling
- [ ] Implement security validations
- [ ] Set up monitoring/logging
- [ ] Test with real M-Pesa transactions

## 🎯 Next Steps

After setting up callbacks, consider:

1. **Database Integration**: Store transactions permanently
2. **User Notifications**: Email/SMS confirmations
3. **Admin Dashboard**: View transaction history
4. **Webhook Management**: Handle other M-Pesa webhooks
5. **Analytics**: Track payment success rates

---

**Need help?** Check the main README.md or open an issue in the repository.