import argparse
import os
import sys
from functools import reduce

import datetime
import httplib2

from collections import defaultdict

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

    for i in r.get('items'):
        start = i['start'].get('dateTime')
        end = i['end'].get('dateTime')
        yield i['summary'], start, end


def list_all_events_in_day(cal_ids, service, today, days, skip_entire_event=False):
    results = []
    for cal_id in cal_ids.split(','):
        events = get_events_in_day(service, cal_id, today + datetime.timedelta(days=days))
        for summary, start, end in events:
            if all([skip_entire_event, start is None, end is None]):
                continue
            if start is None:
                start = '00:00'
            if end is None:
                end = '00:00'
            start_time = dateutil.parser.parse(start)
            end_time = dateutil.parser.parse(end)
            results.append((start, end, start_time, end_time, summary))
    return sorted(results)


def list_cals(service, args):
    cals = get_calendars(service)
    for (id, summary) in cals:
        print(id, summary)


def list_events(service, args):
    today = datetime.datetime.now(jst)

    for start, end, start_time, end_time, summary in list_all_events_in_day(args.cal_ids, service, today, args.days, args.skip_entire):
        prefix = '- ' if args.markdown_list else ''

        if args.no_times:
            print("{prefix}{event}".format(prefix=prefix, event=summary))
        else:
            print("{prefix}{start} - {end} {event}".format(
                prefix=prefix, start=start_time.strftime('%H:%M'), end=end_time.strftime('%H:%M'), event=summary))


def calc_hours(service, args):
    today = datetime.datetime.now(jst)

    events = defaultdict(list)

    for _, _, start_time, end_time, summary in list_all_events_in_day(args.cal_ids, service, today, args.days, True):
        events[summary].append(end_time - start_time)

    total = None
    for (summary, time_list) in events.items():
        if args.no_times:
            print(summary)
        else:
            time = reduce(lambda a, b: a + b, time_list)
            print("{0} - {1}".format(summary, time))
            total = time if total is None else total + time

    if total is not None:
        print("\nTotal: {0}".format(total))


def main(args):
    client_secret_file_path = os.environ['GCAL_CLIENT_SECRET_PATH']
    credentials = get_credentials(client_secret_file_path)
    service = get_service(credentials)

    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(title='sub commands')

    list_parser = sub.add_parser('list')
    list_parser.set_defaults(func=list_cals)

    event_parser = sub.add_parser('events')
    event_parser.set_defaults(func=list_events)
    event_parser.add_argument('cal_ids', nargs='?')
    event_parser.add_argument('days', type=int, nargs='?')
    event_parser.add_argument('--no-times', action='store_true')
    event_parser.add_argument('--markdown-list', action='store_true')
    event_parser.add_argument('--skip-entire', action='store_true')

    hour_parser = sub.add_parser('hour')
    hour_parser.set_defaults(func=calc_hours)
    hour_parser.add_argument('cal_ids', nargs='?')
    hour_parser.add_argument('days', type=int, nargs='?')
    hour_parser.add_argument('--no-times', action='store_true')

    args = parser.parse_args()
    try:
        args.func(service, args)
    except AttributeError:
        parser.print_help()


if __name__ == '__main__':
    main(sys.argv)
