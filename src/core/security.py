"""Security utilities for Telegram WebApp authentication."""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, unquote

from src.config import settings
from src.core.exceptions import AuthenticationError
from src.shared.logger import logger

import time as _time


def generate_webapp_token(telegram_id: int) -> str:
    """Generate HMAC token for webapp auth without initData."""
    timestamp = int(_time.time())
    payload = f"{telegram_id}:{timestamp}"
    bot_token = settings.BOT_TOKEN.get_secret_value()
    
    signature = hmac.new(
        bot_token.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    
    return f"{timestamp}:{signature}"


def validate_webapp_token(telegram_id: int, token: str) -> bool:
    """Validate webapp token. Returns True if valid."""
    try:
        parts = token.split(":")
        if len(parts) != 2:
            return False
        
        timestamp = int(parts[0])
        received_signature = parts[1]
        
        payload = f"{telegram_id}:{timestamp}"
        bot_token = settings.BOT_TOKEN.get_secret_value()
        
        expected_signature = hmac.new(
            bot_token.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:32]
        
        return hmac.compare_digest(received_signature, expected_signature)
        
    except Exception:
        return False


def validate_telegram_webapp_data(init_data: str) -> dict:
    """
    Validate Telegram WebApp init data and return user info.
    
    Args:
        init_data: Raw init data string from Telegram WebApp
        
    Returns:
        dict with user data
        
    Raises:
        AuthenticationError: If validation fails
    """
    try:
        # Parse init data
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        
        # Extract hash
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            raise AuthenticationError("Missing hash in init data")
        
        # Check auth_date (optional, but recommended)
        auth_date = parsed_data.get("auth_date")
        if auth_date:
            auth_timestamp = int(auth_date)
            current_timestamp = int(time.time())
            # Allow 24 hours window
            if current_timestamp - auth_timestamp > 86400:
                raise AuthenticationError("Init data expired")
        
        # Build data check string
        data_check_arr = sorted(
            [f"{k}={v}" for k, v in parsed_data.items()]
        )
        data_check_string = "\n".join(data_check_arr)
        
        # Calculate secret key
        bot_token = settings.BOT_TOKEN.get_secret_value()
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256,
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        # Validate hash
        if not hmac.compare_digest(calculated_hash, received_hash):
            raise AuthenticationError("Invalid hash")
        
        # Parse user data
        user_data_raw = parsed_data.get("user")
        if not user_data_raw:
            raise AuthenticationError("Missing user data")
        
        user_data = json.loads(unquote(user_data_raw))
        
        logger.debug(f"WebApp auth success | user_id={user_data.get('id')}")
        
        return {
            "user": user_data,
            "auth_date": auth_date,
            "query_id": parsed_data.get("query_id"),
            "chat_type": parsed_data.get("chat_type"),
            "chat_instance": parsed_data.get("chat_instance"),
        }
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"WebApp auth failed | error={e}")
        raise AuthenticationError(f"Failed to validate init data: {e}")


def generate_file_hash(content: bytes) -> str:
    """Generate SHA256 hash for file content."""
    return hashlib.sha256(content).hexdigest()


def generate_short_id(length: int = 8) -> str:
    """Generate short random ID."""
    import secrets
    return secrets.token_hex(length // 2)
