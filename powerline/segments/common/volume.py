try:
    import alsaaudio

    def generate_controls( steps, current_value, icons ):
        oldcv = current_value
        current_value = current_value * ( steps - 1 )

        res = []
        full = True

        for i in range( 0, steps ):
            symb = None
            if full and i * 100 + 50 >= current_value and ( current_value == 0 or i > 0 ):
                full = False
                symb = 'cur'
            symb = symb or ('full' if full else 'empty')

            res += [{
                'contents': icons[symb],
                'highlight_groups': [ 'volume:' + symb, 'volume:controls', 'volume:gradient', 'volume_gradient' ],
                'gradient_level': oldcv,
                'click_values': { 'volume': oldcv, 'muted': False,
                    'control_level': int( i * 100 / ( steps - 1 ) ) },
                'draw_inner_divider': False
            }]
        return res

    def vol( pl, format = 'VL {volume:3.0%}', format_muted = None,
            control = 'Master', id = 0, icons = { 'full': '=', 'cur': 'X', 'empty': '-' } ):
        '''Return the current volume.

        :param string format:
            The format.
        :param string control:
            The control.
        :param int id:
            The control id.
        :param dict icons:
            Icons for the visualization.

        Highlight groups used: ``volume:gradient`` (gradient).

        Click values supplied: ``volume`` (int), ``muted`` (boolean)
        '''


        avg = 0;

        res = alsaaudio.Mixer( control, id ).getvolume();

        for a in res:
            avg += a;

        if alsaaudio.Mixer( control, id ).getmute()[ 0 ] == 1 and not format_muted:
            return None
        elif not format:
            return None

        muted = alsaaudio.Mixer(control,id).getmute()[0] == 1

        if not muted and '{controls' in format:
            spl = format.split('{controls')

            res_seg = [{
                'contents': spl[ 0 ].format( volume = avg / ( 100 * len( res ) ) ),
                'highlight_groups': [ 'volume:gradient', 'volume_gradient' ],
                'gradient_level': int( avg / len( res ) ),
                'click_values': { 'volume': avg / ( 100 * len( res ) ), 'muted': muted },
                'draw_inner_divider': False
            }]

            for st in spl[ 1 : ]:
                parts = st.split( '}', 1 )
                steps = 5

                if parts[ 0 ] and parts[ 0 ].startswith( ':' ):
                    try:
                        steps = int( parts[ 0 ][ 1 : ] )
                    except ValueError:
                        pass

                res_seg += generate_controls( steps, int( avg / len( res ) ), icons )

                res_seg += [{
                    'contents':parts[ 1 ].format( volume = avg / ( 100 * len( res ) ) ),
                    'highlight_groups': [ 'volume:gradient', 'volume_gradient' ],
                    'gradient_level': int( avg / len( res ) ),
                    'click_values': { 'volume': avg / ( 100 * len( res ) ), 'muted': muted },
                    'draw_inner_divider': False
                }]

            return res_seg

        return [{
            'contents':(format_muted.format( volume='--' )
                if muted else format.format( volume = avg / ( 100 * len( res ) ) ) ),
            'highlight_groups': [ 'volume:gradient', 'volume_gradient' ],
            'gradient_level': int( avg / len( res ) ),
            'click_values': { 'volume': avg / ( 100 * len( res ) ), 'muted': muted }
        }]

except ImportError:
    def vol( pl, format = 'VL {volume:3.0%}', format_muted = None,
            control = 'Master', id = 0, icons = { 'full': '=', 'cur': 'X', 'empty': '-' } ):
        '''Return the current volume.

        :param string format:
            The format.
        :param string control:
            The control.
        :param int id:
            The control id.
        :param dict icons:
            Icons for the visualization.

        Highlight groups used: ``volume:gradient`` (gradient).

        Click values supplied: ``volume`` (int), ``muted`` (boolean)
        '''

        pl.error('The volume segment requires pyalsaaudio.')
        return None
