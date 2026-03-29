import bcrypt


def hash_password(password: str) -> str:
    secret = password.encode("utf-8")[:72]
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    secret = password.encode("utf-8")[:72]
    return bcrypt.checkpw(secret, hashed_password.encode("utf-8"))
