"""Custom application exceptions."""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or "APP_ERROR"
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            message=f"{resource} с ID {identifier} не найден",
            code="NOT_FOUND",
        )


class InsufficientBalanceError(AppException):
    """Not enough tokens on balance."""

    def __init__(self, required: int, available: int):
        super().__init__(
            message=f"Недостаточно токенов. Требуется: {required}, доступно: {available}",
            code="INSUFFICIENT_BALANCE",
        )
        self.required = required
        self.available = available


class UserBannedError(AppException):
    """User is banned."""

    def __init__(self, user_id: int):
        super().__init__(
            message="Ваш аккаунт заблокирован",
            code="USER_BANNED",
        )
        self.user_id = user_id


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field


class ExternalAPIError(AppException):
    """External API error."""

    def __init__(self, service: str, message: str, status_code: int | None = None):
        super().__init__(
            message=f"Ошибка сервиса {service}: {message}",
            code="EXTERNAL_API_ERROR",
        )
        self.service = service
        self.status_code = status_code


class PaymentError(AppException):
    """Payment processing error."""

    def __init__(self, message: str):
        super().__init__(message=message, code="PAYMENT_ERROR")


class AuthenticationError(AppException):
    """Authentication error."""

    def __init__(self, message: str = "Ошибка аутентификации"):
        super().__init__(message=message, code="AUTH_ERROR")


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        super().__init__(
            message="Слишком много запросов. Попробуйте позже.",
            code="RATE_LIMIT",
        )
        self.retry_after = retry_after
