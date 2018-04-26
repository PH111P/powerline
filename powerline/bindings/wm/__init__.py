
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.bindings.wm.awesome import AwesomeThread


DEFAULT_UPDATE_INTERVAL = 2


conn = None

def get_i3_connection():
    '''Return a valid, cached i3 Connection instance
    '''
    global conn
    if not conn:
        import i3ipc
        conn = i3ipc.Connection()
    try:
        conn.get_tree()
    except BrokenPipeError:
        import i3ipc
        conn = i3ipc.Connection()
    return conn

def get_randr_outputs(d = None, window = None):
    '''Return all randr outputs as a list.

    Outputs are represented by a dictionary with at least the ``name``, ``width``,
    ``height``, ``primary``, ``x`` and ``y`` keys.
    '''

    from Xlib import X, display
    from Xlib.ext import randr

    d = d or display.Display()
    s = d.screen()
    if not window:
        window = s.root.create_window(0, 0, 1, 1, 1, s.root_depth)

    try:
        ress = randr.get_screen_resources(window)

        outputs = ress.outputs
        primary = randr.get_output_primary(window).output

        npos = 0
        modes = { }
        for mode in ress.modes:
            data = mode._data
            data['name'] = ress.mode_names[npos:npos + mode.name_length]
            npos += data['name_length']
            modes[data['id']] = data

        outputs = [(o, d.xrandr_get_output_info(o, 0)) for o in outputs]
        outputs = [{
        'name': o[1].name,
        'crtc_id': o[1].crtc,
        'crtc': d.xrandr_get_crtc_info(o[1].crtc, 0)if o[1].crtc else None,
        'primary': 'primary' if o[0] == primary else None,
        'connection': o[1].connection,
        'status': ['on', 'off'][o[1].crtc == 0],
        'modes': [modes[i] for i in o[1].modes if i in modes],
        'mode_ids': o[1].modes,
        'crtcs': o[1].crtcs,
        'mm_width': o[1].mm_width,
        'mm_height': o[1].mm_height,
        'id': o[0]
        } for o in outputs] # only return connectad outputs

        outputs = [{
        'name': o['name'],
        'primary': o['primary'],
        'crtc_id': o['crtc_id'],
        'x': o['crtc'].x if o['crtc'] else None,
        'y': o['crtc'].y if o['crtc'] else None,
        'height': o['crtc'].height if o['crtc'] else None,
        'width': o['crtc'].width if o['crtc'] else None,
        'crtc': o['crtc'],
        'status': o['status'],
        'connection': not o['connection'],
        'modes': o['modes'],
        'mode_ids': o['mode_ids'],
        'crtcs': o['crtcs'],
        'current_mode': o['crtc'].mode if o['crtc'] else None,
        'mm_width': o['mm_width'],
        'mm_height': o['mm_height'],
        'id': o['id']
        } for o in outputs]

        return outputs
    except RuntimeError:
        return None


def get_connected_randr_outputs(pl):
    '''Iterate over randr outputs. Yields all connected outputs that are not ``off``.
    If multiple outputs should be mirrored, only one of them wil be shown.

    Outputs are represented by a dictionary with at least the ``name``, ``width``,
    ``height``, ``primary``, ``x`` and ``y`` keys.
    '''
    outs = None
    while not outs:
        outs = get_randr_outputs()

    for i in range(0, len(outs)):
        o = outs[i]
        for j in range(0, i): # Being quadriatic is ok, as #outs < 5 in most cases
            if outs[j]['x'] == outs[i]['x'] and outs[j]['y'] == outs[i]['y'] and outs[j]['current_mode'] == outs[i]['current_mode']:
                o = None
                break
        if o and o['connection'] and o['status'] == 'on':
            yield o

wm_threads = {
    'awesome': AwesomeThread,
}
