
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os
import socket

from powerline.lib.url import urllib_read
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from powerline.lib.monotonic import monotonic
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info


@requires_segment_info
def hostname(pl, segment_info, only_if_ssh=False, exclude_domain=False):
    '''Returns the current hostname.

    :param bool only_if_ssh:
        only return the hostname if currently in an SSH session
    :param bool exclude_domain:
        return the hostname without domain if there is one

    No special highlight groups used.
    '''

    if only_if_ssh and not segment_info['environ'].get('SSH_CLIENT'):
        return None
    if exclude_domain:
        return socket.gethostname().split('.')[0]
    return socket.gethostname()

@requires_segment_info
def wireless(pl, segment_info, device=None, format='{quality:3.0%} at {essid}',
    short_format='{quality:3.0%}', format_down=None, auto_shrink=False):
    '''Returns the current connection quality.

    :param string device:
        the device to use. Per default this segment will try to be smart.
    :param string format:
        the output format
    :param string short_format:
        optional shorter format when the powerline needs to shrink segments
    :param string format_down:
        if set to any other value than ``None``, it will be shown when no wireless connection is
        present.
    :param bool auto_shrink:
        if set to true, this segment will use ``short_format`` per default,
        only using ``format`` when any message is present on the ``net.wireless``
        message channel.

    Highlight groups used: ``wireless:quality`` (gradient) or ``wireless:down`` (when no connection is present)

    Click values supplied: ``quality`` (int), ``essid`` (string)
    '''
    payload_name = 'net.wireless'

    if not device:
        for interface in os.listdir('/sys/class/net'):
            if interface.startswith('wl'):
                device = interface
                break

    try:
        import iwlib
    except ImportError:
        pl.info("Couldn't load iwlib")
        return None if not format_down else [{
            'contents': format_down.format(quality=0, essid=None, frequency=0),
            'highlight_groups': ['wireless:down', 'wireless:quality', 'quality_gradient'],
            'gradient_level': 100,
            'payload_name': payload_name
        }]

    stats = iwlib.get_iwconfig(device)
    essid = ''
    quality = 0
    frequency = 0
    if 'ESSID' in stats:
        essid = stats['ESSID']
        if 'stats' in stats and 'quality' in stats['stats']:
            quality = stats['stats']['quality']
        if 'Frequency' in stats:
            frequency = stats['Frequency']

    if essid == '' or quality == 0:
        return None if not format_down else [{
            'contents': format_down.format(quality=0, essid=None, frequency=0),
            'highlight_groups': ['wireless:down', 'wireless:quality', 'quality_gradient'],
            'gradient_level': 100,
            'payload_name': payload_name
        }]

    if not auto_shrink or ('payloads' in segment_info and payload_name in
        segment_info['payloads'] and segment_info['payloads'][payload_name]):
            return [{
                'contents': format.format(quality=quality/85,
                essid=essid.decode(), frequency=frequency),
                'highlight_groups': ['wireless:quality', 'quality_gradient'],
                'gradient_level': 100 * (85 - quality) / 85,
                'click_values': {'essid': essid, 'quality': quality * 100 / 85},
                'payload_name': payload_name
                }]
    return [{
        'contents': short_format.format(quality=quality/85, essid=essid.decode(), frequency=frequency),
        'highlight_groups': ['wireless:quality', 'quality_gradient'],
        'gradient_level': 100 * (85 - quality) / 85,
        'click_values': {'essid': essid, 'quality': quality * 100 / 85},
        'payload_name': payload_name,
        'truncate': lambda a,b,c: short_format.format(quality=quality/85, essid=essid.decode(), frequency=frequency)
        }]


def _external_ip(query_url='http://ipv6.icanhazip.com/'):
    return urllib_read(query_url).strip()


class ExternalIpSegment(ThreadedSegment):
    interval = 300

    def set_state(self, query_url='http://ipv4.icanhazip.com/', **kwargs):
        self.query_url = query_url
        super(ExternalIpSegment, self).set_state(**kwargs)

    def update(self, old_ip):
        return _external_ip(query_url=self.query_url)

    def render(self, ip, **kwargs):
        if not ip:
            return None
        return [{'contents': ip, 'divider_highlight_group': 'background:divider',
            'click_values': {'external_ip': ip}}]


external_ip = with_docstring(ExternalIpSegment(),
'''Return external IP address.

:param str query_url:
    URI to query for IP address, should return only the IP address as a text string

    Suggested URIs:

    * http://ipv4.icanhazip.com/
    * http://ipv6.icanhazip.com/
    * http://icanhazip.com/ (returns IPv6 address if available, else IPv4)

Divider highlight group used: ``background:divider``.

Click values supplied: ``external_ip`` (string)
''')


