import calendar
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def site_time(request):
    local_tz = ZoneInfo(settings.TIME_ZONE)
    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc, local_tz)
    month_calendar = calendar.TextCalendar(firstweekday=0).formatmonth(
        now_local.year,
        now_local.month,
    )
    return {
        "server_timezone": settings.TIME_ZONE,
        "now_utc": now_utc,
        "now_local": now_local,
        "text_calendar": month_calendar,
    }
