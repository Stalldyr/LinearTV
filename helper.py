import slugify
from datetime import datetime, timedelta, time as time_class
import os

def _create_path_friendly_name(title):
    return slugify.slugify(title)

def _calculate_end_time(start_time, duration_minutes):
    start_hour, start_minute = map(int, start_time.split(':'))
    start_datetime = datetime.combine(datetime.today(), time_class(start_hour, start_minute))
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time().strftime('%H:%M')

def calculate_time_blocks(duration, block_size=30):
    total_blocks = (duration + block_size - 1) // block_size
    return total_blocks

def verify_path(filepath):
    return os.path.exists(filepath)

def _create_file_name(directory, season, episode):
    return f"{directory}_s{season:02d}e{episode:02d}.mp4"

def create_movie_file_name(directory):
    return f"{directory}.mp4"

def create_path(*args):
    return os.path.join(*args)

def _map_days_to_integer(day):
    pass

def _map_integer_to_day(number):
    days_map = {
        1: "monday",

    }