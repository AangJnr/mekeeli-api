
import enum

class UserType(str, enum.Enum):
    ORGANIZATION = "ORGANIZATION"
    INDIE = "INDIE"

class SenderType(str, enum.Enum):
    AI = "AI"
    USER = "USER"
