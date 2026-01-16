"""
Utility functions for formatting dates and times
"""
from datetime import datetime

def format_date(date_str):
    """
    Convert date from YYYY-MM-DD to DD-MM-YYYY format
    """
    if not date_str:
        return ''
    try:
        # Parse the date string
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        # Return in DD-MM-YYYY format
        return date_obj.strftime('%d-%m-%Y')
    except:
        return date_str

def format_time(time_str):
    """
    Convert time from 24-hour to 12-hour format with AM/PM
    """
    if not time_str:
        return ''
    try:
        # Parse the time string
        if isinstance(time_str, str):
            time_obj = datetime.strptime(time_str, '%H:%M')
        else:
            time_obj = time_str
        # Return in 12-hour format with AM/PM
        return time_obj.strftime('%I:%M %p')
    except:
        return time_str

def format_datetime(datetime_str):
    """
    Format datetime to DD-MM-YYYY hh:mm AM/PM
    """
    if not datetime_str:
        return ''
    try:
        if isinstance(datetime_str, str):
            dt_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        else:
            dt_obj = datetime_str
        return dt_obj.strftime('%d-%m-%Y %I:%M %p')
    except:
        return datetime_str