try:
    import netifaces
except ImportError:
    def internal_ip(pl, interface='auto', ipv=4):
        return None
else:
    _interface_starts = {
        'eth':      10,  # Regular ethernet adapters         : eth1
        'enp':      10,  # Regular ethernet adapters, Gentoo : enp2s0
        'en':       10,  # OS X                              : en0
        'ath':       9,  # Atheros WiFi adapters             : ath0
        'wlan':      9,  # Other WiFi adapters               : wlan1
        'wlp':       9,  # Other WiFi adapters, Gentoo       : wlp5s0
        'teredo':    1,  # miredo interface                  : teredo
        'lo':      -10,  # Loopback interface                : lo
        'docker':   -5,  # Docker bridge interface           : docker0
        'vmnet':    -5,  # VMWare bridge interface           : vmnet1
        'vboxnet':  -5,  # VirtualBox bridge interface       : vboxnet0
    }

    _interface_start_re = re.compile(r'^([a-z]+?)(\d|$)')

    def _interface_key(interface):
        match = _interface_start_re.match(interface)
        if match:
            try:
                base = _interface_starts[match.group(1)] * 100
            except KeyError:
                base = 500
            if match.group(2):
                return base - int(match.group(2))
            else:
                return base
        else:
            return 0

    def internal_ip(pl, format="{addr}", interface='auto', ipv=4):
        family = netifaces.AF_INET6 if ipv == 6 else netifaces.AF_INET
        if interface == 'auto':
            try:
                interface = next(iter(sorted(netifaces.interfaces(), key=_interface_key, reverse=True)))
            except StopIteration:
                pl.info('No network interfaces found')
                return None
        elif interface == 'default_gateway':
            try:
                interface = netifaces.gateways()['default'][family][1]
            except KeyError:
                pl.info('No default gateway found for IPv{0}', ipv)
                return None
        addrs = netifaces.ifaddresses(interface)
        try:
            addr = addrs[family][0]['addr']
            netmask = addrs[family][0]['netmask'] if "netmask" in addrs[family][0] else None
            if ipv == 6 and netmask is not None:
                # netifaces reports IPv6 subnet mask with suffix (e.g. /64)
                cidr = netmask.split("/")[1]
            elif netmask is not None:
                # Turn subnet mask into a bitmask, then count the ones
                bitmask = "".join("{0:08b}".format(int(number)) for number in netmask.split("."))
                cidr = bitmask.count("1")
            else:
                cidr = 0
            return format.format(addr=addr, netmask=netmask, cidr=cidr)
        except (KeyError, IndexError):
            pl.info("No IPv{0} address found for interface {1}", ipv, interface)
            return None


internal_ip = with_docstring(internal_ip,
'''Return internal IP address

Requires ``netifaces`` module to work properly.

:param str interface:
    Interface on which IP will be checked. Use ``auto`` to automatically
    detect interface. In this case interfaces with lower numbers will be
    preferred over interfaces with similar names. Order of preference based on
    names:

    #. ``eth`` and ``enp`` followed by number or the end of string.
    #. ``ath``, ``wlan`` and ``wlp`` followed by number or the end of string.
    #. ``teredo`` followed by number or the end of string.
    #. Any other interface that is not ``lo*``.
    #. ``lo`` followed by number or the end of string.

    Use ``default_gateway`` to detect the interface based on the machine's
    `default gateway <https://en.wikipedia.org/wiki/Default_gateway>`_ (i.e.,
    the router to which it is connected).

:param string format:
    Format string. Use ``addr`` to show the address, ``netmask`` to show the
    subnet mask, and ``cidr`` to show the subnet in CIDR notation
:param int ipv:
    4 or 6 for ipv4 and ipv6 respectively, depending on which IP address you
    need exactly.
''')


try:
    import psutil

    def _get_bytes(interface):
        try:
            io_counters = psutil.net_io_counters(pernic=True)
        except AttributeError:
            io_counters = psutil.network_io_counters(pernic=True)
        if_io = io_counters.get(interface)
        if not if_io:
            return None
        return if_io.bytes_recv, if_io.bytes_sent

    def _get_interfaces():
        try:
            io_counters = psutil.net_io_counters(pernic=True)
        except AttributeError:
            io_counters = psutil.network_io_counters(pernic=True)
        for interface, data in io_counters.items():
            if data:
                yield interface, data.bytes_recv, data.bytes_sent
