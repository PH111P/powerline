from __future__ import (unicode_literals, division, absolute_import, print_function)
from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info
from powerline.bindings.wm import get_randr_outputs
from os import path
from subprocess import check_call, check_output, run
from glob import glob
from threading import Lock

from Xlib import X, display
from Xlib.ext import randr

lock = Lock()

xlib_rots = {'normal': randr.Rotate_0, 'inverted': randr.Rotate_180,
        'left': randr.Rotate_90, 'right': randr.Rotate_270}
MODES = ['locked', 'auto']
@requires_segment_info
class ScreenRotationSegment(ThreadedSegment):

    interval = 1

    current_state = 0

    # output to manage
    output = None
    touch_output = None

    # Input devices to manage
    devices = None

    # Basedir for accelerometer
    basedir = None

    # Scale of the accelerometer
    scale = 1.0

    # Input devices to be mapped to the specified output
    mapped_inputs = []
    # Touchpads to be enabled/disabled
    touchpads = []

    STATES = []
    g = 8
    # Gravity triggers (rotation -> value)
    triggers = {'normal': -g, 'inverted': g, 'left': g, 'right': -g}
    checks = { }
    touchpad_state = {'normal': 'enable', 'inverted': 'disable',
            'left': 'disable', 'right': 'disable'}

    accel_x = None
    accel_y = None

    # Disable this segment if it runs in a bar on the wrong output
    mode = 1

    last_oneshot = 0
    bar_needs_resize = None

    rotation_hook = None
    hide_controls = { }

    d = None
    window = None

    def set_state(self, output, states=['normal', 'inverted', 'left', 'right'],
            gravity_triggers=None, mapped_inputs=[], touchpads=[], touchpad_states=None,
            rotation_hook=None, hide_controls=True, sensor_is_unsigned=False,
            sensor_max_value=None, **kwargs):
        self.output = output
        self.touch_output = output

        self.sensor_is_unsigned = sensor_is_unsigned
        self.sensor_max_value = sensor_max_value

        self.d = display.Display()
        s = self.d.screen()
        self.window = s.root.create_window(0, 0, 1, 1, 1, s.root_depth)

        self.rotation_hook = rotation_hook
        self.hide_controls = { 'default': hide_controls, output: hide_controls }

        for basedir in glob('/sys/bus/iio/devices/iio:device*'):
            with open(path.join(basedir, 'name')) as f:
                if 'accel' in f.read():
                    self.basedir = basedir
                    break
        else:
            # No accels found, throw an error
            pass

        self.devices = check_output(['xinput', '--list', '--name-only']).splitlines()
        with open(path.join(self.basedir, 'in_accel_scale')) as f:
            self.scale = float(f.read())

        if gravity_triggers:
            self.triggers = gravity_triggers
        if touchpad_states:
            self.touchpad_states = touchpad_states

        self.mapped_inputs = mapped_inputs
        self.touchpads = touchpads

        self.current_state = 0
        self.STATES = states


        self.checks = {
            'normal':   lambda x, y: y < self.triggers['normal'],
            'inverted': lambda x, y: y > self.triggers['inverted'],
            'left':     lambda x, y: x > self.triggers['left'],
            'right':    lambda x, y: x < self.triggers['right']
        }

        self.rotate(self.current_state)
        self.update_touchpad(self.current_state)
        super(ScreenRotationSegment, self).set_state(**kwargs)

    def rotate(self, state):
        outs = get_randr_outputs(self.d, self.window)
        if outs == None:
            return False
        outs = [o for o in outs if o['crtc']]
        op = [o for o in outs if o['name'] == self.output]
        if not len(op):
            # The output to be rotated doesn't exist :(
            return False
        op = op[0]

        # Get all outputs that are mirrored to the output we shall rotate
        # (We must also rotate these outputs)
        current_mode = op['current_mode']

        mirrored_outs = [o for o in outs if o['x'] == op['x'] and o['y'] == op['y'] and o['current_mode'] == op['current_mode']]

        if (self.STATES[self.current_state] in ['left', 'right']) != (self.STATES[state] in ['left', 'right']):

            # If the user has some non-mirrored setup, only normal and inverted
            # layouts are implemented for now.
            # Anything else requires work . . .

            if len(outs) != len(mirrored_outs):
                return False

            # Disable all screens to be rotated
            for o in mirrored_outs:
                randr.set_crtc_config(self.d, o['crtc_id'], 0, 0, 0, 0, 1, [])

            mx_x = 0
            mx_y = 0
            mx_mm_x = 0.0
            mx_mm_y = 0.0

            ratio = 1

            for o in outs:
                if o['width']:
                    mx_x = max(mx_x, o['x'] + o['width'])
                if o['height']:
                    mx_y = max(mx_y, o['y'] + o['height'])
                if o['width'] and o['height']:
                    ratio = max(ratio, max(o['width'] / o['height'], o['height'] / o['width'] ))
                if o in mirrored_outs and o['crtc'].rotation in [xlib_rots['left'],
                        xlib_rots['right']]:
                    if o['mm_width'] and o['width']:
                        mx_mm_x = max(mx_mm_x, o['width'] * 1.0 / o['mm_width'])
                    if o['mm_height'] and o['height']:
                        mx_mm_y = max(mx_mm_y, o['height'] * 1.0 / o['mm_height'])
                else:
                    if o['mm_width'] and o['height']:
                        mx_mm_y = max(mx_mm_y, o['height'] * 1.0 / o['mm_width'])
                    if o['mm_height'] and o['width']:
                        mx_mm_x = max(mx_mm_x, o['width'] * 1.0 / o['mm_height'])

            if mx_x and mx_y and mx_mm_x and mx_mm_y:
                self.window.xrandr_set_screen_size(mx_y, mx_x, int(mx_x / mx_mm_x * ratio),
                        int(mx_y / mx_mm_y * ratio))

        # Actually rotate these outputs, don't change anything besides the rotation
        for o in mirrored_outs:
            randr.set_crtc_config(self.d, o['crtc_id'], 0, o['x'], o['y'],
                    current_mode, xlib_rots[self.STATES[state]], [o['id']])

        if (self.STATES[self.current_state] in ['left', 'right']) != (self.STATES[state] in ['left', 'right']):
            self.bar_needs_resize = self.output
            if self.rotation_hook:
                run(self.rotation_hook, shell=True)

        needs_map = [i.decode('utf-8') for i in self.devices if len([j for j in self.mapped_inputs
            if j in i.decode('utf-8')])]

        ids = [check_output(['xinput', '--list', '--id-only', i]).splitlines()[0].decode()
                for i in needs_map]
        for i in ids:
            check_call(['xinput', '--map-to-output', i, self.touch_output])

        return True

    def update_touchpad(self, state):
        needs_map = [i.decode('utf-8') for i in self.devices if len([j for j in self.touchpads
            if j in i.decode('utf-8')])]

        for dev in needs_map:
            check_call(['xinput', self.touchpad_state[self.STATES[state]], dev])

    def read_accel(self, f):
        val = f.read()
        if not self.sensor_is_unsigned:
            return float(val) * self.scale
        else:
            if(int(val) <= self.sensor_max_value // 2):
                return float(val) * self.scale
            return float(int(val) - self.sensor_max_value) * self.scale


    def update(self, *args, **kwargs):
        if self.mode == 0:
            return -1

        self.accel_x = open(path.join(self.basedir, 'in_accel_x_raw'))
        self.accel_y = open(path.join(self.basedir, 'in_accel_y_raw'))
        x = self.read_accel(self.accel_x)
        y = self.read_accel(self.accel_y)
        self.accel_x.close()
        self.accel_y.close()

        self.devices = check_output(['xinput', '--list', '--name-only']).splitlines()

        for i in range(len(self.STATES)):
            if i == self.current_state:
                continue
            if self.checks[self.STATES[i]](x, y):
                global lock
                with lock:
                    if i == self.current_state:
                        continue
                    if self.rotate(i):
                        self.current_state = i
                        self.update_touchpad(self.current_state)

        return self.current_state

    def render(self, data, segment_info, show_on_all_outputs=True, name='rotation',
            format='{icon}', icons={'left':'l', 'right':'r', 'normal':'n', 'inverted':'i',
                'locked':'l', 'auto':'a'}, additional_controls=[], **kwargs):

        channel_name = 'randr.srot'
        channel_value = None
        if 'payloads' in segment_info and channel_name in segment_info['payloads']:
            channel_value = segment_info['payloads'][channel_name]

        current_output = segment_info['output'] if 'output' in segment_info else None

        if self.bar_needs_resize:
            scrn = self.bar_needs_resize
            self.bar_needs_resize = None
            segment_info['restart'](scrn)


        # A user wants to map devices to a different screen
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0].startswith('capture_input:') and current_output and channel_value[1] > self.last_oneshot:
            new_output = channel_value[0].split(':')[1]
            if current_output == new_output:
                self.last_oneshot = channel_value[1]
                self.touch_output = new_output
                self.rotate(self.current_state)
        # A user wants to rotate a different screen
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0].startswith('capture:') and current_output and channel_value[1] > self.last_oneshot:
            new_output = channel_value[0].split(':')[1]
            if current_output == new_output:
                self.last_oneshot = channel_value[1]
                self.output = new_output
                self.touch_output = new_output
                self.rotate(self.current_state)
        # A user wants to toggle auto rotation
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'toggle_rot' and current_output and self.output == current_output and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.mode = 1 - self.mode
            self.rotate(self.current_state)
        # A user wants to toggle visibility of controls
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0].startswith('toggle_controls') and current_output and channel_value[1] > self.last_oneshot:
            new_output = channel_value[0].split(':')[1]
            if current_output == new_output:
                self.last_oneshot = channel_value[1]
                if new_output in self.hide_controls:
                    self.hide_controls[new_output] = not self.hide_controls[new_output]
                else:
                    self.hide_controls[new_output] = not self.hide_controls['default']

        c_vals = {
                    'mode': MODES[self.mode],
                    'rotation': self.STATES[self.current_state],
                    'output': current_output,
                    'managed_output': self.output,
                    'touch_output': self.touch_output
                }

        if (current_output in self.hide_controls and not self.hide_controls[current_output]) or (not current_output in self.hide_controls and not self.hide_controls['default']):
            add_segments = [{
                    'contents': i[0].format(rotation=self.STATES[self.current_state],
                        mode=MODES[self.mode],
                        managed_output=self.output, touch_output=self.touch_output),
                    'payload_name': channel_name,
                    'highlight_groups': i[1] + ['srot'],
                    'click_values': c_vals,
                    'draw_inner_divider': True
                } for i in additional_controls]
        else:
            add_segments = []

        if current_output and current_output != self.output:
            if not show_on_all_outputs:
                return add_segments if len(add_segments) else None

        if name == 'rotation':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[self.STATES[self.current_state]],
                    managed_output=self.output, touch_output=self.touch_output),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + self.STATES[data], 'srot:rotation', 'srot'],
                'click_values': c_vals,
                'draw_inner_divider': True
            }] + add_segments

        if name == 'mode':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[MODES[self.mode]],
                    managed_output=self.output, touch_output=self.touch_output),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + MODES[self.mode], 'srot:mode', 'srot'],
                'click_values': c_vals,
                'draw_inner_divider': True
            }] + add_segments

        return add_segments if len(add_segments) else None


