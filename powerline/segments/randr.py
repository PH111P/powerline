from __future__ import (unicode_literals, division, absolute_import, print_function)
from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info
from os import path
from subprocess import check_call, check_output, run
from glob import glob

MODES = ['locked', 'auto']
@requires_segment_info
class ScreenRotationSegment(ThreadedSegment):

    interval = 1

    current_state = 0

    # output to manage
    initial_output = None
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

    def set_state(self, output, states=['normal', 'inverted', 'left', 'right'],
            gravity_triggers=None, mapped_inputs=[], touchpads=[], touchpad_states=None,
            rotation_hook=None, **kwargs):
        self.initial_output = output
        self.output = output
        self.touch_output = output

        self.rotation_hook = rotation_hook

        for basedir in glob('/sys/bus/iio/devices/iio:device*'):
            if 'accel' in open(path.join(basedir, 'name')).read():
                self.basedir = basedir
                break
        else:
            # No accels found, throw an error
            pass

        self.devices = check_output(['xinput', '--list', '--name-only']).splitlines()
        self.scale = float(open(path.join(self.basedir, 'in_accel_scale')).read())

        if gravity_triggers:
            self.triggers = gravity_triggers
        if touchpad_states:
            self.touchpad_states = touchpad_states

        self.mapped_inputs = mapped_inputs
        self.touchpads = touchpads

        self.current_state = 0
        self.STATES = states

        self.accel_x = open(path.join(basedir, 'in_accel_x_raw'))
        self.accel_y = open(path.join(basedir, 'in_accel_y_raw'))

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
        check_call(['xrandr', '--output', self.output, '--rotate', self.STATES[state]])

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

    def update_touchpad(self, state):
        needs_map = [i.decode('utf-8') for i in self.devices if len([j for j in self.touchpads
            if j in i.decode('utf-8')])]

        for dev in needs_map:
            check_call(['xinput', self.touchpad_state[self.STATES[state]], dev])

    def read_accel(self, f):
        f.seek(0)
        return float(f.read()) * self.scale

    def update(self, *args, **kwargs):
        if self.mode == 0:
            return -1

        x = self.read_accel(self.accel_x)
        y = self.read_accel(self.accel_y)

        for i in range(len(self.STATES)):
            if i == self.current_state:
                continue
            if self.checks[self.STATES[i]](x, y):
                self.rotate(i)
                self.current_state = i
                self.update_touchpad(self.current_state)


        return self.current_state

    def render(self, data, segment_info, show_on_all_outputs=True, name='rotation',
            format='{icon}', icons={'left':'l', 'right':'r', 'normal':'n', 'inverted':'i',
                'locked':'l', 'auto':'a'}, **kwargs):

        channel_name = 'randr.srot'
        channel_value = None
        if 'payloads' in segment_info and channel_name in segment_info['payloads']:
            channel_value = segment_info['payloads'][channel_name]

        if self.bar_needs_resize:
            scrn = self.bar_needs_resize
            self.bar_needs_resize = None
            if segment_info['output'] == scrn:
                segment_info['restart'](scrn)


        # A user wants to map devices to a different screen
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'capture_input' and 'output' in segment_info and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.touch_output = segment_info['output']
            self.rotate(self.current_state)
        # A user wants to rotate a different screen
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'capture' and 'output' in segment_info and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.output = segment_info['output']
            self.touch_output = segment_info['output']
            self.mode = 1
            self.rotate(self.current_state)
        # A user wants to toggle auto rotation
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'toggle_rot' and 'output' in segment_info and self.output == segment_info['output'] and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.mode = 1 - self.mode
            self.rotate(self.current_state)


        if 'output' in segment_info and segment_info['output'] != self.initial_output:
            self.mode = 0
            if not show_on_all_outputs:
                return None

        if name == 'rotation':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[self.STATES[self.current_state]]),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + self.STATES[data], 'srot:rotation', 'srot'],
                'click_values': {
                    'mode': MODES[self.mode],
                    'rotation': self.STATES[self.current_state],
                    'output': segment_info['output'],
                    'managed_output': self.output,
                    'touch_output': self.touch_output
                }
            }]

        if name == 'mode':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[MODES[self.mode]]),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + MODES[self.mode], 'srot:mode', 'srot'],
                'click_values': {
                    'mode': MODES[self.mode],
                    'rotation': self.STATES[self.current_state],
                    'output': segment_info['output'],
                    'managed_output': self.output,
                    'touch_output': self.touch_output
                }
            }]

        return None


srot = with_docstring(ScreenRotationSegment(),
''' Manage screen rotation and optionally display some information. Optionally disables
    Touchpads in rotated states.
    Requires ``xinput`` and ``xrandr`` and an accelerometer.

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
        ``mode`` (eiteher ``auto`` or ``locked``, depending on whether auto-rotation on the
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
    :param string list mapped_inputs:
        List of substrings of device names that should be mapped to the specified output.
        The entries in the specified list should be only substrings of devices listed as
        ``Virtual core pointer``, not of devices listed as ``Virtual core keyboard``.
    :param string list touchpads:
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

    Highlight groups used: ``srot:normal``, ``srot:inverted``, ``srot:right``, ``srot:left``,
    ``srot:rotation``, ``srot`` if the name parameter is ``rotation``, ``srot:auto``,
    ``srot:locked``, ``srot:mode``, ``srot`` if the name parameter is ``mode``.
    None if the name is set to something else.

    Click values supplied: ``mode`` (string), ``rotation`` (string), ``output`` (string,
    the output this regment is rendered to), ``managed_output`` (string, the screen
    currently managed), ``touch_output`` (string, the screen where touch inputs are mapped to).

    Interaction: This segment supports interaction via bar commands in the following way:

    +----------------------------------+---------------------------------------------------+
    | Bar command                      | Description                                       |
    +==================================+===================================================+
    | #bar;pass_oneshot:capture_input  | Map all specified input devices to the output     |
    |                                  | this command originates from. (experimental)      |
    +----------------------------------+---------------------------------------------------+
    | #bar;pass_oneshot:capture        | Rotate the screen where this command originates   |
    |                                  | from. (experimental)                              |
    +----------------------------------+---------------------------------------------------+
    | #bar;pass_oneshot:toggle_rot     | Toggle auto rotation if used on the screen        |
    |                                  | that is currently managed; otherwise ignored.     |
    +----------------------------------+---------------------------------------------------+
''')
