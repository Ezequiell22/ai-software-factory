from datetime import datetime
from zoneinfo import ZoneInfo
from .settings import settings
def inside_work_window(now=None):
    tz = ZoneInfo(settings.app_timezone)
    current = now.astimezone(tz) if now else datetime.now(tz)
    return settings.work_start_hour <= current.hour < settings.work_end_hour
