from datetime import timedelta
from jinja2 import Template
import os
from datetime import datetime, timedelta
import pytz
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Try to import personal config, fall back to template if not found
try:
    from config import *
except ImportError:
    print("[!] Personal config.py not found. Please copy config_template.py to config.py and update settings.")
    from config_template import *

# === AUTHENTICATION ===
def get_authenticated_service():
    
    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(f"token.json not found at {TOKEN_PATH}. Ask ChatGPT for help.")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('calendar', 'v3', credentials=creds)


# === CALENDAR SETUP ===
def get_calendar_ids(service, calendar_names):
    calendar_list = service.calendarList().list().execute().get('items', [])
    id_map = {cal['summary']: cal['id'] for cal in calendar_list}
    missing = [name for name in calendar_names if name not in id_map]
    if missing:
        raise ValueError(f"Could not find calendars: {missing}")
    return {name: id_map[name] for name in calendar_names}

# === TIME RANGE ===
def get_week_bounds(week_offset=0):
    """Get the datetime bounds for a work week (Mon-Fri) offset from current week.
    
    Args:
        week_offset (int): Number of weeks forward from current week (0 = current week)
        
    Returns:
        tuple: (monday, friday) datetime objects representing the week bounds
               monday is set to midnight (00:00)
               friday is set to end of day (23:59)
    """
    # Get today's date
    today = datetime.now()
    
    # Calculate Monday by subtracting days since last Monday
    monday = today - timedelta(days=today.weekday())
    
    # Add the requested week offset
    monday += timedelta(weeks=week_offset)
        
    # Calculate Friday as 5 days after Monday
    friday = monday + timedelta(days=5)
    
    # Set times to start/end of day and return
    return monday.replace(hour=0, minute=0), friday.replace(hour=23, minute=59)

# === PULL EVENTS ===
def get_events(service, calendar_ids, start_dt, end_dt):
    all_events = []
    time_min = start_dt.isoformat() + 'Z'
    time_max = end_dt.isoformat() + 'Z'
    for cal_name, cal_id in calendar_ids.items():
        events = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])
        for e in events:
            s = e['start'].get('dateTime')
            e_ = e['end'].get('dateTime')
            if s and e_:
                all_events.append((s, e_))
    return all_events


def plot_availability_html(events, start_dt, end_dt, filename):
    tz = pytz.timezone(TIMEZONE)

    # Localize start/end datetimes
    start_dt = tz.localize(start_dt)
    end_dt = tz.localize(end_dt)

    # Normalize and collect busy intervals
    busy_blocks = set()
    for s_raw, e_raw in events:
        s = datetime.fromisoformat(s_raw).astimezone(tz)
        e = datetime.fromisoformat(e_raw).astimezone(tz)

        # Clip to M–F 8–18
        s = max(s, start_dt.replace(hour=HOURS_START, minute=0))
        e = min(e, end_dt.replace(hour=HOURS_END, minute=0))

        # Fill grid in 30-minute blocks
        while s < e:
            if s.weekday() < 5 and HOURS_START <= s.hour < HOURS_END:
                busy_blocks.add((s.strftime('%A'), s.hour, s.minute // 30))
            s += timedelta(minutes=30)

    # Read HTML template from file
    with open(os.path.join(BASE_PATH, 'cal_template.html')  , 'r') as f:
        template = Template(f.read())

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    html = template.render(
        days=days,
        hours=list(range(HOURS_START, HOURS_END)),
        busy_blocks=busy_blocks,
        start_date=start_dt.strftime('%b %d'),
        end_date=(start_dt + timedelta(days=4)).strftime('%b %d'),
        calendar_title=CALENDAR_TITLE
    )

    with open(filename, 'w') as f:
        f.write(html)

    print(f"[✓] HTML calendar saved to: {filename}")
    
# === MAIN ===
def main():
    service = get_authenticated_service()
    calendar_ids = get_calendar_ids(service, CALENDAR_NAMES)

    # Change to the git repo directory
    os.chdir(os.path.expanduser(GITPATH))

    # Generate calendars for the next 4 weeks
    for week_offset in range(4):
        
        # Get start/end dates for this week
        start_dt, end_dt = get_week_bounds(week_offset=week_offset)
        
        # Get events for this week's date range
        events = get_events(service, calendar_ids, start_dt, end_dt)

        # Generate the HTML file for this week
        filename = f'availability_{week_offset}.html'
        plot_availability_html(events, start_dt, end_dt, filename)

        # Add the file to git
        os.system(f'git add {filename}')

    # Commit all the calendar files
    os.system('git commit -m "Update availability calendars"')

    # Push the changes
    os.system('git push')

    print(f"[✓] Changes pushed to git repository at {GITPATH}")

if __name__ == '__main__':
    main()
