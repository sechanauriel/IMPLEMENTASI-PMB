"""Validation utilities"""

import re
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_indonesia(phone: str) -> bool:
    """
    Validate Indonesian phone number format
    
    Valid formats:
    - +62812345678 (with +62)
    - 08123456789 (with 0)
    - Length: 10-15 digits
    """
    pattern = r'^(\+62|0)[0-9]{9,12}$'
    return bool(re.match(pattern, phone))


def validate_date_of_birth(dob: datetime) -> bool:
    """
    Validate date of birth
    
    Requirements:
    - Age must be between 15-60 years old
    """
    today = datetime.now()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    return 15 <= age <= 60


def normalize_phone(phone: str) -> str:
    """
    Normalize Indonesian phone number to standard format (+62XXXXXXXXXX)
    
    Examples:
    - 08123456789 -> +628123456789
    - +628123456789 -> +628123456789
    - 628123456789 -> +628123456789
    """
    phone = phone.strip()
    
    if phone.startswith('+62'):
        return phone
    elif phone.startswith('0'):
        return '+62' + phone[1:]
    elif phone.startswith('62'):
        return '+' + phone
    else:
        raise ValueError(f"Format nomor tidak dikenali: {phone}")
