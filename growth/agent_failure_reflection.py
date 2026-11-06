"""E3: evidence-based fallback gates from *verified* previous failure results.

The workflow remains deterministic for known failures. This is intentional:
no model may synthesize a tool name, re-grant OAuth or retry a possibly
published social post. Actions resume only after bounded cooldown or
independent official-source evidence of recovery.
"""
from datetime import datetime, timedelta, timezone

AUTH_BLOCKERS = frozenset({
    "meta_owner_oauth_unavailable",
    "awaiting_official_oauth",
    "identity_unavailable",
    "identity_mismatch",
    "missing_threads_manage_insights_or_unavailable",
})
PERSISTENCE_ERRORS = frozenset({
    "provider_saved_but_source_readback_missing",
    "readback_unverified",
    "readback_unavailable",
    "snapshot_write_unverified",
})
HARD_PAUSE = timedelta(hours=72)
SOFT_PAUSE = timedelta(hours=12)
MAX_HISTORY = 100


def aware(value):
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone needed")
    return dt.astimezone(timezone.utc)


def classify(history, *, action, observed_at, now):
    """Explain if and why this action should be withheld.

    Return a sanitized, bounded decision; never forward remote exception text,
    raw model tool arguments or credentials into agent memory.
    """
    now, observed_at = aware(now), aware(observed_at)
    if not isinstance(history, list):
        raise ValueError("untrusted_history")
    if len(history) > MAX_HISTORY:
        raise ValueError("history_too_large")
    for entry in reversed(history):
        if not isinstance(entry, dict) or entry.get("selected_action") != action:
            continue
        if entry.get("status") not in ("blocked", "unverified"):
            continue
        reason = entry.get("result_code")
        if reason not in AUTH_BLOCKERS and reason not in PERSISTENCE_ERRORS:
            continue
        try:
            failed_at = aware(entry["finished_at"])
        except (TypeError, KeyError, ValueError, OverflowError):
            # An ambiguous failure timeline must not grant auto-retry.
            return {"allow": False, "reason": "previous_failure_time_unverified",
                    "requires": "owner_review"}
        age = now - failed_at
        if not timedelta(0) <= age <= timedelta(days=7):
            continue
        # A confirmed official observation newer than the failure is an
        # independent recovery signal: a scope/identity may have been fixed.
        if observed_at > failed_at + timedelta(minutes=2):
            return {"allow": True, "reason": "official_source_newer_than_failure",
                    "requires": "normal_policy_gate"}
        pause = HARD_PAUSE if reason in AUTH_BLOCKERS else SOFT_PAUSE
        if age < pause:
            return {
                "allow": False,
                "reason": "owner_permission_or_identity_action" if reason in AUTH_BLOCKERS
                    else "source_readback_recovery_required",
                "requires": "owner_reconnect_or_independent_proof" if reason in AUTH_BLOCKERS
                    else "diagnose_private_storage_before_requery",
            }
    return {"allow": True, "reason": "no_recent_blocking_outcome",
            "requires": "normal_policy_gate"}
