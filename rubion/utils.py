## @package rubion.utils
# Some utilities used in the website

from django.conf import settings
import datetime


## prints to standard out if the debug setting is true
# @param what The text to print
def debugprint( what ):
    if settings.DEBUG:
        print ( what )

## returns the gregorian representation of a iso data
# @param iso_year Year in iso format
# @param iso_week Week in iso format
# @param iso_day Day in iso format
# @returns The date in gregorian format
def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    fourth_jan = datetime.date(iso_year, 1, 4 )
    _, fourth_jan_week, fourth_jan_day = fourth_jan.isocalendar()
    return fourth_jan + datetime.timedelta(
        days=iso_day-fourth_jan_day, weeks=iso_week-fourth_jan_week)
