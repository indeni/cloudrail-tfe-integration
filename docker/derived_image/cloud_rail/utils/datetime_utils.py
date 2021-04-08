import logging
from datetime import datetime

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%SZ'
DATETIME_REGEX = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}Z'


def convert_datetime_to_str(date: datetime) -> str:
    try:
        return date.strftime(DATETIME_FORMAT)
    except Exception:
        logging.exception('failed convert datetime {} to str'.format(date))


def convert_str_to_datetime(date: str) -> datetime:
    try:
        return datetime.strptime(date, DATETIME_FORMAT)
    except Exception:
        logging.exception('failed convert str {} to datetime'.format(date))
