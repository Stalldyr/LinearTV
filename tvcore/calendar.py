import calendar
from calendar import HTMLCalendar
from datetime import datetime, timedelta


def first_day_of_iso_week(year, week):
    jan4 = datetime(year, 1, 4)
    
    # Get the ISO week number and the weekday of January 4th
    start_iso_week, start_iso_day = jan4.isocalendar()[1:3]
    
    # Calculate the difference in weeks, then adjust for the start of the week
    weeks_diff = week - start_iso_week
    days_to_monday = timedelta(days=(1-start_iso_day))
    
    # Calculate the first day of the given ISO week
    return jan4 + days_to_monday + timedelta(weeks=weeks_diff)

def get_iso_week_number(date: datetime) -> int:
    return date.isocalendar()[1]

def get_dates_in_a_week(date: datetime) -> int:
    iso_week = get_iso_week_number(date)
    
    dates = []
    for i in range(1,8):
        dates.append(datetime.fromisocalendar(date.year, iso_week, i))
        
    return dates

def get_iso_week(date:datetime, year:int):
    iso_week = get_iso_week_number(date)

    return (datetime.fromisocalendar(year, iso_week, 1), datetime.fromisocalendar(year, iso_week, 7))

def get_iso_week_span(date: datetime) -> int:
    iso_week = get_iso_week_number(date)
    
    return (datetime.fromisocalendar(date.year, iso_week, 1), datetime.fromisocalendar(date.year, iso_week, 7))

def convert():
    pass

class CustomHTMLCalendar(calendar.HTMLCalendar):
    def __init__(self, year=None, month=None):
        super().__init__(calendar.SUNDAY)
        self.year, self.month = year, month

    def formatday(self, day, weekday):
        if day == 0:
            return ''
        else:
            return f'{day}'

    def formatweek(self, theweek):
        week = ''
        for d, wd in theweek:
            week += self.formatday(d, wd)
        return f'{week}'

    def formatmonth(self, withyear=True):
        return super().formatmonth(self.year, self.month, withyear)




if __name__ == "__main__":
    # Usage
    #custom_calendar = CustomHTMLCalendar(2023, 4)
    #print(custom_calendar.formatmonth())

    print()