
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info

vim_modes = {
    'vi-navigation': 'NORMAL',
    'vi-insert': 'INSERT',
    'vi-insert-multiple': 'INSMUL',
    'vi-replace': 'RPLACE'
}



@requires_segment_info
def prompt_count(pl, segment_info):
    return str(segment_info['ipython'].prompt_count)


@requires_segment_info
def vi_mode(pl, segment_info, override=None):
    '''Return the current vim mode.

    :param dict override:
        dict for overriding default mode strings, e.g. ``{ 'vi-navigation': 'NORM' }``
    '''

    if not 'mode' in segment_info:
        return None
    mode = segment_info['mode']
    if mode == None:
        return None
    if not override:
        return vim_modes[mode]
    try:
        return override[mode]
    except KeyError:
        return vim_modes[mode]
    return 'SQUID '
