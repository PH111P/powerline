import os
import sys
import re

from powerline.lib.shell import run_cmd

# XXX Warning: module name must not be equal to the segment name as long as this
# segment is imported into powerline.segments.common module.

show_original=False
capacity_full_design=-1
base_dir = '/sys/class/power_supply'

def _file_exists(path, arg):
    return os.path.exists(path.format(arg))

def _get_batteries(file_names):
    import functools
    batteries = []
    for linux_bat in os.listdir('/sys/class/power_supply'):
        if linux_bat.startswith('BAT'):
            pos = [functools.reduce(lambda x, y: x and y, a, True) for a in
                    [[_file_exists(base_dir + '/{0}/' + b, linux_bat) for b in file_names[i]]
                    for i in range(0, len(file_names))]]
            for i in range(0, len(pos)):
                if pos[i]:
                    batteries += [(linux_bat, i)]
                    break
    return batteries

def _get_paths(file_names, batteries, battery):
    return [(base_dir + '/BAT' + str(battery) + '/' + fn)
            for fn in file_names[
                [bat[1] for bat in batteries
                    if bat[0] == ('BAT' + str(battery))][0]]]

def _read(file_names):
    res = []
    for p in file_names:
        with open(p, 'r') as f:
            res += [f.readline().split()[0]]
    return res

def _get_battery(pl):
    if os.path.isdir(base_dir):
        file_names = [['charge_now', 'charge_full', 'charge_full_design'],
                ['energy_now', 'energy_full', 'energy_full_design']]
        batteries = _get_batteries(file_names)

        def _get_capacity(pl, battery):
            current = 0
            full = 1

            paths = _get_paths(file_names, batteries, battery)
            vals = _read(paths)

            current = int(float(vals[0]))
            if not show_original:
                full = int(float(vals[1]))
            elif capacity_full_design == -1:
                full = int(float(vals[2]))
            else:
                full = capacity_full_design
            return (current * 100/full)

        return _get_capacity
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_battery_status(pl):
    if os.path.isdir(base_dir):
        status_paths = [['status']]
        batteries = _get_batteries(status_paths)

        def _get_status(pl, battery):
            path = _get_paths(status_paths, batteries, battery)
            stat = _read(path)[0]
            return stat
        return _get_status
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_battery_rem_time(pl, battery):
    if os.path.isdir(base_dir):
        rem_time_paths = [['energy_now', 'energy_full', 'power_now', 'status'],
                ['charge_now', 'charge_full', 'current_now', 'status']]
        batteries = _get_batteries(rem_time_paths)

        def _get_rem_time(pl, battery):
            paths = _get_paths(rem_time_paths, batteries, battery)
            vals = _read(paths)
            if vals[2] == '0' or vals[3] == 'Unknown':
                return 0

            curr = int(float(vals[2]))
            charge = int(vals[0])
            full = int(vals[1])
            if vals[3] == 'Charging':
                return (full - charge) / curr
            elif vals[3] == 'Discharging':
                return charge / curr
            else:
                return 0
        return _get_rem_time
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_capacity(pl, battery):
    global _get_capacity

    def _failing_get_capacity(pl, battery):
        raise NotImplementedError

    try:
        _get_capacity = _get_battery(pl)
    except NotImplementedError:
        _get_capacity = _failing_get_capacity
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_capacity = _failing_get_capacity
    return _get_capacity(pl, battery)

def _get_status(pl, battery):
    global _get_status

    def _failing_get_status(pl, battery):
        raise NotImplementedError

    try:
        _get_status = _get_battery_status(pl)
    except NotImplementedError:
        _get_status = _failing_get_status
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_status = _failing_get_status
    return _get_status(pl, battery)

def _get_rem_time(pl, battery):
    global _get_rem_time

    def _failing_get_rem_time(pl, battery):
        raise NotImplementedError

    try:
        _get_rem_time = _get_battery_rem_time(pl, battery)
    except NotImplementedError:
        _get_rem_time = _failing_get_rem_time
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_rem_time = _failing_get_rem_time
    return _get_rem_time(pl, battery)

