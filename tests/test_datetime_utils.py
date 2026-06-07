from datetime import datetime, timezone

from webapp.datetime_utils import utc_now


def test_utc_now_returns_timezone_aware_utc_datetime():
    now = utc_now()

    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc
