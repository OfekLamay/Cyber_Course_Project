from __future__ import annotations

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.db import transaction

from Cyber_Course_Project.password_policy import load_password_policy
from Sign_In.models import PasswordHistory


def is_recent_password(user: User, raw_password: str) -> bool:
    """
    True if raw_password matches the current password OR any of the last (N-1) history entries.
    Total blocked window ~= N passwords, where N = password_history_count.
    """
    policy = load_password_policy()
    n = int(policy.password_history_count)

    if n <= 0:
        return False

    # Current password
    if user.password and check_password(raw_password, user.password):
        return True

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
    Record a hash in history and prune to (N-1) history entries (since current is stored on user.password).
    """
    policy = load_password_policy()
    n = int(policy.password_history_count)

    if n <= 1:
        PasswordHistory.objects.filter(user=user).delete()
        return

    PasswordHistory.objects.create(user=user, password_hash=password_hash)

    keep = n - 1
    ids_to_keep = list(
        PasswordHistory.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("id", flat=True)[:keep]
    )
    PasswordHistory.objects.filter(user=user).exclude(id__in=ids_to_keep).delete()