# Object-Oriented M-Pesa STK Push Application

## 🏗️ Architecture Overview

This application has been refactored into a modern, object-oriented structure with proper separation of concerns.

## 📁 Project Structure

```
Test/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── app_factory.py           # Flask application factory
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration classes
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   └── mpesa.py            # M-Pesa data models
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   └── mpesa_service.py    # M-Pesa service classes
│   ├── api/                    # API routes and controllers
│   │   ├── __init__.py
│   │   └── routes.py           # Flask route handlers
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── validators.py       # Input validation
│       └── logging.py          # Logging utilities
├── app_oop.py                  # Main application entry point
├── app.py                      # Original monolithic version
├── .env                        # Environment variables
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── mpesa_stk_push.html       # Frontend interface
└── README.md                 # Documentation
```

## 🔧 Key Components

### 1. **Configuration Management** (`src/config/settings.py`)
- **`MpesaConfig`**: M-Pesa API configuration with validation
- **`FlaskConfig`**: Flask application settings
- **`ConfigManager`**: Centralized configuration management

### 2. **Data Models** (`src/models/mpesa.py`)
- **`STKPushRequest`**: Request data model with validation
- **`STKPushResponse`**: Response data model
- **`AccessToken`**: Token management with expiration

### 3. **Services Layer** (`src/services/mpesa_service.py`)
- **`TokenManager`**: Access token caching and management
- **`STKPushService`**: STK push operations
- **`MpesaService`**: Main service orchestrator

### 4. **API Layer** (`src/api/routes.py`)
- **`STKPushAPI`**: REST API controller
- Clean separation of HTTP handling from business logic

### 5. **Utilities** (`src/utils/`)
- **`validators.py`**: Input validation classes
- **`logging.py`**: Structured logging and performance monitoring

## 🚀 How to Run

### Using the Object-Oriented Version:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app_oop.py
```

### Using the Original Version:
```bash
python app.py
```

## 🏆 Benefits of Object-Oriented Design

### 1. **Separation of Concerns**
- Configuration separate from business logic
- API routes separate from service logic
- Clear boundaries between components

### 2. **Maintainability**
- Easy to locate and modify specific functionality
- Changes in one module don't affect others
- Clear interfaces between components

### 3. **Testability**
- Each class can be unit tested independently
- Mock objects can be easily injected
- Clear test boundaries

### 4. **Scalability**
- Easy to add new features without modifying existing code
- New services can be added by implementing interfaces
- Configuration can be extended without code changes

### 5. **Reusability**
- Services can be reused across different endpoints
- Utilities can be shared across modules
- Models ensure consistent data structures

## 🔍 Design Patterns Used

### 1. **Factory Pattern**
- `ApplicationFactory` creates configured Flask instances
- Centralizes application setup and configuration

### 2. **Service Pattern**
- Business logic encapsulated in service classes
- Clear separation between API and business logic

### 3. **Repository Pattern**
- `TokenManager` abstracts token storage and retrieval
- Easy to switch between different caching mechanisms

### 4. **Dependency Injection**
- Services receive dependencies through constructors
- Easy to mock dependencies for testing

### 5. **Builder Pattern**
- `STKPushRequest` builds valid request objects
- Encapsulates validation and formatting logic

## 📊 Performance Comparison

| Feature | Original | Object-Oriented |
|---------|----------|-----------------|
| **Code Organization** | Single file | Multiple modules |
| **Testing** | Difficult | Easy to test |
| **Configuration** | Inline | Centralized |
| **Validation** | Ad-hoc | Systematic |
| **Error Handling** | Basic | Comprehensive |
| **Logging** | Print statements | Structured logging |
| **Caching** | Basic | Advanced with threading |
| **Maintainability** | Low | High |

## 🧪 Testing the Application

### Test the API endpoints:

```bash
# Health check
curl http://127.0.0.1:8000/health

# STK Push (replace with valid data)
curl -X POST http://127.0.0.1:8000/stk-push/ \
  -H "Content-Type: application/json" \
  -d '{"phoneNumber": "254712345678", "amount": 100}'
```

## 🔧 Configuration

The application uses the same `.env` file as before:

```env
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_BUSINESS_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=your_callback_url
FLASK_SECRET_KEY=your_secret_key
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=8000
```

## 📈 Future Enhancements

The object-oriented structure makes it easy to add:

1. **Database Integration**: Add repository classes for data persistence
2. **Authentication**: Add authentication services and middleware
3. **Rate Limiting**: Add rate limiting decorators
4. **Monitoring**: Add metrics collection services
5. **Testing**: Add comprehensive test suites
6. **API Documentation**: Add Swagger/OpenAPI documentation
7. **Background Jobs**: Add async task processing

## 🎯 Migration from Original Version

Both versions can run simultaneously:
- Original version: `python app.py`
- Object-oriented version: `python app_oop.py`

The object-oriented version provides the same functionality with better architecture, performance, and maintainability.