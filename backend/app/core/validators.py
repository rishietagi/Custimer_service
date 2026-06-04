import re
from datetime import datetime, date

def validate_model_number(model: str) -> tuple[bool, str]:
    """Validates that product model number is not empty and has a reasonable length."""
    if not model or not model.strip():
        return False, "Model number cannot be empty."
    if len(model.strip()) < 3:
        return False, "Model number must be at least 3 characters."
    return True, ""

def validate_pincode(pincode: str) -> tuple[bool, str]:
    """Validates that pincode is numeric and of valid length (5 or 6 digits)."""
    if not pincode or not pincode.strip():
        return False, "Pincode is required."
    clean_pincode = pincode.strip()
    if not clean_pincode.isdigit():
        return False, "Pincode must contain only numbers."
    if len(clean_pincode) not in [5, 6]:
        return False, "Pincode must be 5 or 6 digits long."
    return True, ""

def validate_phone(phone: str) -> tuple[bool, str]:
    """Validates that phone number is valid (e.g., 10 digits, numeric/standard characters)."""
    if not phone or not phone.strip():
        return False, "Phone number is required."
    
    # Strip common formatting characters
    clean_phone = re.sub(r"[\s\-\(\)\+]", "", phone)
    
    if not clean_phone.isdigit():
        return False, "Phone number must contain only numbers after stripping symbols."
    
    if len(clean_phone) < 10 or len(clean_phone) > 15:
        return False, "Phone number must be between 10 and 15 digits."
    
    return True, ""

def validate_future_date(dt_val) -> tuple[bool, str]:
    """Validates that the preferred date is not in the past."""
    if not dt_val:
        return False, "Preferred date is required."
    
    current_date = date.today()
    if isinstance(dt_val, str):
        try:
            # Try ISO format first, then default %Y-%m-%d
            if "T" in dt_val:
                dt_val = dt_val.split("T")[0]
            target_date = datetime.strptime(dt_val, "%Y-%m-%d").date()
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD."
    elif isinstance(dt_val, datetime):
        target_date = dt_val.date()
    elif isinstance(dt_val, date):
        target_date = dt_val
    else:
        return False, "Invalid date type."

    if target_date < current_date:
        return False, "Preferred date cannot be in the past."
    
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    """Simple email validation check."""
    if not email or not email.strip():
        return False, "Email cannot be empty."
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email.strip()):
        return False, "Invalid email address format."
    return True, ""

def validate_serial_number(serial: str) -> tuple[bool, str]:
    """Validates that serial number is not empty and has a reasonable length."""
    if not serial or not serial.strip():
        return False, "Serial number cannot be empty."
    if len(serial.strip()) < 5:
        return False, "Serial number must be at least 5 characters."
    return True, ""
