from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from .Security_Config import SIGN_IN_CONFIG


class LockdownManagement:

    @staticmethod
    def _cache_key(username):
        return f"login_attempts:{username}"

    @staticmethod
    def is_user_locked(user):
        data = cache.get(LockdownManagement._cache_key(user.username))
        if not data:
            return False

        locked_until = data.get("locked_until")
        return locked_until is not None and timezone.now() < locked_until

    @staticmethod
    def register_failed_attempt(user):
        now = timezone.now()
        key = LockdownManagement._cache_key(user.username)

        data = cache.get(key, {
            "attempts": 0,
            "first_attempt": now,
            "locked_until": None
        })

        # Enforce attempt window from config
        window_seconds = SIGN_IN_CONFIG["attempt_window_seconds"]
        if now - data["first_attempt"] > timedelta(seconds=window_seconds):
            data["attempts"] = 0
            data["first_attempt"] = now
            data["locked_until"] = None

        # 🚫 Prevent exceeding configured attempts
        if data["attempts"] >= SIGN_IN_CONFIG["max_attempts"]:
            return

        data["attempts"] += 1

        # Lock user when limit is reached
        if data["attempts"] == SIGN_IN_CONFIG["max_attempts"]:
            data["locked_until"] = now + timedelta(
                seconds=SIGN_IN_CONFIG["lockout_duration_seconds"]
            )

        cache.set(
            key,
            data,
            timeout=SIGN_IN_CONFIG["lockout_duration_seconds"]
        )

    @staticmethod
    def reset_attempts(user):
        if SIGN_IN_CONFIG["reset_attempts_on_success"]:
            cache.delete(LockdownManagement._cache_key(user.username))