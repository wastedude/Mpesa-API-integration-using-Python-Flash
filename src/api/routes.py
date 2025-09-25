"""
Flask API routes for M-Pesa STK Push application.
Defines REST API endpoints and request handling.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any

from ..services.mpesa_service import MpesaService
from ..utils.validators import RequestValidator
from ..utils.logging import app_logger, timing_decorator


class STKPushAPI:
    """STK Push API controller."""
    
    def __init__(self, mpesa_service: MpesaService):
        self.mpesa_service = mpesa_service
        self.blueprint = Blueprint('stk_push', __name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes."""
        self.blueprint.add_url_rule(
            '/stk-push/', 
            'stk_push', 
            self.handle_stk_push, 
            methods=['POST']
        )
        
        self.blueprint.add_url_rule(
            '/health', 
            'health_check', 
            self.health_check, 
            methods=['GET']
        )
    
    @timing_decorator(app_logger)
    def handle_stk_push(self) -> tuple[Dict[str, Any], int]:
        """
        Handle STK push requests.
        
        Returns:
            Tuple of (response_data, http_status_code)
        """
        try:
            # Parse and validate request data
            data = request.get_json()
            validated_data, error = RequestValidator.validate_stk_push_request(data)
            
            if error:
                app_logger.warning(f"Invalid STK push request: {error}")
                return {'success': False, 'message': error}, 400
            
            # Process STK push
            response = self.mpesa_service.process_stk_push(
                phone_number=validated_data['phone_number'],
                amount=validated_data['amount'],
                reference=validated_data.get('reference'),
                description=validated_data.get('description')
            )
            
            # Return response
            status_code = 200 if response.success else 400
            return response.to_dict(), status_code
        
        except Exception as e:
            app_logger.error(f"Unexpected error in STK push handler: {e}")
            return {
                'success': False, 
                'message': 'Internal server error occurred. Please try again.'
            }, 500
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Health status information
        """
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'service': 'mpesa-stk-push'
        }


def create_api_blueprint(mpesa_service: MpesaService) -> Blueprint:
    """
    Create and configure API blueprint.
    
    Args:
        mpesa_service: M-Pesa service instance
        
    Returns:
        Configured Flask blueprint
    """
    stk_api = STKPushAPI(mpesa_service)
    return stk_api.blueprint