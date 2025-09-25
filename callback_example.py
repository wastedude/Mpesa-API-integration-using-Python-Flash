"""
M-Pesa STK Push Callback Handler Example
=====================================

This file shows how to implement a basic callback handler for M-Pesa STK Push.
Copy this code into your main app file or create a separate module.
Make sure to adapt the logic to fit your application's needs.
"""

from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mpesa_callbacks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Example Flask app setup (if using separately)
# app = Flask(__name__)

def parse_callback_metadata(items):
    """
    Parse M-Pesa callback metadata items into a dictionary.
    
    Args:
        items: List of callback metadata items from M-Pesa
        
    Returns:
        dict: Parsed transaction data
    """
    transaction_data = {}
    
    for item in items:
        name = item.get('Name', '')
        value = item.get('Value')
        
        if name == 'Amount':
            transaction_data['amount'] = float(value) if value else 0
        elif name == 'MpesaReceiptNumber':
            transaction_data['mpesa_receipt'] = str(value) if value else ''
        elif name == 'PhoneNumber':
            transaction_data['phone_number'] = str(value) if value else ''
        elif name == 'TransactionDate':
            transaction_data['transaction_date'] = str(value) if value else ''
        elif name == 'Balance':
            transaction_data['balance'] = float(value) if value else 0
    
    return transaction_data

def log_callback_data(callback_data, result_code, result_desc):
    """
    Log callback data for debugging and monitoring.
    
    Args:
        callback_data: Full callback data from M-Pesa
        result_code: Transaction result code
        result_desc: Transaction result description
    """
    logger.info(f"M-Pesa Callback Received:")
    logger.info(f"  Result Code: {result_code}")
    logger.info(f"  Result Description: {result_desc}")
    logger.info(f"  Full Data: {json.dumps(callback_data, indent=2)}")

def handle_successful_payment(transaction_data, checkout_request_id, merchant_request_id):
    """
    Handle successful payment processing.
    
    Args:
        transaction_data: Parsed transaction details
        checkout_request_id: M-Pesa checkout request ID
        merchant_request_id: M-Pesa merchant request ID
    """
    receipt = transaction_data.get('mpesa_receipt', 'N/A')
    amount = transaction_data.get('amount', 0)
    phone = transaction_data.get('phone_number', 'N/A')
    
    print(f"✅ PAYMENT SUCCESS!")
    print(f"   Receipt: {receipt}")
    print(f"   Amount: KES {amount}")
    print(f"   Phone: {phone}")
    print(f"   Checkout ID: {checkout_request_id}")
    
    # TODO: Implement your business logic here
    # Examples:
    # - Save transaction to database
    # - Update user account balance
    # - Send confirmation email/SMS
    # - Trigger fulfillment process
    # - Update order status
    
    # Example database save (pseudo-code):
    # db.transactions.insert({
    #     'checkout_request_id': checkout_request_id,
    #     'merchant_request_id': merchant_request_id,
    #     'mpesa_receipt': receipt,
    #     'amount': amount,
    #     'phone_number': phone,
    #     'status': 'completed',
    #     'created_at': datetime.now()
    # })
    
    # Example email notification (pseudo-code):
    # send_email(
    #     to=get_user_email_by_phone(phone),
    #     subject='Payment Confirmation',
    #     message=f'Your payment of KES {amount} was successful. Receipt: {receipt}'
    # )

def handle_failed_payment(result_desc, checkout_request_id, merchant_request_id):
    """
    Handle failed payment processing.
    
    Args:
        result_desc: Description of why payment failed
        checkout_request_id: M-Pesa checkout request ID
        merchant_request_id: M-Pesa merchant request ID
    """
    print(f"❌ PAYMENT FAILED!")
    print(f"   Reason: {result_desc}")
    print(f"   Checkout ID: {checkout_request_id}")
    
    # TODO: Implement your failure handling logic here
    # Examples:
    # - Update transaction status in database
    # - Notify user of failure
    # - Log for analysis
    # - Trigger retry mechanism (if applicable)
    
    # Example database update (pseudo-code):
    # db.transactions.update(
    #     {'checkout_request_id': checkout_request_id},
    #     {'status': 'failed', 'failure_reason': result_desc}
    # )
    
    # Example user notification (pseudo-code):
    # send_sms(
    #     phone=get_phone_by_checkout_id(checkout_request_id),
    #     message=f'Payment failed: {result_desc}. Please try again.'
    # )

