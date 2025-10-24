# security/throttles.py
import time
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle


class PhoneRateThrottle(BaseThrottle):
    def __init__(self):
        self.cache_prefix = "throttle"
        self.now = int(time.time())

    def _cache_key(self, prefix, value):
        return f"{self.cache_prefix}:{prefix}:{value}"

    def allow_request(self, request, view):
        phone = request.data.get("phone_number")
        ip = self.get_ident(request)

        if not phone:
            return True

        minute_key = self._cache_key("minute", phone)
        day_key = self._cache_key("day", phone)
        ip_day_key = self._cache_key("ipday", ip)

        block_key = self._cache_key("block", phone)
        ip_block_key = self._cache_key("blockip", ip)

        if cache.get(block_key):
            return False
        if cache.get(ip_block_key):
            return False

        minute_count = cache.get(minute_key, 0)
        day_count = cache.get(day_key, 0)
        ip_day_count = cache.get(ip_day_key, 0)

        if minute_count >= 3:
            cache.set(block_key, True, timeout=30 * 60)
            return False

        if day_count >= 5:
            cache.set(block_key, True, timeout=24 * 60 * 60)
            return False

        if ip_day_count >= 10:
            cache.set(ip_block_key, True, timeout=24 * 60 * 60)
            return False

        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(day_key, day_count + 1, timeout=24 * 60 * 60)
        cache.set(ip_day_key, ip_day_count + 1, timeout=24 * 60 * 60)

        return True