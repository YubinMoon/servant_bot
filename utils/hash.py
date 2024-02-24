import hashlib
import random
import string


def generate_key(source: str, length: int) -> str:
    hashed_string = hashlib.sha256(source.encode()).hexdigest()
    key = hashed_string[:length]
    return key


def get_random_key(length: int = 6) -> str:
    letters = string.ascii_uppercase
    return "".join(random.choice(letters) for _ in range(length))
