from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs

import phonenumbers
from email_validator import validate_email, EmailNotValidError
from phonenumbers.phonenumberutil import NumberParseException


def normalize_phone(text: str, default_region="US") -> str | None:
    try:
        phone_obj = phonenumbers.parse(text, default_region)

        if not phonenumbers.is_possible_number(phone_obj):
            return None
        if not phonenumbers.is_valid_number(phone_obj):
            return None

        return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)

    except NumberParseException:
        return None


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def parse_date_str(text: str) -> datetime | None:
    try:
        return datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        try:
            return datetime.strptime(text, "%m/%d/%Y")
        except ValueError:
            return None


def is_valid_deadline(date_obj: datetime) -> bool:
    return date_obj.date() >= (datetime.now().date() + timedelta(days=1))




def build_callback_data(**kwargs) -> str:
    """
    Collects callback_data from a dictionary of parameters.
    Example:build_callback_data(action="edit", id=1) → "action=edit&id=1"
    """
    return urlencode(kwargs)


def parse_callback_data(data: str) -> dict[str, str]:
    """
    Parses callback_data back into a dictionary.
    Example:"action=edit&id=1" → {"action": "edit", "id": "1"}
    """
    return {k: v[0] for k, v in parse_qs(data).items()}