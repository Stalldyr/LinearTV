from datetime import datetime, timedelta, time as time_class
import slugify

def create_path_friendly_name(title):
    return slugify.slugify(title)

def map_days_to_integer(day):
    days_map = {
        "monday": 1,
        "tuesday": 2,
        "wednesday": 3,
        "thursday": 4, 
        "friday": 5,
        "saturday": 6, 
        "sunday": 7,
    }


def map_integer_to_day(number):
    days_map = {
        1: "monday",

    }

def calculate_end_time(start_time, duration_minutes):
    start_hour, start_minute = map(int, start_time.split(':'))
    start_datetime = datetime.combine(datetime.today(), time_class(start_hour, start_minute))
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time().strftime('%H:%M')

def calculate_time_blocks(duration, block_size=30):
    total_blocks = (duration + block_size - 1) // block_size
    return total_blocks

def calculate_time_slots(start, end, steps):
    start2 = datetime.strptime(start, "%H:%M")
    end2 = datetime.strptime(end, "%H:%M")
    
    slots = []

    while start2 < end2:
        slots.append(datetime.strftime(start2, "%H:%M"))
        start2 += timedelta(minutes=int(steps))

    return slots