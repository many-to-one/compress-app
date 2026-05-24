import hashlib
from datetime import datetime, timedelta
from jose import jwt
from core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",        # ważne
    bcrypt__rounds=12,         # opcjonalne
    bcrypt__truncate_error=True  # KLUCZOWE
)

# =========================
# NORMALIZE PASSWORD
# =========================
def normalize_password(password: str) -> bytes:
    """
    bcrypt limit = 72 bytes
    SHA-256 digest = 32 bytes → always safe
    """
    return hashlib.sha256(password.encode("utf-8")).digest()


# =========================
# HASH PASSWORD
# =========================
# def get_password_hash(password: str) -> str:
#     normalized = normalize_password(password)
#     return pwd_context.hash(normalized)
def get_password_hash(password: str) -> str:
    normalized = normalize_password(password)

    print("DEBUG PASSWORD RAW:", repr(password))
    print("DEBUG RAW BYTES LEN:", len(password.encode("utf-8")))
    print("DEBUG NORMALIZED TYPE:", type(normalized))
    print("DEBUG NORMALIZED LEN:", len(normalized))

    assert isinstance(normalized, bytes)
    assert len(normalized) <= 72

    return pwd_context.hash(normalized)



# =========================
# VERIFY PASSWORD
# =========================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized = normalize_password(plain_password)
    return pwd_context.verify(normalized, hashed_password)


# =========================
# ACCESS TOKEN
# =========================
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


# =========================
# RESET TOKEN
# =========================
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "SECRET"
ALGORITHM = "HS256"

def create_reset_token(email: str):

    expire = datetime.utcnow() + timedelta(minutes=30)

    data = {
        "sub": email,
        "exp": expire,
        "type": "password_reset"
    }

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


from jose import JWTError

def verify_reset_token(token: str):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("type") != "password_reset":
            return None

        return payload.get("sub")

    except JWTError:
        return None