# Route decorator - add this to your Flask app
# @app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    Main M-Pesa STK Push callback handler.
    
    This endpoint receives payment notifications from M-Pesa.
    Always return success (200) to prevent M-Pesa from retrying.
    """
    try:
        # Get the JSON data from M-Pesa
        callback_data = request.get_json()
        
        if not callback_data:
            logger.warning("Received empty callback data")
            return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
        
        # Extract the STK callback data
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        
        if not stk_callback:
            logger.warning("Missing stkCallback in request body")
            return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
        
        # Extract key information
        merchant_request_id = stk_callback.get('MerchantRequestID', '')
        checkout_request_id = stk_callback.get('CheckoutRequestID', '')
        result_code = stk_callback.get('ResultCode', -1)
        result_desc = stk_callback.get('ResultDesc', 'Unknown error')
        
        # Log the callback for debugging
        log_callback_data(callback_data, result_code, result_desc)
        
        # Check if payment was successful (ResultCode = 0 means success)
        if result_code == 0:
            # Payment successful - extract transaction details
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            # Parse the metadata
            transaction_data = parse_callback_metadata(items)
            
            # Handle successful payment
            handle_successful_payment(transaction_data, checkout_request_id, merchant_request_id)
            
        else:
            # Payment failed or was cancelled
            handle_failed_payment(result_desc, checkout_request_id, merchant_request_id)
        
        # Always return success to M-Pesa to prevent retries
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Success"
        }), 200
        
    except Exception as e:
        # Log the error but still return success to M-Pesa
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        logger.error(f"Request data: {request.get_data()}")
        
        # Don't return error status - M-Pesa will retry
        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Success"
        }), 200

# Health check endpoint for monitoring
# @app.route('/mpesa/callback/health', methods=['GET'])
def callback_health():
    """Health check for callback endpoint."""
    return jsonify({
        "status": "healthy",
        "endpoint": "/mpesa/callback",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }), 200

# Test endpoint to simulate M-Pesa callback (for development only)
# @app.route('/mpesa/callback/test', methods=['POST'])
def test_callback():
    """
    Test endpoint to simulate M-Pesa callback.
    Use this for testing your callback handler during development.
    
    Example usage:
    POST /mpesa/callback/test
    Content-Type: application/json
    
    {
        "success": true,
        "amount": 100,
        "phone": "254712345678",
        "receipt": "TEST123"
    }
    """
    test_data = request.get_json()
    
    if test_data.get('success', True):
        # Simulate successful callback
        mock_callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "test-merchant-123",
                    "CheckoutRequestID": "test-checkout-456",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": test_data.get('amount', 100)},
                            {"Name": "MpesaReceiptNumber", "Value": test_data.get('receipt', 'TEST123')},
                            {"Name": "PhoneNumber", "Value": test_data.get('phone', '254712345678')},
                            {"Name": "TransactionDate", "Value": int(datetime.now().strftime('%Y%m%d%H%M%S'))}
                        ]
                    }
                }
            }
        }
    else:
        # Simulate failed callback
        mock_callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "test-merchant-123",
                    "CheckoutRequestID": "test-checkout-456",
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user"
                }
            }
        }
    
    # Process the mock callback using our handler
    with app.test_request_context('/mpesa/callback', 
                                  method='POST', 
                                  json=mock_callback,
                                  headers={'Content-Type': 'application/json'}):
        response = mpesa_callback()
    
    return jsonify({
        "message": "Test callback processed",
        "mock_data": mock_callback,
        "handler_response": response.get_json()
    }), 200

if __name__ == "__main__":
    # Example of how to use this in a standalone script
    print("M-Pesa Callback Handler Example")
    print("================================")
    print("Copy the mpesa_callback() function to your Flask app")
    print("and add the @app.route decorator")
    print("Example:")
    print("  @app.route('/mpesa/callback', methods=['POST'])")
    print("  def mpesa_callback():")
    print("      # ... function code here ...")