
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info


@requires_segment_info
def prompt_count(pl, segment_info):
    return str(segment_info['ipython'].prompt_count)


@requires_segment_info
def vi_mode(pl, segment_info):
    ipython = segment_info['ipython']._shell
    if (getattr(ipython.pt_app, 'editing_mode', None) == 'VI'
            and ipython.prompt_includes_vi_mode):
        return str(ipython.pt_app.app.vi_state.input_mode)[3:6]
    else:
        return None
