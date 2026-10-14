from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# Titkosítási beállítások
SECRET_KEY = "szakdolgozat_titkos_es_biztonsagos_kulcsa_123!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 óráig érvényes a belépési token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Beérkező jelszó ellenőrzése az adatbázisban lévő hash-sel"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Jelszó titkosítása (hash-elése)"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """JWT belépőkártya (token) generálása"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt