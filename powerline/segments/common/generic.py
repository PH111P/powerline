
from __future__ import (unicode_literals, division, absolute_import, print_function)

import subprocess
from powerline.theme import requires_segment_info

def generic_shell(pl, command, highlight_groups=["generic_shell"]):
    '''Execute the given command in a shell and return its result

    :param string command:
        The command to execute.
    :param string_list highlight_groups:
        The highlight groups to use.

    Click values supplied: ``contents`` (string)
    '''

    shell = subprocess.Popen(['/bin/sh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    shell.stdin.write((command + '\n').encode('utf-8'));
    shell.stdin.flush();
    shell.stdin.close();

    contents = shell.stdout.read().decode().strip('\n ')

    return [{
        'contents': contents,
        'click_values': {'contents': contents},
        'highlight_groups': highlight_groups
    }]


@requires_segment_info
def generic_growable(pl, segment_info, channel_name, segments_short, segments_long):
    '''Returns the segments in ``segments_short`` if the channel ``channel_name`` is
    empty, otherwise the segments in ``segments_long``.

    :param string channel_name:
        The channel to use. This should be different across different
        instances of this segment if you don't want the different instances
        to interact with each other.
    :param (string,string_list)_list segments_short:
        A list of (contents, highlight_groups) touples, the segments
        to be displayed in the short mode.
    :param (string,string_list)_list segments_long:
        A list of (contents, highlight_groups) touples, the segments
        to be displayed in the long mode.

    Interaction: ``#bar;ch_<fill/clear/toggle>`` fills/ clears/ toggles the
    specified channel.
    '''

    if 'payloads' in segment_info and channel_name in segment_info['payloads'] and segment_info['payloads'][channel_name]:
        return [{
            'contents': s[0],
            'highlight_groups': s[1],
            'payload_name': channel_name,
            'draw_inner_divider': True
        } for s in segments_long]
    else:
        return [{
            'contents': s[0],
            'highlight_groups': s[1],
            'payload_name': channel_name,
            'draw_inner_divider': True
        } for s in segments_short]
