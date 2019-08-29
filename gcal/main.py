import os
import sys

import datetime
import httplib2

import dateutil.parser
import pytz
from apiclient import discovery
from credentials import get_credentials

jst = pytz.timezone('Asia/Tokyo')


def get_service(credentials):
    http = credentials.authorize(httplib2.Http())
    return discovery.build('calendar', 'v3', http=http)


def get_calendars(service):
    r = service.calendarList().list().execute()
    items = r.get('items')
    return [(e['id'], e['summary']) for e in items]


def get_time_range_in_day(dt):
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=jst).isoformat()
    end = dt.replace(hour=23, minute=59, second=59, microsecond=999, tzinfo=jst).isoformat()
    return start, end


def get_events_in_day(service, cal_id, day):
    start, end = get_time_range_in_day(day)
    r = service.events().list(
        calendarId=cal_id, timeMin=start, timeMax=end, singleEvents=True, orderBy='startTime'
    ).execute()

    return [(i['summary'], i['start']['dateTime'], i['end']['dateTime']) for i in r.get('items')]


def list_all_events_in_day(cal_ids, service, today, days):
    results = []
    for cal_id in cal_ids.split(','):
        events = get_events_in_day(service, cal_id, today + datetime.timedelta(days=days))
        for summary, start, end in events:
            start_time = dateutil.parser.parse(start)
            end_time = dateutil.parser.parse(end)
            results.append((start_time, end, start_time, end_time, summary))
    return sorted(results)


def main(args):
    client_secret_file_path = os.environ['GCAL_CLIENT_SECRET_PATH']
    credentials = get_credentials(client_secret_file_path)
    service = get_service(credentials)

    if len(args) == 1:
        cals = get_calendars(service)
        for (id, summary) in cals:
            print(id, summary)
        return

    cal_ids = args[1]
    days = int(args[2])

    opt = ""
    if 4 <= len(args):
        opt = args[3]

    today = datetime.datetime.now(jst)

    for start_time, end, start_time, end_time, summary in list_all_events_in_day(cal_ids, service, today, days):
        if opt == "--no-times":
            print("{event}".format(event=summary))
        else:
            print("{start} - {end} {event}".format(start=start_time.strftime('%H:%M'), end=end_time.strftime('%H:%M'), event=summary))


if __name__ == '__main__':
    main(sys.argv)
