from datetime import datetime, timezone
import pytz
import jdatetime
from nudgemate.config import settings

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_persian_digits(text: str | int) -> str:
    """Converts English digits to Persian digits."""
    return str(text).translate(PERSIAN_DIGITS)


def get_current_time() -> datetime:
    """Returns current datetime aware of the configured timezone."""
    tz = pytz.timezone(settings.TIMEZONE)
    return datetime.now(tz)


def format_jalali(dt: datetime | str, include_time: bool = True) -> str:
    """
    Converts Gregorian datetime to human-readable Jalali (Shamsi) string.
    Example: ۱۴۰۵/۰۷/۱۱ ساعت ۱۲:۳۰
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt

    tz = pytz.timezone(settings.TIMEZONE)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)

    jdt = jdatetime.datetime.fromgregorian(datetime=dt)
    
    # Persian weekday name
    weekdays = [
        "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
        "چهارشنبه", "پنج‌شنبه", "جمعه"
    ]
    weekday_name = weekdays[jdt.weekday()]
    
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    month_name = months[jdt.month - 1]

    if include_time:
        formatted = f"{weekday_name} {jdt.day} {month_name} ساعت {jdt.strftime('%H:%M')}"
    else:
        formatted = f"{weekday_name} {jdt.day} {month_name} {jdt.year}"

    return to_persian_digits(formatted)


def format_relative_time(target_dt: datetime | str) -> str:
    """Returns friendly relative time in Persian, e.g., '۱۰ دقیقه دیگر'."""
    if isinstance(target_dt, str):
        try:
            target_dt = datetime.fromisoformat(target_dt)
        except Exception:
            return ""

    now = get_current_time()
    tz = pytz.timezone(settings.TIMEZONE)
    if target_dt.tzinfo is None:
        target_dt = tz.localize(target_dt)
    else:
        target_dt = target_dt.astimezone(tz)

    delta = target_dt - now
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        return "سررسید گذشته"
    elif total_seconds < 60:
        return "کمتر از یک دقیقه دیگر"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return to_persian_digits(f"{minutes} دقیقه دیگر")
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        rem_min = (total_seconds % 3600) // 60
        if rem_min > 0:
            return to_persian_digits(f"{hours} ساعت و {rem_min} دقیقه دیگر")
        return to_persian_digits(f"{hours} ساعت دیگر")
    else:
        days = total_seconds // 86400
        return to_persian_digits(f"{days} روز دیگر")
