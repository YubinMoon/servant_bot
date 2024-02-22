import hashlib


def generate_key(string: str, length: int) -> str:
    hashed_string = hashlib.sha256(string.encode()).hexdigest()
    key = hashed_string[:length]
    return key
