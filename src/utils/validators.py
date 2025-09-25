"""
Validation utilities for M-Pesa STK Push application.
Provides input validation and sanitization functions.
"""

import re
from typing import Tuple, Optional


class ValidationError(Exception):
    """Custom validation error."""
    pass


class PhoneNumberValidator:
    """Phone number validation utility."""
    
    # Pre-compiled regex patterns for better performance
    KENYAN_PHONE_PATTERN = re.compile(r'^254[0-9]{9}$')
    LOCAL_PHONE_PATTERN = re.compile(r'^0[0-9]{9}$')
    SHORT_PHONE_PATTERN = re.compile(r'^[0-9]{9}$')
    
    @classmethod
    def validate(cls, phone_number: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate and format phone number.
        
        Returns:
            Tuple of (formatted_phone_number, error_message)
        """
        if not phone_number or not isinstance(phone_number, str):
            return None, "Phone number is required"
        
        # Clean the phone number
        phone_number = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
        
        # Remove any non-digit characters
        if not phone_number.isdigit():
            return None, "Phone number must contain only digits"
        
        # Validate and format based on pattern
        if cls.KENYAN_PHONE_PATTERN.match(phone_number):
            return phone_number, None
        elif cls.LOCAL_PHONE_PATTERN.match(phone_number):
            return '254' + phone_number[1:], None
        elif cls.SHORT_PHONE_PATTERN.match(phone_number) and phone_number.startswith(('7', '1')):
            return '254' + phone_number, None
        else:
            return None, "Invalid phone number format. Use 254XXXXXXXXX, 07XXXXXXXX, or 7XXXXXXXX"


class AmountValidator:
    """Amount validation utility."""
    
    MIN_AMOUNT = 1
    MAX_AMOUNT = 70000  # Sandbox limit
    
    @classmethod
    def validate(cls, amount) -> Tuple[Optional[float], Optional[str]]:
        """
        Validate amount.
        
        Returns:
            Tuple of (validated_amount, error_message)
        """
        if amount is None:
            return None, "Amount is required"
        
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            return None, "Amount must be a valid number"
        
        if amount_float <= 0:
            return None, f"Amount must be greater than {cls.MIN_AMOUNT}"
        
        if amount_float > cls.MAX_AMOUNT:
            return None, f"Amount cannot exceed {cls.MAX_AMOUNT} KES"
        
        return amount_float, None


class RequestValidator:
    """General request validation utility."""
    
    @staticmethod
    def validate_stk_push_request(data: dict) -> Tuple[Optional[dict], Optional[str]]:
        """
        Validate STK push request data.
        
        Returns:
            Tuple of (validated_data, error_message)
        """
        if not data:
            return None, "Request data is required"
        
        # Validate phone number
        phone_number, phone_error = PhoneNumberValidator.validate(data.get('phoneNumber'))
        if phone_error:
            return None, phone_error
        
        # Validate amount
        amount, amount_error = AmountValidator.validate(data.get('amount'))
        if amount_error:
            return None, amount_error
        
        # Return validated data
        return {
            'phone_number': phone_number,
            'amount': amount,
            'reference': data.get('reference'),
            'description': data.get('description')
        }, None