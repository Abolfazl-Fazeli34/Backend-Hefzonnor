# account/services/otp_service.py
from django.core.cache import cache
import random

class OTPService:
    def __init__(self, phone_number, length=6, ttl=300):
        self.phone_number = phone_number
        self.length = length
        self.ttl = ttl
        self.cache_key = f"otp:{self.phone_number}"

    def generate(self):
        if cache.get(self.cache_key):
            cache.delete(self.cache_key)

        otp = str(random.randint(10**(self.length-1), 10**self.length - 1))
        cache.set(self.cache_key, otp, timeout=self.ttl)
        return otp

    def send(self, otp):
        print(f"OTP for {self.phone_number}: {otp}")

    def verify(self, code):
        otp = cache.get(self.cache_key)
        if otp is None:
            return False, "OTP expired"
        if otp != code:
            return False, "Invalid OTP"
        cache.delete(self.cache_key)
        return True, "OTP verified"
