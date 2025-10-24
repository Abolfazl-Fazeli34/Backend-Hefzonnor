import random


def divide_and_spread_remainder(a: int, b: int):
    quotient = a // b
    remainder = a % b

    parts = [quotient] * b

    indices = random.sample(range(b), remainder)
    for i in indices:
        parts[i] += 1

    return parts
