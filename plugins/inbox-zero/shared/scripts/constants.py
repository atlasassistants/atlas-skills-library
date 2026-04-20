"""Plugin-wide numeric constants. Kept in one place so tuning does not require
hunting through multiple modules. See observability-pass spec §Architecture."""

QUOTA_SOFT_BUDGET = 30_000        # Gmail API calls per rolling 24h per user
QUOTA_WARN_PCT = 80               # Warn threshold as percentage of budget
STALE_LOCK_HOURS = 4.0            # Lockfile older than this is reaped as stale
LOG_ROTATE_BYTES = 10_485_760     # 10 MB per log file before rotation
LOG_ROTATE_BACKUPS = 3            # Keep .1 .2 .3 backups
VOICE_GUIDE_STALE_DAYS = 30       # Voice guide older than this raises a finding