srot = with_docstring(ScreenRotationSegment(),
''' Manage screen rotation and optionally display some information. Optionally disables
    Touchpads in rotated states. (Note that rotating to the ``left`` and ``right``
    states does not currently work if there is another output connected whose
    displayed content is not mirrored to the screen to be rotated.)

    Requires ``xinput`` and ``python-xlib`` and an accelerometer.

    :param string output:
        The initial output to be rotated and to which touchscreen and stylus inputs are mapped.
        (Note that this can be changed at runtime via interaction with the segment.)
    :param bool show_on_all_outputs:
        If set to false, this segment is only visible on the specified output.
    :param string name:
        Possible values are ``rotation`` and ``mode``. This value is used to determine
        which highlight groups to use and how to populate the ``icon`` field in the
        format string in the returned segment.
        If set to any other value, this segment will produce no output.
    :param string format:
        Format string. Possible fields are ``rotation`` (the current rotation state of the screen),
        ``mode`` (either ``auto`` or ``locked``, depending on whether auto-rotation on the
        screen is enabled or not), and ``icon`` (an icon depicting either the rotation status
        or the auto-rotation status, depending on the segment's name).
    :param dict icons:
        Dictionary mapping rotation states (``normal``, ``inverted``, ``left``, ``right``)
        and auto-rotation states (``locked``, ``auto``) to strings to use to display them.
        Depending on the given name parameter, not all of these fields must be populated.
    :param string list states:
        Allowed rotation states. Possible entries are ``normal``, ``inverted``, ``left``, and
        ``right``. Per default, all of them are enabled.
    :param dict gravity_triggers:
        Sensor values that trigger rotation as a dictionary mapping rotation states
        (``normal``, ``inverted``, ``left``, ``right``) to numbers.
        Defaults to ``{'normal': -8, 'inverted': 8, 'left': 8, 'right': -8}``, meaning that
        a (scaled) reading of the ``in_accel_x_raw`` reading greater than 8 triggers a
        rotation to state ``left`` and a reading less than -8 triggers a rotation to state
        ``right``. Readings of ``in_accel_y_raw`` greater and less than 8 and -8 respectively
        will yield a rotation to the ``inverted`` and ``normal`` states respectively.
    :param string_list mapped_inputs:
        List of substrings of device names that should be mapped to the specified output.
        The entries in the specified list should be only substrings of devices listed as
        ``Virtual core pointer``, not of devices listed as ``Virtual core keyboard``.
    :param string_list touchpads:
        List of substrings of device names of touchpads to be managed.
        The entries in the specified list should be only substrings of devices listed as
        ``Virtual core pointer``, not of devices listed as ``Virtual core keyboard``.
    :param dict touchpad_states:
        Dictionary mapping a rotation state (``normal``, ``inverted``, ``left``, ``right``)
        to either ``enabled`` or ``disabled``, depending on whether the touchpads shall be
        enabled or disabled if the output is currently in the corresponding state.
    :param string rotation_hook:
        A string to be run by a shell after a rotation that changes the screen ratio
        (e.g. from ``normal`` to ``left``).
        It will be executed after the rotation takes place, but before the inputs are
        mapped to the output and before the bar resizes itself.
    :param (string,string_list)_list additional_controls:
        A list of (contents, highlight_groups) pairs. For each entry, an additional
        segment with the given contents and highlight groups is omitted. These segments
        obtain the same click values and may also be used to control the segment behavior.
        Also, all segments additionally use the ``srot`` highlight group and the contents
        may be a format string with all fields (except ``icon``) available.
    :param bool hide_controls:
        Hide the extra control segments. They may be shown via segment interaction.

    Highlight groups used: ``srot:normal`` or ``srot:inverted`` or ``srot:right`` or ``srot:left`` or ``srot:rotation`` or ``srot`` (if the name parameter is ``rotation``) or
    ``srot:auto`` or ``srot:locked`` or ``srot:mode`` or ``srot`` (if the name parameter
    is ``mode``) or None (if the name is set to something else).

    Click values supplied: ``mode`` (string), ``rotation`` (string), ``output`` (string,
    the output this segment is rendered to), ``managed_output`` (string, the screen
    currently managed), ``touch_output`` (string, the screen where touch inputs are mapped to).

    Interaction: This segment supports interaction via bar commands in the following way.
    (Note that parameters given to the bar may be combined with click values.)

    +------------------------------------------+---------------------------------------------+
    | Bar command                              | Description                                 |
    +==========================================+=============================================+
    | #bar;pass_oneshot:capture_input:<output> | Map all specified input devices to <output> |
    |                                          | (experimental)                              |
    +------------------------------------------+---------------------------------------------+
    | #bar;pass_oneshot:capture:<output>       | Rotate the screen <output> instead          |
    |                                          | (experimental)                              |
    +------------------------------------------+---------------------------------------------+
    | #bar;pass_oneshot:toggle_rot             | Toggle auto rotation if used on the screen  |
    |                                          | that is currently managed; otherwise        |
    |                                          | ignored.                                    |
    +------------------------------------------+---------------------------------------------+
    | #bar;pass_oneshot:toggle_controls:<outpt>| Toggles the visibility of additional        |
    |                                          | control segments on output <output>         |
    +------------------------------------------+---------------------------------------------+
''')

