from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info

try:
    import dbus

    @requires_segment_info
    class BluetoothSegment(ThreadedSegment):
        interval = 300

        def set_state(self, **kwargs):
            super(BluetoothSegment, self).set_state(**kwargs)

        def update(self, *args, **kwargs):
            bus = dbus.SystemBus()
            bt = bus.get_object('org.bluez', '/')
            bti = dbus.Interface(bt, 'org.freedesktop.DBus.ObjectManager')
            obj = bti.GetManagedObjects()

            res = []
            for path, ifac in obj.items():
                if "org.bluez.Device1" in ifac:
                    props = obj[path]["org.bluez.Device1"]

                    btpt = bus.get_object('org.bluez', path)
                    btip = dbus.Interface(btpt, 'org.freedesktop.DBus.Properties')

                    try:
                        bat_per = btip.Get('org.bluez.Battery1', 'Percentage')
                    except dbus.DBusException:
                        bat_per = None
                    if bat_per != None:
                        bat_per = int(bat_per)

                    res += [{'name': str(props['Alias']), 'mac': str(props['Address']),
                            'connected': bool(props['Connected']), 'paired': bool(props['Paired']),
                            'battery': bat_per}]
            return res

        def render(self, bt_data, segment_info, format='BT {name}',
                short_format='BT{count_connected:2}', format_down=None, format_battery=None,
                ignore_unconnected=True, auto_shrink=False, **kwargs):
            channel_name = 'bluetooth'

            if auto_shrink and not ('payloads' in segment_info and channel_name in
                    segment_info['payloads'] and segment_info['payloads'][channel_name]):
                format = short_format

            if not bt_data:
                return None

            n_bt = []
            for b in bt_data:
                b = b.copy()
                if b['battery'] != None:
                    b['bat_or_empty'] = b['battery']
                else:
                    b['bat_or_empty'] = ''
                if format_battery:
                    b.update({'battery': format_battery.format(**b)})
                    if b['bat_or_empty'] != '':
                        b['bat_or_empty'] = b['battery']
                    else:
                        b['bat_or_empty'] = ''
                n_bt += [b]

            count_paired = len([b for b in bt_data if b['paired']])
            count_connected = len([b for b in bt_data if b['connected']])

            if '{name' in format or '{mac' in format:
                return [{'contents': format.format(**b),
                    'draw_inner_divider': True,
                    'highlight_groups': ['bluetooth'],
                    'click_values': b,
                    'payload_name': channel_name
                    } for b in n_bt if not ignore_unconnected or b['connected']]
            elif ('{count_connected' in format and count_connected) or \
                    ('{count_paired' in format and count_paired):
                return [{'contents': format.format(count_connected=count_connected,
                    count_paired=count_paired),
                    'highlight_groups': ['bluetooth'],
                    'click_values': {},
                    'payload_name': channel_name}]
            elif format_down:
                return [{'contents': format_down.format(count_connected=count_connected,
                    count_paired=count_paired),
                    'highlight_groups': ['bluetooth:down', 'bluetooth'],
                    'click_values': {},
                    'payload_name': channel_name}]

    bluetooth = with_docstring(BluetoothSegment(),
    ''' Return the connected Bluetooth devices. Requires ``dbus``.

        :param string format:
            Format
        :param string short_format:
            Short format
        :param string format_down:
            Format when no device is connected
        :param string format_battery:
            Format used to display the battery status of the connected device.
        :param boolean ignore_unconnected:
            When listing devices, ignore
        :param boolean auto_shrink:
            if set to true, this segment will use ``short_format`` per default,
            only using ``format`` when any message is present on the ``bluetooth`` message channel.

        Highlight groups used: ``bluetooth`` or ``bluetooth:down``

        Click values supplied: (any value available in format)
    ''')

except ImportError:
    def bluetooth(pl, format='BT {name}', short_format='BT{count_connected:2}', format_down=None,
            format_battery=None, ignore_unconnected=True, auto_shrink=False):
        ''' Return the connected Bluetooth devices. Requires ``dbus``.

            :param string format:
                Format
            :param string short_format:
                Short format
            :param string format_down:
                Format when no device is connected
            :param string format_battery:
                Format used to display the battery status of the connected device.
            :param boolean ignore_unconnected:
                When listing devices, ignore
            :param boolean auto_shrink:
                if set to true, this segment will use ``short_format`` per default,
                only using ``format`` when any message is present on the ``bluetooth`` message
                channel.

            Highlight groups used: ``bluetooth`` or ``bluetooth:down``

            Click values supplied: (any value available in format)
        '''

        pl.error('The bluetooth segment requires the python dbus package.')
        return None

