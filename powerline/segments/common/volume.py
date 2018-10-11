from __future__ import (unicode_literals, division, absolute_import, print_function)
try:
    import alsaaudio

    def vol(pl, format='VL {volume:3.0%}', format_muted=None, control='Master', id=0):
        '''Return the current volume.

        :param string format:
            The format.
        :param string control:
            The control.
        :param int id:
            The control id.

        Highlight groups used: ``volume_gradient`` (gradient).

        Click values supplied: ``volume`` (int), ``muted`` (boolean)
        '''


        avg = 0;

        res = alsaaudio.Mixer(control,id).getvolume();

        for a in res:
            avg += a;

        if alsaaudio.Mixer(control,id).getmute()[0] == 1 and not format_muted:
            return None
        elif not format:
            return None

        muted = alsaaudio.Mixer(control,id).getmute()[0] == 1

        return [{
            'contents':(format_muted.format(volume='--')
                if muted else format.format(volume=avg/(100*len(res)))),
            'highlight_groups': ['volume_gradient'],
            'divider_highlight_group': None,
            'gradient_level': int(a / len( res )),
            'click_values': {'volume': avg/(100*len(res)), 'muted': muted}
        }]

except ImportError:
    def vol(pl, *args, **kwargs):
        return None