@requires_segment_info
class OutputSegment(ThreadedSegment):
    interval = 1

    d = None
    window = None
    outputs = {}

    segment_state = 0 # 0: minimal, 1: list outputs

    MIRROR_STATES = ['extend', 'mirror']
    mirror_state = 0 # 0: extend, 1: mirror

    last_oneshot = 0

    bar_needs_resize = None

    auto_update = False

    lock = Lock()

    redraw_hook = None

    def set_state(self, auto_update=False, redraw_hook=None, **kwargs):
        self.d = display.Display()
        s = self.d.screen()
        self.window = s.root.create_window(0, 0, 1, 1, 1, s.root_depth)

        outs = get_randr_outputs(self.d, self.window)
        if outs != None:
            self.outputs = [o for o in outs if o['connection']]

        prim = [o for o  in self.outputs if o['primary'] != None]
        if len(prim) > 0:
            prim = prim[0]
            onaji = [o for o in self.outputs if o['x'] == prim['x'] and o['y'] == prim['y']]
            if len(onaji) > 1:
                self.mirror_state = 1

        self.auto_update = auto_update

        self.redraw_hook = redraw_hook

        super(OutputSegment, self).set_state(**kwargs)

    def update(self, *args, **kwargs):
        od_out = self.outputs
        outs = get_randr_outputs(self.d, self.window)
        if outs == None:
            return None
        nw_out = [o for o in outs if o['connection']]

        old = [o['name'] for o in self.outputs]
        new = [o['name'] for o in nw_out]

        mg = [o for o in old if o in new]
        mg = [o for o in new if o in mg]

        change = not (len(mg) == len(old) and len(mg) == len(new))

        if change:
            if self.auto_update:
                for o in old:
                    if not o in mg:
                        self.disable_output([out for out in od_out if out['name'] == o][0])
                for o in new:
                    if not o in mg:
                        self.enable_output([out for out in nw_out if out['name'] == o][0])
            else:
                with self.lock:
                    self.outputs = nw_out
        return None

    def update_mirror_state(self):
        if self.mirror_state == 0:
            self.configure_extend()
        elif self.mirror_state == 1:
            self.configure_mirror()

    def resize_randr_screen(self):
        outs = [o for o in self.outputs if o['crtc']]

        for o in outs:
            randr.set_crtc_config(self.d, o['crtc_id'], 0, 0, 0, 0, 1, [])

        mx_x = 0
        mx_y = 0
        mx_mm_x = 0.0
        mx_mm_y = 0.0

        ratio =  1
        for o in outs:
            if o['width']:
                mx_x = max(mx_x, o['x'] + o['width'])
            if o['height']:
                mx_y = max(mx_y, o['y'] + o['height'])
            if o['width'] and o['height']:
                ratio = max(ratio, max(o['width'] / o['height'], o['height'] / o['width'] ))
            if not o['crtc'].rotation in [xlib_rots['left'], xlib_rots['right']]:
                if o['mm_width'] and o['width']:
                    mx_mm_x = max(mx_mm_x, o['width'] * 1.0 / o['mm_width'])
                if o['mm_height'] and o['height']:
                    mx_mm_y = max(mx_mm_y, o['height'] * 1.0 / o['mm_height'])
            else:
                if o['mm_width'] and o['height']:
                    mx_mm_y = max(mx_mm_y, o['height'] * 1.0 / o['mm_width'])
                if o['mm_height'] and o['width']:
                    mx_mm_x = max(mx_mm_x, o['width'] * 1.0 / o['mm_height'])

        if mx_x and mx_y and mx_mm_x and mx_mm_y:
            self.window.xrandr_set_screen_size(mx_x, mx_y, int(mx_x / mx_mm_x * ratio),
                    int(mx_y / mx_mm_y * ratio))

        for o in outs:
            randr.set_crtc_config(self.d, o['crtc_id'], 0, o['x'], o['y'],
                    o['current_mode'], o['crtc'].rotation, [o['id']])



    def configure_mirror(self, output=None):
        with self.lock:
            outs = get_randr_outputs(self.d, self.window)
            if outs == None:
                return False
            self.outputs = [o for o in outs if o['connection']]

        used_crtc = [o['crtc_id'] for o in self.outputs if o['crtc_id']]
        if output:
            free_crtc = [c for c in output['crtcs'] if c not in used_crtc]

            if len(free_crtc) < 1:
                # No crtc available, so we cannot enable this output
                return False

        # We need to find a mode that every connected output supports
        enabled_outputs = [o for o in self.outputs if o['crtc']]

        # print([o['name'] for o in enabled_outputs])

        if len(enabled_outputs) == 0:
            return False

        def resolutions(modes):
            return {(m['width'], m['height']) for m in modes}

        ress = {}
        mode_map = {}
        if output:
            # print(output['modes'])
            ress = resolutions(output['modes'])
            # print(ress)
            mode_map.update({output['name']: output['modes']})
        else:
            ress = resolutions(enabled_outputs[0]['modes'])

        # print(ress)

        for e in enabled_outputs:
            mode_map.update({e['name']: e['modes']})
            ress = [m for m in ress if m in resolutions(e['modes'])]
        if len(ress) > 0:
            # Outputs could agree on a resolution, so pick the largest one
            ress = sorted(ress, reverse=True)
            # print(ress)
            if output:
                mode_map.update({output['name']: \
                    [o for o in output['modes'] if (o['width'], o['height']) == ress[0]]})
            for e in enabled_outputs:
                mode_map.update({e['name']: \
                    [o for o in e['modes'] if (o['width'], o['height']) == ress[0]]})

        if output:
            randr.set_crtc_config(self.d, free_crtc[0],
                0, 0, 0, mode_map[output['name']][0]['id'], randr.Rotate_0, [output['id']])

        for o in enabled_outputs:
            randr.set_crtc_config(self.d, o['crtc_id'],
                0, 0, 0, mode_map[o['name']][0]['id'], o['crtc'].rotation, [o['id']])

        with self.lock:
            outs = get_randr_outputs(self.d, self.window)
            if outs == None:
                return False
            self.outputs = [o for o in outs if o['connection']]
        enabled_outputs = [o for o in self.outputs if o['crtc']]
        # Everything worked (hopefully), so redraw the bar
        self.bar_needs_resize = [o['name'] for o in enabled_outputs]
        self.resize_randr_screen()
        if self.redraw_hook:
            run(self.redraw_hook, shell=True)
        return True

    def configure_extend(self, output=None):
        with self.lock:
            outs = get_randr_outputs(self.d, self.window)
            if outs == None:
                return False
            self.outputs = [o for o in outs if o['connection']]
        used_crtc = [o['crtc_id'] for o in self.outputs if o['crtc_id']]
        if output:
            free_crtc = [c for c in output['crtcs'] if c not in used_crtc]

            if len(free_crtc) < 1:
                # No crtc available, so we cannot enable this output
                return False

        enabled_outputs = [o for o in self.outputs if o['crtc']]

        if len(enabled_outputs) == 0:
            return False

        wd = 0
        for o in enabled_outputs:
            randr.set_crtc_config(self.d, o['crtc_id'],
                0, wd, 0, o['mode_ids'][0], o['crtc'].rotation, [o['id']])
            wd += [m['width'] for m in o['modes'] if m['id'] == o['mode_ids'][0]][0]

        if output:
            randr.set_crtc_config(self.d, free_crtc[0],
                    0, wd, 0, output['mode_ids'][0], randr.Rotate_0, [output['id']])

        with self.lock:
            outs = get_randr_outputs(self.d, self.window)
            if outs == None:
                return False
            self.outputs = [o for o in outs if o['connection']]
        enabled_outputs = [o for o in self.outputs if o['crtc']]
        # Everything worked (hopefully), so redraw the bar
        self.bar_needs_resize = [o['name'] for o in enabled_outputs]
        self.resize_randr_screen()
        if self.redraw_hook:
            run(self.redraw_hook, shell=True)
        return True

    def enable_output(self, output):
        if self.mirror_state == 0:
            return self.configure_extend(output)
        elif self.mirror_state == 1:
            return self.configure_mirror(output)

        return False

    def disable_output(self, output):
        enabled_outputs = [o for o in self.outputs if o['crtc']]
        if len(enabled_outputs) <= 1 and output in enabled_outputs:
            # Yeah, I know most users are stupid, but at least don't let them disable all outputs
            return False

        # disable the output
        if output['crtc']:
            randr.set_crtc_config(self.d, output['crtc_id'], 0, 0, 0, 0, randr.Rotate_0, [])

        if self.mirror_state == 0:
            res = self.configure_extend(None)
            if res:
                if not self.bar_needs_resize:
                    self.bar_needs_resize = []
                self.bar_needs_resize += [output['name']]
            return res
        elif self.mirror_state == 1:
            res = self.configure_mirror(None)
            if res:
                if not self.bar_needs_resize:
                    self.bar_needs_resize = []
                self.bar_needs_resize += [output['name']]
            return res

        return False

    def render(self, data, segment_info, mirror_format='{mirror_icon}',
            mirror_icons={'mirror': 'M', 'extend': 'E'}, output_format='{output} {status_icon}',
            short_format='{mirror_icon} {output_count}', status_icons={'on': 'on', 'off': 'off'},
            hide_if_single_output=True, auto_shrink=True, **kwargs):
        channel_name = 'randr.output'

        channel_value = None
        if 'payloads' in segment_info and channel_name in segment_info['payloads']:
            channel_value = segment_info['payloads'][channel_name]

        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0].startswith('mode:') and channel_value[1] > self.last_oneshot:
            command = channel_value[0].split(':')[1]
            self.last_oneshot = channel_value[1]
            if command == 'toggle':
                self.mirror_state = (self.mirror_state + 1) % len(self.MIRROR_STATES)
            else:
                for i in self.MIRROR_STATES:
                    if i == command:
                        self.mirror_state = i
            self.update_mirror_state()

        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0].startswith('output:') and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            output = channel_value[0].split(':')[1]
            command = channel_value[0].split(':')[2]

            output = [o for o in self.outputs if o['name'] == output]
            if len(output) == 1:
                output = output[0]
                if command == 'on':
                    self.enable_output(output)
                if command == 'off':
                    self.disable_output(output)
                if command == 'toggle':
                    if output['crtc']:
                        self.disable_output(output)
                    else:
                        self.enable_output(output)

        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'ch_toggle' and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.segment_state = 1 - self.segment_state

        if self.bar_needs_resize:
            scrn = self.bar_needs_resize
            self.bar_needs_resize = None
            segment_info['restart'](scrn)


        if hide_if_single_output and len(self.outputs) < 2:
            return None

        if auto_shrink and self.segment_state == 0:
            return [{
                'contents': short_format.format(mirror_state=self.MIRROR_STATES[self.mirror_state],
                    mirror_icon=mirror_icons[self.MIRROR_STATES[self.mirror_state]],
                    output_count=len(self.outputs)),
                'highlight_groups': ['output:short',
                    'output:' + self.MIRROR_STATES[self.mirror_state], 'output'],
                'draw_inner_divider': True,
                'payload_name': channel_name,
                'click_values': {'mirror_state': self.MIRROR_STATES[self.mirror_state]}
            }]

        result = []

        result += [{
            'contents': mirror_format.format(mirror_state=self.MIRROR_STATES[self.mirror_state],
                mirror_icon=mirror_icons[self.MIRROR_STATES[self.mirror_state]]),
            'highlight_groups': ['output:' + self.MIRROR_STATES[self.mirror_state],
                'output:mirror_state', 'output'],
            'draw_inner_divider': True,
            'payload_name': channel_name,
            'click_values': {'mirror_state': self.MIRROR_STATES[self.mirror_state]}
        }]

        result += [{
            'contents': output_format.format(output=o['name'],
                status_icon=status_icons[o['status']]),
            'highlight_groups': ['output:' + o['status'], 'output:status', 'output'],
            'draw_inner_divider': True,
            'payload_name': channel_name,
            'click_values': {'output_name': o['name'], 'output_status': o['status']}
        } for o in sorted(self.outputs, key=lambda o: -1.0/o['x'] if o['x'] else 0, reverse=True)]

        return result

    # [ ][ ] / [=] / ... > eDPI (--o) > HDMI1 (o--) >
    # extend/mirror/ ... > only show connected outputs, use different colors for enabled/ disabled
    # Click on [ ][ ] / [=] cycles through modes
    # Click on outputs toggles them on / off acc to mode;
    # In extend mode: sort outputs according to their relative position

