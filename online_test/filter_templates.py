from online_test import app
from datetime import datetime

@app.template_filter('not_started')
def format_not_started(value):
    return (datetime.fromtimestamp(int(value)) - datetime.now()).total_seconds()>0 

@app.template_filter('ongoing')
def format_ongoing(value, duration):
    return (datetime.fromtimestamp(int(value)) - datetime.now()).total_seconds() + (duration * 60) > 0

@app.template_filter('expired')
def format_expired(value):
    return (datetime.fromtimestamp(int(value)) - datetime.now()).total_seconds() + (duration * 60)<= 0 


# start now   durat    state
# 19:00 18:00 01:00    not started
# 18:00 19:00 01:00    ongoing
# 18:00 20:00 01:00    expired