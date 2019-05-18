from datetime import (datetime, timedelta, timezone)
from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info
import os

@requires_segment_info
class GoogleCalendarSegment(ThreadedSegment):

    interval = 300
    service = None
    dev_key = None
    first_run = True

    def set_state(self, developer_key, credentials=os.path.expanduser('~') + '/.config/powerline/gcalendar_credentials', range=1, **kwargs):
        self.dev_key = developer_key
        self.cred_path = credentials
        self.range = range
        self.invalid = True
        self.service = None

        super(GoogleCalendarSegment, self).set_state(**kwargs)

    def init_service(self, **kwargs):
        if not self.service:
            import httplib2

            from apiclient.discovery import build
            from oauth2client.file import Storage

            # If the Credentials don't exist or are invalid, run through the native client
            # flow. The Storage object will ensure that if successful the good
            # Credentials will get written back to a file.
            if not os.path.exists(self.cred_path):
                super(GoogleCalendarSegment, self).set_state(**kwargs)
                self.invalid = True
                return None

            storage = Storage(self.cred_path)
            credentials = storage.get()
            if credentials is None or credentials.invalid == True:
                super(GoogleCalendarSegment, self).set_state(**kwargs)
                self.invalid = True
                return None

            # Create an httplib2.Http object to handle our HTTP requests and authorize it
            # with our good Credentials.
            http = httplib2.Http()
            http = credentials.authorize(http)

            self.service = build(serviceName='calendar', version='v3',
                    http=http, developerKey=self.dev_key)
        self.invalid = False

    def get_remind(self, dict):
        mx = 0
        for d in dict:
            mx = max(mx, d['minutes'])
        return mx

    def update(self, *args, **kwargs):
        if self.invalid:
            # If the user has a really slow internet connection,
            # we don't want that this segment incurs a delay before the
            # powerline is shown.
            if self.first_run:
                self.first_run = False
                return []
            if self.dev_key:
                self.init_service(**kwargs)
            if self.invalid:
                return None

        # Get the list of all calendars
        calendars = self.service.calendarList().list().execute()['items']

        # Get the next count events from every calendar
        result = [self.service.events().list(
            calendarId=id,
            orderBy='startTime',
            singleEvents=True,
            timeMin=datetime.now(timezone.utc).isoformat(),
            timeMax=(datetime.now(timezone.utc) + timedelta(self.range)).isoformat()
        ).execute() for id in [c['id'] for c in calendars]]

        result = [(c['items'], self.get_remind(c['defaultReminders'])) for c in result]
        return sum([[(e,r) for e in c] for c, r in result], []) or []

    def render(self, events, segment_info, format='{summary}{time}',
            short_format='{short_summary}{time}', time_format=' (%H:%M)', count=3, show_count=False,
            hide_times=[" (00:00)"], auto_shrink=False, single_when_shrunk=True, **kwargs):

        channel_name = 'appoints.gcalendar'
        channel_full = 'payloads' in segment_info and channel_name in segment_info['payloads'] and segment_info['payloads'][channel_name]

        long_mode = not auto_shrink or channel_full
        short_mode = single_when_shrunk and not long_mode

        if events is None:
            return [{
                'contents': 'No valid credentials' if long_mode else
                    short_format.format(short_summary='', summary='', time='', location='',
                    count='', error='/!\\'),
                'payload_name': channel_name,
                'highlight_groups': ['appoint:error', 'appoint:urgent', 'appoint']
            }]
        segments = []
        if show_count and len(events) > 0 and not short_mode:
            segments += [{
                'contents': str(len(events)),
                'payload_name': channel_name,
                'highlight_groups': ['appoint:count', 'appoint']
            }]

        # Sort all events
        def remove_at(string, pos):
            return string[:pos] + string[pos+1:]

        try:
            events = [(
                datetime.strptime(ev['start']['date']+'+0000', "%Y-%m-%d%z") if 'date' in ev['start'] else datetime.strptime(remove_at(ev['start']['dateTime'],-3), "%Y-%m-%dT%H:%M:%S%z"),
                ev['summary'],
                ev['location'] if 'location' in ev else '(???)',
                timedelta(minutes=self.get_remind(ev['reminders']['overrides']), seconds=self.interval) if 'reminders' in ev and 'overrides' in ev['reminders'] else timedelta(minutes=bf)
            ) for ev, bf in events]
        except ValueError:
            events = [(
                datetime.strptime(ev['start']['date']+'+0000', "%Y-%m-%d%z") if 'date' in ev['start'] else datetime.strptime(remove_at(ev['start']['dateTime'],-3)+'+0000', "%Y-%m-%dT%H:%M:%SZ%z"),
                ev['summary'],
                ev['location'] if 'location' in ev else '(???)',
                timedelta(minutes=self.get_remind(ev['reminders']['overrides']), seconds=self.interval) if 'reminders' in ev and 'overrides' in ev['reminders'] else timedelta(minutes=bf)
            ) for ev, bf in events]

        now = datetime.now(timezone.utc)
        events = [e for e in sorted([(dt - bf, sm, lc, bf) for dt, sm, lc, bf in events]) if e[0] <= now]

        evt_count = len(events)
        if count != 0:
            events = events[:count]

        def shorten(summary):
            words = summary.split(' ')
            res = ''
            for w in words:
                if len(w) and w[0].isupper():
                    res += w[0:3]
            return res

        def truncate_long(pl, wd, seg):
            wd -= len(seg['contents'])
            nw_con = seg['contents'][0:max(len(seg['contents'])//2, -wd)].strip(' .,;(-')
            return nw_con + '…' if len(nw_con) < len(seg['contents']) else nw_con

        # check if these events are relevant
        if not short_mode:
            return [{
                'contents': (format if long_mode else short_format).format(summary=sm, location=lc,
                    error='', time='' if (dt + bf).strftime(time_format) in hide_times else
                    (dt + bf).strftime(time_format), short_summary=shorten(sm), count=evt_count),
                'highlight_groups': ['appoint:urgent', 'appoint'] if now < dt + bf else ['appoint'],
                'draw_inner_divider': True,
                'payload_name': channel_name,
                '_data': {'time': "" if (dt + bf).strftime(time_format) in hide_times
                    else (dt + bf).strftime(time_format), 'summary': sm,
                    'short_summary': shorten(sm), 'location': lc, 'count': evt_count},
                'truncate': (lambda a,b,seg: short_format.format(**seg['_data'])) if
                    not auto_shrink else truncate_long
            } for dt, sm, lc, bf in events if dt <= now] + segments
        elif evt_count:
            urgent = False
            for dt, sm, lc, bf in events:
                if now < dt + bf:
                    urgent = True
            return [{
                'contents': short_format.format(time='', summary='', short_summary='',
                    location='', count=evt_count, error=''),
                'highlight_groups': ['appoint:urgent', 'appoint'] if urgent else ['appoint'],
                'payload_name': channel_name
                }]

gcalendar = with_docstring(GoogleCalendarSegment(),
'''Return the next ``count`` appoints found in your Google Calendar.

:param string format:
    The format to use when displaying events. Valid fields are time, summary, short_summary,
    count, error, and location.
:param string short_format:
    The format to use when displaying events with few space. Valid fields are time, summary,
    short_summary, count, error, and location.
:param string time_format:
    The format to use when displaying times and dates.
:param int count:
    Number of appoints that shall be shown
:param bool show_count:
    Add an additional segment containing the number of events in the specified range.
:param list hide_times:
    Times (using time_format) not to be displayed as start times.
:param string credentials:
    A path to a file containing credentials to access the Google Calendar API.
:param string developer_key:
    Your Google dev key.
:param int range:
    Number of days into the future to check. No more than 250 events will be displayed in any case.
:param bool auto_shrink:
    Use ``short_format`` per default unless the ``appoints.gcalendar`` channel is full.
:param bool single_when_shrunk:
    Only show a single segment using ``short_format`` when this segment is in its short mode.


Highlight groups used: ``appoint``, ``appoint:urgent``, ``appoint:count``.
''')
