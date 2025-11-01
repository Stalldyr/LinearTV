import slugify
from datetime import datetime, timedelta, time as time_class

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