except ImportError:
    def _get_bytes(interface):
        with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
            rx = int(file_obj.read())
        with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
            tx = int(file_obj.read())
        return (rx, tx)

    def _get_interfaces():
        for interface in os.listdir('/sys/class/net'):
            x = _get_bytes(interface)
            if x is not None:
                yield interface, x[0], x[1]


class NetworkLoadSegment(KwThreadedSegment):
    interfaces = {}
    replace_num_pat = re.compile(r'[a-zA-Z]+')

    @staticmethod
    def key(interface='auto', **kwargs):
        return interface

    def compute_state(self, interface):
        if interface == 'auto':
            proc_exists = getattr(self, 'proc_exists', None)
            if proc_exists is None:
                proc_exists = self.proc_exists = os.path.exists('/proc/net/route')
            if proc_exists:
                # Look for default interface in routing table
                with open('/proc/net/route', 'rb') as f:
                    for line in f.readlines():
                        parts = line.split()
                        if len(parts) > 1:
                            iface, destination = parts[:2]
                            if not destination.replace(b'0', b''):
                                interface = iface.decode('utf-8')
                                break
            if interface == 'auto':
                # Choose interface with most total activity, excluding some
                # well known interface names
                interface, total = 'eth0', -1
                for name, rx, tx in _get_interfaces():
                    base = self.replace_num_pat.match(name)
                    if None in (base, rx, tx) or base.group() in ('lo', 'vmnet', 'sit'):
                        continue
                    activity = rx + tx
                    if activity > total:
                        total = activity
                        interface = name

        try:
            idata = self.interfaces[interface]
            try:
                idata['prev'] = idata['last']
            except KeyError:
                pass
        except KeyError:
            idata = {}
            if self.run_once:
                idata['prev'] = (monotonic(), _get_bytes(interface))
                self.shutdown_event.wait(self.interval)
            self.interfaces[interface] = idata

        idata['last'] = (monotonic(), _get_bytes(interface))
        return idata.copy()

    def render_one(self, idata, recv_format='DL {value:>8}', sent_format='UL {value:>8}', suffix='B/s', si_prefix=False, **kwargs):
        if not idata or 'prev' not in idata:
            return None

        t1, b1 = idata['prev']
        t2, b2 = idata['last']
        measure_interval = t2 - t1

        if None in (b1, b2):
            return None

        r = []
        for i, key in zip((0, 1), ('recv', 'sent')):
            format = locals()[key + '_format']
            try:
                value = (b2[i] - b1[i]) / measure_interval
            except ZeroDivisionError:
                self.warn('Measure interval zero.')
                value = 0
            max_key = key + '_max'
            is_gradient = max_key in kwargs
            hl_groups = ['network_load_' + key, 'network_load']
            if is_gradient:
                hl_groups[:0] = (group + '_gradient' for group in hl_groups)
            r.append({
                'contents': format.format(value=humanize_bytes(value, suffix, si_prefix)),
                'divider_highlight_group': 'network_load:divider',
                'highlight_groups': hl_groups
            })
            if is_gradient:
                max = kwargs[max_key]
                if value >= max:
                    r[-1]['gradient_level'] = 100
                else:
                    r[-1]['gradient_level'] = value * 100.0 / max

        return r


network_load = with_docstring(NetworkLoadSegment(),
'''Return the network load.

Uses the ``psutil`` module if available for multi-platform compatibility,
falls back to reading
:file:`/sys/class/net/{interface}/statistics/{rx,tx}_bytes`.

:param str interface:
    Network interface to measure (use the special value "auto" to have powerline
    try to auto-detect the network interface).
:param str suffix:
    String appended to each load string.
:param bool si_prefix:
    Use SI prefix, e.g. MB instead of MiB.
:param str recv_format:
    Format string that determines how download speed should look like. Receives
    ``value`` as argument.
:param str sent_format:
    Format string that determines how upload speed should look like. Receives
    ``value`` as argument.
:param float recv_max:
    Maximum number of received bytes per second. Is only used to compute
    gradient level.
:param float sent_max:
    Maximum number of sent bytes per second. Is only used to compute gradient
    level.

Divider highlight group used: ``network_load:divider``.

Highlight groups used: ``network_load_sent_gradient`` (gradient) or ``network_load_recv_gradient`` (gradient) or ``network_load_gradient`` (gradient), ``network_load_sent`` or ``network_load_recv`` or ``network_load``.
''')
