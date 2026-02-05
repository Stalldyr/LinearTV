from datetime import datetime, timedelta, time as time_class
import slugify

def create_path_friendly_name(title):
    return slugify.slugify(title)

def calculate_end_time(start_time:str, duration_minutes:int):
    start_hour, start_minute = map(int, start_time.split(':'))
    start_datetime = datetime.combine(datetime.today(), time_class(start_hour, start_minute))
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time().strftime('%H:%M')

def calculate_time_blocks(duration:int, block_size:int=30):
    return (duration + block_size - 1) // block_size

def calculate_time_slots(start:str, end:str, steps:int):
    """
    Calculates time slots for schedule table

    start: schedule start time
    end: schedule end time
    steps: schedule steps (in minutes)
    """

    start_dt = datetime.strptime(start, "%H:%M")
    end_dt = datetime.strptime(end, "%H:%M")
    
    slots = []

    while start_dt < end_dt:
        slots.append(datetime.strftime(start_dt, "%H:%M"))
        start_dt += timedelta(minutes=int(steps))

    return slots