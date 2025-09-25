"""
M-Pesa service classes for handling API interactions.
Provides high-level interfaces for M-Pesa operations.
"""

import base64
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading

from ..config.settings import MpesaConfig
from ..models.mpesa import STKPushRequest, STKPushResponse, AccessToken
from ..utils.logging import app_logger, security_logger, timing_decorator


class TokenManager:
    """Manages M-Pesa access tokens with caching."""
    
    def __init__(self, config: MpesaConfig):
        self.config = config
        self._token_cache: Dict[str, AccessToken] = {}
        self._cache_lock = threading.Lock()
    
    def get_access_token(self) -> str:
        """Get valid access token (from cache or generate new)."""
        cache_key = f"{self.config.consumer_key}:{self.config.consumer_secret}"
        
        with self._cache_lock:
            # Check cache first
            if cache_key in self._token_cache:
                cached_token = self._token_cache[cache_key]
                if cached_token.is_valid:
                    security_logger.log_token_generation(from_cache=True)
                    return cached_token.token
            
            # Generate new token
            token = self._generate_new_token()
            
            # Cache the token (valid for 55 minutes with 5-minute buffer)
            expires_at = datetime.now() + timedelta(minutes=55)
            self._token_cache[cache_key] = AccessToken(token=token, expires_at=expires_at)
            
            security_logger.log_token_generation(from_cache=False)
            return token
    
    @timing_decorator(app_logger)
    def _generate_new_token(self) -> str:
        """Generate new access token from M-Pesa API."""
        auth_string = f"{self.config.consumer_key}:{self.config.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode('utf-8')
        
        headers = {'Authorization': f'Basic {encoded_auth}'}
        
        try:
            response = requests.get(
                self.config.oauth_url,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                token = response.json()['access_token']
                app_logger.info(f"New access token generated: {token[:10]}...")
                return token
            else:
                raise Exception(f"Token generation failed: {response.status_code} - {response.text}")
        
        except requests.RequestException as e:
            app_logger.error(f"Network error generating token: {e}")
            raise Exception(f"Network error: {e}")


class STKPushService:
    """Service for handling STK Push operations."""
    
    def __init__(self, config: MpesaConfig, token_manager: TokenManager):
        self.config = config
        self.token_manager = token_manager
    
    @timing_decorator(app_logger)
    def initiate_stk_push(self, request: STKPushRequest) -> STKPushResponse:
        """
        Initiate STK push transaction.
        
        Args:
            request: STK push request object
            
        Returns:
            STK push response object
        """
        try:
            # Log request (with phone number masking)
            security_logger.log_request(request.phone_number, request.amount)
            
            # Get access token
            access_token = self.token_manager.get_access_token()
            
            # Prepare request data
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self._generate_password(timestamp)
            
            # Create payload
            payload = request.to_mpesa_payload(
                business_shortcode=self.config.business_shortcode,
                password=password,
                timestamp=timestamp,
                callback_url=self.config.callback_url
            )
            
            # Make API request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.post(
                self.config.stk_push_url,
                headers=headers,
                json=payload,
                timeout=20
            )
            
            # Parse response
            result = response.json()
            stk_response = STKPushResponse.from_mpesa_response(result)
            
            # Log response
            security_logger.log_response(
                success=stk_response.success,
                response_code=stk_response.response_code,
                error_message=stk_response.message if not stk_response.success else None
            )
            
            return stk_response
        
        except requests.RequestException as e:
            error_msg = f"Network error during STK push: {e}"
            app_logger.error(error_msg)
            return STKPushResponse.error(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during STK push: {e}"
            app_logger.error(error_msg)
            return STKPushResponse.error(error_msg)
    
    def _generate_password(self, timestamp: str) -> str:
        """Generate password for STK push request."""
        concat_string = f"{self.config.business_shortcode}{self.config.passkey}{timestamp}"
        return base64.b64encode(concat_string.encode()).decode()


class MpesaService:
    """Main M-Pesa service class that combines all operations."""
    
    def __init__(self, config: MpesaConfig):
        self.config = config
        self.token_manager = TokenManager(config)
        self.stk_push_service = STKPushService(config, self.token_manager)
    
    def process_stk_push(self, phone_number: str, amount: float, 
                        reference: Optional[str] = None, 
                        description: Optional[str] = None) -> STKPushResponse:
        """
        Process STK push request with validation and error handling.
        
        Args:
            phone_number: Customer phone number
            amount: Transaction amount
            reference: Optional transaction reference
            description: Optional transaction description
            
        Returns:
            STK push response
        """
        try:
            # Create request object (validates and formats data)
            request = STKPushRequest(
                phone_number=phone_number,
                amount=amount,
                reference=reference,
                description=description
            )
            
            # Process the request
            return self.stk_push_service.initiate_stk_push(request)
        
        except ValueError as e:
            # Validation error
            return STKPushResponse.error(str(e))
        except Exception as e:
            # Unexpected error
            error_msg = f"Failed to process STK push: {e}"
            app_logger.error(error_msg)
            return STKPushResponse.error(error_msg)