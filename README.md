# M-Pesa STK Push Application

A secure Flask application for processing M-Pesa STK Push payments.

## Security Features

✅ **Environment Variables**: Sensitive credentials stored in `.env` file  
✅ **Input Validation**: Phone numbers and amounts are validated  
✅ **Data Masking**: Sensitive data is masked in logs  
✅ **Error Handling**: Proper error responses without exposing internals  
✅ **Git Protection**: `.gitignore` prevents credential commits  

## Setup Instructions

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install flask flask-cors requests python-dotenv cryptography
   ```

3. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your actual M-Pesa credentials
   - Generate a strong Flask secret key

4. **Run the application**:
   ```bash
   python app.py
   ```

## Security Best Practices

### For Development:
- Never commit `.env` files
- Use sandbox credentials only
- Enable debug mode only in development
- Use HTTPS in production

### For Production:
- Use production M-Pesa credentials
- Set `FLASK_DEBUG=False`
- Use a production WSGI server (not Flask's dev server)
- Implement rate limiting
- Use HTTPS/TLS encryption
- Set up proper logging and monitoring
- Implement API authentication/authorization

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MPESA_CONSUMER_KEY` | M-Pesa API consumer key | `ABC123...` |
| `MPESA_CONSUMER_SECRET` | M-Pesa API consumer secret | `XYZ789...` |
| `MPESA_BUSINESS_SHORTCODE` | Your business shortcode | `174379` |
| `MPESA_PASSKEY` | M-Pesa passkey | `bfb279f9aa...` |
| `MPESA_CALLBACK_URL` | Callback URL for responses | `https://yoursite.com/callback` |
| `FLASK_SECRET_KEY` | Flask session secret | Random string |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `FLASK_HOST` | Server host | `127.0.0.1` |
| `FLASK_PORT` | Server port | `8000` |

## Additional Security Recommendations

1. **Use HTTPS**: Always use HTTPS in production
2. **Rate Limiting**: Implement request rate limiting
3. **Authentication**: Add user authentication for API access
4. **Logging**: Implement proper logging (without sensitive data)
5. **Monitoring**: Set up monitoring and alerting
6. **Firewall**: Configure firewall rules
7. **Regular Updates**: Keep dependencies updated
8. **Backup**: Regular backup of configuration and data