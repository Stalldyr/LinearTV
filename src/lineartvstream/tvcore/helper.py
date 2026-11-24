from datetime import datetime, timedelta, timezone, date
import re

def calculate_time_slots(start:str, end:str, steps:int):
    """
    Calculates time slots for schedule table
    """

    start_dt = datetime.strptime(start, "%H:%M")
    end_dt = datetime.strptime(end, "%H:%M")
    
    slots = []

    while start_dt < end_dt:
        slots.append(datetime.strftime(start_dt, "%H:%M"))
        start_dt += timedelta(minutes=int(steps))

    return slots

def calculate_offset(start_time:datetime, current_time:datetime, buffer_seconds:int=10):
    offset = (current_time - start_time).seconds - buffer_seconds
    return max(0, offset)




def get_iso_week_span(start_date: datetime, end_date:datetime=None) -> tuple:
    start_date_iso = start_date.isocalendar()
    if end_date is None:
        return date.fromisocalendar(start_date_iso.year, start_date_iso.week, 1), date.fromisocalendar(start_date_iso.year, start_date_iso.week, 7)

    end_date_iso = start_date.isocalendar()
    return date.fromisocalendar(start_date_iso.year, start_date_iso.week, 1), date.fromisocalendar(end_date_iso.year, end_date_iso.week, 7)

def get_iso_week_span_target_year(start_week: int, end_week: int, target_year: int):
    return (datetime.fromisocalendar(target_year, start_week ,1).date(), datetime.fromisocalendar(target_year, end_week, 1).date())




def parse_aspnet_date(date_str):
    match = re.search(r'/Date\((\d+)([+-]\d{4})\)/', date_str)
    if not match:
        raise ValueError(f"Void date format: {date_str}")
    
    ms = int(match.group(1))
    tz_str = match.group(2)
    
    tz_hours = int(tz_str[1:3])
    tz_minutes = int(tz_str[3:5])
    sign = 1 if tz_str[0] == '+' else -1
    tz = timezone(timedelta(hours=sign * tz_hours, minutes=sign * tz_minutes))
    
    return datetime.fromtimestamp(ms / 1000, tz=tz)

def same_iso_week_this_year(dt: date, target_year: int = None) -> date:
    if target_year is None:
        target_year = date.today().isocalendar().year
    
    _, week, weekday = dt.isocalendar()
    new_date = date.fromisocalendar(target_year, week, weekday)
    return dt.replace(year=new_date.year, month=new_date.month, day=new_date.day)