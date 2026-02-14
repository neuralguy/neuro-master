from enum import Enum


class GenerationType(str, Enum):
    """Type of AI generation."""
    IMAGE = "image"
    VIDEO = "video"
    FACESWAP = "faceswap"


class GenerationStatus(str, Enum):
    """Status of generation task."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Status of payment."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BalanceOperationType(str, Enum):
    """Type of balance operation."""
    DEPOSIT = "deposit"           # Пополнение
    GENERATION = "generation"     # Списание за генерацию
    REFERRAL = "referral"         # Бонус за реферала
    WELCOME = "welcome"           # Приветственный бонус
    ADMIN = "admin"               # Изменение админом
    REFUND = "refund"             # Возврат
