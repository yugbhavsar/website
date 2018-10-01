from django.conf import settings
import datetime

def debugprint( what ):
    if settings.DEBUG:
        print ( what )

def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    fourth_jan = datetime.date(iso_year, 1, 4 )
    _, fourth_jan_week, fourth_jan_day = fourth_jan.isocalendar()
    return fourth_jan + datetime.timedelta(
        days=iso_day-fourth_jan_day, weeks=iso_week-fourth_jan_week)
