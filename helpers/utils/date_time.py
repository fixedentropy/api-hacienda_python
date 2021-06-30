from datetime import datetime, time, tzinfo

from dateutil import utils as du_utils, parser, tz
from pytz import timezone

from helpers.errors.exceptions import ValidationError
from helpers.errors.enums import ValidationErrorCodes


TZ_CR = tz.gettz('America/Costa_Rica')


def parse_datetime_range_cr(since: str, until: str):
    date_since, date_before = get_today_datetime_range_cr()
    if isinstance(since, str):
        date_since = parse_datetime(
            since, 'since/desde', day_first=False
        )
    if isinstance(until, str):
        date_before = parse_datetime(
            until, 'before/hasta', day_first=False
        )
        date_before = datetime.combine(date_before.date(), time.max, date_before.tzinfo)

    return date_since, date_before


def get_today_datetime_range_cr():
    return get_today_datetime_range(timezone('America/Costa_Rica'))


def get_today_datetime_range(time_zone: tzinfo):
    dt_begin = du_utils.today(time_zone)
    dt_end = datetime.combine(dt_begin.date(), time.max, time_zone)
    return dt_begin, dt_end


def parse_datetime(value, field, day_first: bool = True) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, int) \
            or isinstance(value, str) and value.isdigit():  # avoid parsing digit-only values
        raise ValidationError(
            value, field,
            error_code=ValidationErrorCodes.INVALID_DATETIME_FORMAT
        )

    try:
        parsed = du_utils.default_tzinfo(
            parser.parse(value, dayfirst=day_first), TZ_CR
        )
    except (ValueError, OverflowError) as ver:
        raise ValidationError(
            value, field,
            error_code=ValidationErrorCodes.INVALID_DATETIME_FORMAT
        ) from ver
    else:
        return parsed
