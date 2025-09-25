"""
Flask application factory for M-Pesa STK Push application.
Creates and configures the Flask application with all components.
"""

from flask import Flask
from flask_cors import CORS

from .config.settings import ConfigManager
from .services.mpesa_service import MpesaService
from .api.routes import create_api_blueprint
from .utils.logging import app_logger


class ApplicationFactory:
    """Factory for creating Flask application instances."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize application factory.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_file)
        self.mpesa_service = None
        self.app = None
    
    def create_app(self) -> Flask:
        """
        Create and configure Flask application.
        
        Returns:
            Configured Flask application
        """
        # Validate configuration first
        self.config_manager.validate()
        
        # Create Flask app
        self.app = Flask(__name__)
        
        # Configure Flask
        self._configure_app()
        
        # Initialize services
        self._initialize_services()
        
        # Register blueprints
        self._register_blueprints()
        
        # Setup error handlers
        self._setup_error_handlers()
        
        app_logger.info("Flask application created and configured successfully")
        return self.app
    
    def _configure_app(self):
        """Configure Flask application settings."""
        flask_config = self.config_manager.flask
        
        self.app.config.update({
            'SECRET_KEY': flask_config.secret_key,
            'DEBUG': flask_config.debug,
            'JSON_SORT_KEYS': flask_config.json_sort_keys,
            'JSONIFY_PRETTYPRINT_REGULAR': flask_config.jsonify_prettyprint_regular,
            'TESTING': False,
        })
        
        # Enable CORS
        CORS(self.app)
        
        app_logger.info("Flask configuration applied")
    
    def _initialize_services(self):
        """Initialize application services."""
        mpesa_config = self.config_manager.mpesa
        self.mpesa_service = MpesaService(mpesa_config)
        
        app_logger.info("Application services initialized")
    
    def _register_blueprints(self):
        """Register Flask blueprints."""
        api_blueprint = create_api_blueprint(self.mpesa_service)
        self.app.register_blueprint(api_blueprint)
        
        app_logger.info("API blueprints registered")
    
    def _setup_error_handlers(self):
        """Setup global error handlers."""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return {
                'success': False, 
                'message': 'Endpoint not found'
            }, 404
        
        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return {
                'success': False, 
                'message': 'Method not allowed'
            }, 405
        
        @self.app.errorhandler(500)
        def internal_error(error):
            app_logger.error(f"Internal server error: {error}")
            return {
                'success': False, 
                'message': 'Internal server error'
            }, 500
        
        app_logger.info("Error handlers configured")
    
    def run(self):
        """Run the Flask application."""
        if not self.app:
            self.create_app()
        
        flask_config = self.config_manager.flask
        
        app_logger.info("Starting M-Pesa STK Push application...")
        app_logger.info("Features enabled:")
        app_logger.info("- Object-oriented architecture ✓")
        app_logger.info("- Modular design with separation of concerns ✓")
        app_logger.info("- Access token caching ✓")
        app_logger.info("- Comprehensive validation ✓")
        app_logger.info("- Structured logging ✓")
        app_logger.info("- Performance monitoring ✓")
        app_logger.info(f"- Running on {flask_config.host}:{flask_config.port}")
        
        if flask_config.debug:
            app_logger.warning("DEBUG mode is enabled - Disable in production!")
        
        self.app.run(
            host=flask_config.host,
            port=flask_config.port,
            debug=flask_config.debug,
            threaded=flask_config.threaded,
            use_reloader=flask_config.debug
        )


def create_app(config_file: str = None) -> Flask:
    """
    Create Flask application using the factory pattern.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configured Flask application
    """
    factory = ApplicationFactory(config_file)
    return factory.create_app()