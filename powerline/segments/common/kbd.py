from powerline.lib.shell import run_cmd

DEFAULT_LOCKS = {
        'Caps Lock': 'Caps',
        'Num Lock': 'Num',
        'Scroll Lock': 'Scroll',
        'Compose': 'Compose',
        'Kana': 'Kana'
    }
STATUS_DICT = {
        'on': 'on',
        'off': 'off'
    }

def lock_status(pl, format = '{lock}: {status}',  locks = DEFAULT_LOCKS, status_dict = STATUS_DICT):
    '''Run ``xset -q`` to get the current status of the keyboard locks.
    Each specified lock is returned as its own segment and optionally uses a different
    highlight group.

    :param string format:
        The format to use. Valid fields for this format string are ``lock`` and ``status``.
    :param dict locks:
        The different locks to check and what to display for them
        (e.g. {'Caps Lock': 'Caps', 'Num Lock': '123'})
    :param dict status_dict:
        Dictionary used to actually display the status
        (e.g. {'on': 'on', 'off': 'off'})

    Highlight groups used: ``keyboard:caps_lock_on``, ``keyboard:caps_lock_off``, ``keyboard`` or ``keyboard:num_lock_on``, ``keyboard:num_lock_off``, ``keyboard`` or ``keyboard:scroll_lock_on``, ``keyboard:scroll_lock_off``, ``keyboard``
    '''

    raw_data = run_cmd(pl, ['xset', '-q']).replace('\n', '')
    return [{'contents': format.format(lock = locks[l], status =
        status_dict[raw_data.split(l)[1].lstrip(': ').split(' ')[0]]),
        'highlight_groups': ['keyboard:' + l.lower().replace(' ', '_') + '_'
            + a for a in status_dict] + ['keyboard'],
        'draw_inner_divider': True} for l in locks]

