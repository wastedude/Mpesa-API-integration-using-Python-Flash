"""
Data models for M-Pesa STK Push application.
Defines request and response structures.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class STKPushRequest:
    """STK Push request model."""
    phone_number: str
    amount: float
    reference: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate and format request data."""
        # Format phone number
        self.phone_number = self._format_phone_number(self.phone_number)
        
        # Set default reference if not provided
        if not self.reference:
            self.reference = f"PAY_{self.phone_number[-6:]}_{int(datetime.now().timestamp() % 100000)}"
        
        # Set default description if not provided
        if not self.description:
            self.description = f"Payment of KES {self.amount}"
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to 254XXXXXXXXX format."""
        phone = phone.strip()
        
        if phone.startswith('254'):
            return phone
        elif phone.startswith(('07', '01')):
            return '254' + phone[1:]
        elif phone.startswith(('7', '1')):
            return '254' + phone
        else:
            raise ValueError("Invalid phone number format")
    
    def to_mpesa_payload(self, business_shortcode: int, password: str, timestamp: str, callback_url: str) -> Dict[str, Any]:
        """Convert to M-Pesa API payload format."""
        return {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(self.amount),
            "PartyA": self.phone_number,
            "PartyB": business_shortcode,
            "PhoneNumber": self.phone_number,
            "CallBackURL": callback_url,
            "AccountReference": self.reference,
            "TransactionDesc": self.description
        }


@dataclass
class STKPushResponse:
    """STK Push response model."""
    success: bool
    message: str
    merchant_request_id: Optional[str] = None
    checkout_request_id: Optional[str] = None
    response_code: Optional[str] = None
    response_description: Optional[str] = None
    
    @classmethod
    def from_mpesa_response(cls, response_data: Dict[str, Any]) -> 'STKPushResponse':
        """Create response from M-Pesa API response."""
        response_code = response_data.get('ResponseCode')
        
        if response_code == '0':
            return cls(
                success=True,
                message="STK push sent successfully. Please check your phone.",
                merchant_request_id=response_data.get('MerchantRequestID'),
                checkout_request_id=response_data.get('CheckoutRequestID'),
                response_code=response_code,
                response_description=response_data.get('ResponseDescription')
            )
        else:
            error_message = response_data.get('errorMessage') or response_data.get('ResponseDescription', 'Unknown error')
            return cls(
                success=False,
                message=f"STK push failed: {error_message}",
                response_code=response_code,
                response_description=response_data.get('ResponseDescription')
            )
    
    @classmethod
    def error(cls, message: str) -> 'STKPushResponse':
        """Create error response."""
        return cls(success=False, message=message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'success': self.success,
            'message': self.message
        }
        
        if self.success:
            result['data'] = {
                'MerchantRequestID': self.merchant_request_id,
                'CheckoutRequestID': self.checkout_request_id,
                'ResponseCode': self.response_code,
                'ResponseDescription': self.response_description
            }
        
        return result


@dataclass
class AccessToken:
    """Access token model with expiration handling."""
    token: str
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() >= self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired)."""
        return not self.is_expired