def battery(pl, name='capacity', icons={'online':'CHR', 'offline':'BAT', 'full':''}, format='{capacity:3.0%}',
        rem_time_format='%H:%M', gamify_steps=5, bat=0, original_health=False, full_design=-1):
    '''Return batteries' charge status.

        :param str name:
                Determines the information displayed. Valid values:

                ========  ========================================================================
                Name      Description
                ========  ========================================================================
                capacity  The remaining capacity of the battery as a float btw 0 and 1.
                gamify    Rem. cap. encoded in a string of gamify_steps chars from icons.
                status    Current adapter status (Charging, Discharging or Full).
                icon      Icon depicting current battery status/capacity.
                rem_time  Remaining time till the battery is full or empty.
                ========  ========================================================================
        :param dict icons:
                Icons used to display the adapter status. Possible entries are ``online``,
                ``offline`` and ``full`` for statuses, ``0``, ``25``, ``50``, ``75`` and ``100``
                for use with gamify. If ``online``, ``offline`` or ``full`` are absent, icon will
                try to use appropriate icons from gamify.
        :param string format:
                Format used to display the capacity.
        :param string rem_time_format:
                Format used to display the remaining time (as a strftime format string)
        :param int gamify_steps:
                Number of discrete steps to show between 0% and 100% capacity if gamify
                occurs in format. The single one step that is neither completely full
                nor completely empty will use the icon corresponding to the percentage
                that part is empty.
        :param int bat:
                Specifies the battery to display information for.
        :param bool original_health:
                Use the original battery health as base value. (Experimental)
        :param int full_design:
                Specifies the design capacity of the battery. You will need this only if this value
                happens to read wrong. (Experimental)

        ``battery_gradient`` and ``battery`` groups are used in any case, first is
        preferred.

        Highlight groups used: ``battery`` or ``battery_gradient`` (gradient) or ``battery:100`` or
        ``battery:50`` or ``battery:0`` or ``battery:full`` or ``battery:online``
        or ``battery:offline``.

        Click values supplied: ``capacity`` (int), ``rem_time`` (string), ``status`` (string).
        '''
    capacity = 0
    try:
        global show_original
        global capacity_full_design
        show_original = original_health
        capacity_full_design = full_design
        capacity = min(100, _get_capacity(pl, bat))
    except NotImplementedError:
        pl.info('Unable to get battery capacity.')
        capacity = None

    status = None
    try:
        status = _get_status(pl, bat)
    except NotImplementedError:
        pl.info('Unable to get battery status.')
        status = None

    rem_time = 0
    try:
        rem_time = _get_rem_time(pl, bat)
    except NotImplementedError:
        pl.info('Unable to get remaining time.')
        rem_time = None
    except OSError:
        pl.info('Your BIOS is screwed.')
        rem_time = None

    if rem_time:
        from datetime import time
        rem_sec = int(rem_time * 3600)
        rem_hours = int(rem_sec / 3600)
        rem_sec -= rem_hours * 3600
        rem_minutes = int(rem_sec / 60)
        rem_sec -= rem_minutes * 60
        rem_time = time(hour=rem_hours, minute=rem_minutes, second=rem_sec).strftime(rem_time_format)
    else:
        rem_time = None

    click_values = {'status': status, 'rem_time': rem_time, 'capacity': capacity}

    def get_icon(percentage):
        for p in range(100, -1, -1):
            if percentage >= p and str(p) in icons:
                return icons[str(p)]
        return ''
    def get_status_icon(status):
        if status in icons:
            return icons[status]
        else:
            return get_icon(capacity)
    def translate_status(status):
        return {'Charging':'online', 'Discharging':'offline', 'Full':'full'}.get(status, 'unknown')

    if name == 'gamify':
        segment_size = 100 // gamify_steps
        full = int(capacity + .5) // segment_size
        half = (int(capacity) % segment_size) * 100 // segment_size
        empty = gamify_steps - full - 1

        ret = []
        ret.append({
            'contents': get_icon(100) * full,
            'draw_inner_divider': False,
            'highlight_groups': ['battery:100', 'battery_gradient', 'battery'],
            # Using zero as “nothing to worry about”: it is least alert color.
            'gradient_level': 0,
            'click_values': click_values
            })
        ret.append({
            'contents': get_icon(half),
            'draw_inner_divider': False,
            'highlight_groups': ['battery_gamify_gradient', 'battery_gradient', 'battery'],
            'gradient_level': segment_size - half,
            'click_values': click_values
            })
        ret.append({
            'contents': get_icon(0) * empty,
            'highlight_groups': ['battery:0', 'battery_gradient', 'battery'],
            # Using a hundred as it is most alert color.
            'gradient_level': 100,
            'click_values': click_values
            })
        return ret
    elif name == 'icon':
        return [{
            'contents': get_status_icon(translate_status(status)),
            'highlight_groups': ['battery:' + translate_status(status), 'battery_gradient', 'battery'],
            'gradient_level': 100 - capacity,
            'click_values': click_values
            }]
    elif name == 'status':
        if not status:
            return None
        return [{
            'contents': status,
            'highlight_groups': ['battery:' + translate_status(status), 'battery_gradient', 'battery'],
            'gradient_level': 100 - capacity,
            'click_values': click_values
            }]
    elif name == 'capacity':
        return [{
            'contents': format.format(capacity=capacity / 100.0, status=status, rem_time=rem_time),
            'highlight_groups': ['battery_gradient', 'battery'],
            # Gradients are “least alert – most alert” by default, capacity has
            # the opposite semantics.
            'gradient_level': 100 - capacity,
            'click_values': click_values
            }]
    elif name == 'rem_time':
        if not rem_time:
            return None
        return [{
            'contents': rem_time,
            'highlight_groups': ['battery_gradient', 'battery'],
            # Gradients are “least alert – most alert” by default, capacity has
            # the opposite semantics.
            'gradient_level': 100 - capacity,
            'click_values': click_values
            }]
    else:
        return None
