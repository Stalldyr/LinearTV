import slugify
from datetime import datetime, timedelta, time as time_class
import os

def _create_valid_filename(title):
    return slugify.slugify(title)

def _calculate_end_time(start_time, duration_minutes):
    start_hour, start_minute = map(int, start_time.split(':'))
    start_datetime = datetime.combine(datetime.today(), time_class(start_hour, start_minute))
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time().strftime('%H:%M')

def _calculate_blocks(duration, block_size=30):
    total_blocks = (duration + block_size - 1) // block_size
    return total_blocks

def _verify_local_file(filepath):
    if os.path.exists(filepath):
        return True
    print(f"Lokal fil ikke funnet: {filepath}")
    return False

def _get_file_path(*args):
    return os.path.join(*args)

def _map_days_to_integer(day):
    pass

def _map_integer_to_day(number):
    days_map = {
        1: "monday",

    }