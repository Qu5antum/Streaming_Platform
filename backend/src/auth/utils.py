from passlib.hash import argon2

def hash_password(password: str):
    hashed_password = argon2.hash(password)
    return hashed_password

def verify_password(password_in: str, hashed_password):
    return argon2.verify(password_in, hashed_password)  