output = with_docstring(OutputSegment(),
'''Manage connected outputs, optionally detect newly (dis-)connected outputs automatically.

    Requires ``python-xlib``.

    :param string mirror_format:
        Format used to display the mirror mode (extend/mirror) part of the segment.
        Valid fields are ``mirror_state`` and ``mirror_icon``.
    :param dict mirror_icons:
        Icons used in the ``mirror_icon`` field of ``mirror_format``.
        Needs the entries ``extend`` and ``mirror``.
    :param string output_format:
        Format used to display outputs and information about their status.
        Valid fields are ``output`` and ``status_icon``.
    :param dict status_icons:
        Icons used in the ``status_icon`` field of ``output_format``.
        Needs the entries ``off`` and ``on``.
    :param bool hide_if_single_output:
        Hide the segment if only a single output is connected. (Enabling this will still show
        the segment if there is more than one output connected, of whom only one is not turned
        ``off``.)
    :param bool auto_update:
        If set to true, this segment will automatically enable newly connected outputs
        or disable newly disconnected outputs according to the current mode.
        Also restarts bars appropriately.


    Highlight groups used: ``output:mirror`` or ``output:extend`` or ``output:mirror_state`` or ``output`` (for the mirror mode part) and ``output:off`` or ``output:on`` or ``output:status`` or ``output`` (for the outputs).

    Click values supplied: ``mirror_state`` (string) for the mirror mode part and
    ``output_name`` (string), ``output_status`` (string) in the remaining part.

    Interaction: This segment supports interaction via bar commands in the following way.
    (Note that parameters given to the bar may be combined with click values.)

    +---------------------------------------------------+------------------------------------+
    | Bar command                                       | Description                        |
    +===================================================+====================================+
    | #bar;pass_oneshot:mode:<mode/toggle>              | Set the mirror mode to <mode> or   |
    |                                                   | <toggle> it.                       |
    +---------------------------------------------------+------------------------------------+
    | #bar;pass_oneshot:output:<output>:<on/off/toggle> | Turn output <output> <on/off> or   |
    |                                                   | <toggle> its status. Restarts bars.|
    +---------------------------------------------------+------------------------------------+

''')
