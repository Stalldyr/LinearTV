import calendar
from datetime import datetime, timedelta, timezone, date
import re


def first_day_of_iso_week(year, week):
    jan4 = datetime(year, 1, 4)
    
    # Get the ISO week number and the weekday of January 4th
    start_iso_week, start_iso_day = jan4.isocalendar()[1:3]
    
    # Calculate the difference in weeks, then adjust for the start of the week
    weeks_diff = week - start_iso_week
    days_to_monday = timedelta(days=(1-start_iso_day))
    
    # Calculate the first day of the given ISO week
    return jan4 + days_to_monday + timedelta(weeks=weeks_diff)

def get_iso_week(date: datetime) -> tuple:
    return date.isocalendar()

def get_iso_week_number(date: datetime) -> int:
    return date.isocalendar()[1]

def get_dates_in_a_week(date: datetime) -> int:
    iso_week = get_iso_week_number(date)
    
    dates = []
    for i in range(1,8):
        dates.append(datetime.fromisocalendar(date.year, iso_week, i))
        
    return dates

def get_iso_week_span(start_date: datetime, end_date:datetime) -> tuple:
    return datetime.fromisocalendar(start_date.year, get_iso_week_number(start_date), 1), datetime.fromisocalendar(end_date.year, get_iso_week_number(end_date), 7)

def get_number_of_weeks(start_date: datetime, end_date:datetime):
    return datetime.fromisocalendar(end_date.year, get_iso_week_number(end_date),1) - datetime.fromisocalendar(start_date.year, get_iso_week_number(start_date),1)


def get_iso_week_span_target_year(start_week: int, end_week: int, target_year: int):
    return (datetime.fromisocalendar(target_year, start_week ,1), datetime.fromisocalendar(target_year, end_week, 1))

def parse_aspnet_date(date_str):
    match = re.search(r'/Date\((\d+)([+-]\d{4})\)/', date_str)
    if not match:
        raise ValueError(f"Ugyldig dato-format: {date_str}")
    
    ms = int(match.group(1))
    tz_str = match.group(2)
    
    tz_hours = int(tz_str[1:3])
    tz_minutes = int(tz_str[3:5])
    sign = 1 if tz_str[0] == '+' else -1
    tz = timezone(timedelta(hours=sign * tz_hours, minutes=sign * tz_minutes))
    
    return datetime.fromtimestamp(ms / 1000, tz=tz)

def same_iso_week_this_year(dt: date, target_year: int = None) -> date:
    #TODO: Move to calendar module??
    if target_year is None:
        target_year = date.today().isocalendar().year
    
    _, week, weekday = dt.isocalendar()
    new_date = date.fromisocalendar(target_year, week, weekday)
    return dt.replace(year=new_date.year, month=new_date.month, day=new_date.day)