from passlib.hash import argon2
from pydantic import SecretStr

def hash_password(password: SecretStr):
    hashed_password = argon2.hash(password.get_secret_value())
    return hashed_password

def verify_password(password_in: str, hashed_password):
    return argon2.verify(password_in, hashed_password)  