# M-Pesa Callback Quick Reference

## 🚀 30-Second Setup

1. **Add callback route to your app:**
```python
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    callback_data = request.get_json()
    stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
    
    if stk_callback.get('ResultCode') == 0:
        # Payment success
        metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        for item in metadata:
            if item.get('Name') == 'MpesaReceiptNumber':
                print(f"✅ Payment success! Receipt: {item.get('Value')}")
                break
    else:
        print(f"❌ Payment failed: {stk_callback.get('ResultDesc')}")
    
    return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
```

2. **Update your STK Push request:**
```python
# Replace this line in your initiate_stk_push function:
"CallBackURL": "https://httpbin.org/post",  # ❌ Remove this

# With this:
"CallBackURL": f"{os.getenv('CALLBACK_BASE_URL', 'http://127.0.0.1:8000')}/mpesa/callback",
```

3. **Set environment variable:**
```env
CALLBACK_BASE_URL=https://yourdomain.com
```

## 📱 M-Pesa Result Codes

| Code | Meaning |
|------|---------|
| 0 | Success ✅ |
| 1 | Insufficient Funds |
| 1032 | User Cancelled |
| 1037 | Timeout (No PIN) |
| 1025 | Request Timeout |
| 1001 | Unable to Lock Subscriber |

## 🔧 Testing Commands

**Test callback locally with curl:**
```bash
curl -X POST http://127.0.0.1:8000/mpesa/callback \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "ResultCode": 0,
        "ResultDesc": "Success",
        "CallbackMetadata": {
          "Item": [
            {"Name": "MpesaReceiptNumber", "Value": "TEST123"}
          ]
        }
      }
    }
  }'
```

**Expose local server for testing:**
```bash
# Install ngrok
npm install -g ngrok

# Run your app
python app.py

# In another terminal
ngrok http 8000

# Use the ngrok URL in your .env
CALLBACK_BASE_URL=https://abc123.ngrok.io
```

## 📊 Sample Callback Data

**Successful Payment:**
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
          {"Name": "Amount", "Value": 100.00},
          {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
          {"Name": "PhoneNumber", "Value": 254712345678},
          {"Name": "TransactionDate", "Value": 20191219102115}
        ]
      }
    }
  }
}
```

**Failed Payment:**
```json
{
  "Body": {
    "stkCallback": {
      "MerchantRequestID": "29115-34620561-1",
      "CheckoutRequestID": "ws_CO_191220191020363925",
      "ResultCode": 1032,
      "ResultDesc": "Request cancelled by user"
    }
  }
}
```

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Callback not received | Use HTTPS URL, check firewall |
| Multiple callbacks | Implement idempotency check |
| JSON parsing error | Validate request.get_json() |
| Timeout errors | Always return 200 status |

## ✅ Production Checklist

- [ ] HTTPS callback URL
- [ ] Public domain (not localhost)
- [ ] SSL certificate valid
- [ ] Callback endpoint returns 200
- [ ] Error handling implemented  
- [ ] Logging enabled
- [ ] Database storage ready
- [ ] User notifications setup

---
📖 **Full Guide:** See `CALLBACK_SETUP_GUIDE.md` for detailed instructions