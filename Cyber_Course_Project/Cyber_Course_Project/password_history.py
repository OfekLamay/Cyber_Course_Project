from __future__ import annotations

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.db import transaction

from Cyber_Course_Project.password_policy import load_password_policy
from Sign_In.models import PasswordHistory


def is_recent_password(user: User, raw_password: str) -> bool:
    """
    Returns True if raw_password matches any of the last N password hashes
    (including current password).
    """
    policy = load_password_policy()
    n = int(policy.password_history_count)

    if n <= 0:
        return False

    # Check current password hash first
    if user.password and check_password(raw_password, user.password):
        return True

    # Check last (n-1) historical hashes (so total checked ~= n including current)
    remaining = max(n - 1, 0)
    if remaining == 0:
        return False

    recent_hashes = (
        PasswordHistory.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("password_hash", flat=True)[:remaining]
    )

    for h in recent_hashes:
        if h and check_password(raw_password, h):
            return True

    return False


@transaction.atomic
def record_password_hash(user: User, password_hash: str) -> None:
    """
    Record a password hash in history, and prune older entries according
    to password_history_count (keeping only the last N-1 historical hashes,
    since 'current' is stored on user.password).
    """
    policy = load_password_policy()
    n = int(policy.password_history_count)

    if n <= 1:
        # If N==1, only "current password" matters; no need to store history.
        PasswordHistory.objects.filter(user=user).delete()
        return

    PasswordHistory.objects.create(user=user, password_hash=password_hash)

    # Keep only the last (n-1) history entries
    keep = n - 1
    ids_to_keep = list(
        PasswordHistory.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("id", flat=True)[:keep]
    )
    PasswordHistory.objects.filter(user=user).exclude(id__in=ids_to_keep).delete()