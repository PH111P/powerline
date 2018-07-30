
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderer import Renderer
from powerline.theme import Theme
from powerline.lemonbar import SEGMENT_NAME

class LemonbarRenderer(Renderer):
    '''
    lemonbar (formerly bar/bar ain't recursive) renderer

    See documentation of `lemonbar <https://github.com/LemonBoy/bar>`_ and :ref:`the usage instructions <lemonbar-usage>`
    '''

    character_translations = Renderer.character_translations.copy()
    character_translations[ord('%')] = '%%{}'

    clear_left = ('%{F-}', '%{B-}')
    clear_right = ('%{F-}', '%{B-}')
    center_is_wide = False

    hov_cmd = [None, None]

    @staticmethod
    def hlstyle(*args, **kwargs):
        # We don’t need to explicitly reset attributes, so skip those calls
        return ''

    def hl(self, escaped_contents, fg=None, bg=None, attrs=None, click=None, \
            click_values={}, next_segment=None, *args, **kwargs):
        button_map = {
                'left': 1,
                'middle': 2,
                'right': 3,
                'scroll up': 4,
                'scroll down': 5,
                'hover enter': 6,
                'hover leave': 7
                }

        text = ''
        click_count = 0
        cl_hov = ''

        next_hov = [None, None]
        if next_segment and 'highlight' in next_segment and 'click' in next_segment['highlight'] \
                and next_segment['highlight']['click'] != None:
            if 'hover enter' in next_segment['highlight']['click']:
                next_hov[0] = next_segment['highlight']['click']['hover enter']
                next_hov[0] = next_hov[0].replace(':', '\\:') + SEGMENT_NAME.decode() \
                        + ((next_segment['payload_name']) if 'payload_name' in next_segment \
                        else next_segment['name'])

            if 'hover leave' in next_segment['highlight']['click']:
                next_hov[1] = next_segment['highlight']['click']['hover leave']
                next_hov[1] = next_hov[1].replace(':', '\\:') + SEGMENT_NAME.decode() \
                        + ((next_segment['payload_name']) if 'payload_name' in next_segment \
                        else next_segment['name'])

        if click is not None:
            for key in [c for c in click if 'hover' in c] + [c for c in click if not 'hover' in c]:
                if not key in button_map:
                    continue
                st = click[key].format(escaped_contents.strip(), **click_values).strip()
                st = st.replace(':', '\\:') + SEGMENT_NAME.decode() \
                        + ((kwargs['payload_name']) if 'payload_name' in kwargs else \
                        (kwargs['name'] if 'name' in kwargs else ''))
                st2 = click[key].replace(':', '\\:') + SEGMENT_NAME.decode() \
                        + ((kwargs['payload_name']) if 'payload_name' in kwargs else \
                        (kwargs['name'] if 'name' in kwargs else ''))

                if key == 'hover enter':
                    if self.hov_cmd[0] == None:
                        self.hov_cmd[0] = st2
                    else:
                        continue
                if key == 'hover leave':
                    if self.hov_cmd[1] == None:
                        self.hov_cmd[1] = st2
                    else:
                        continue

                text += '%{{A{1}:{0}:}}'.format(st, button_map[key])
                if not 'hover' in key:
                    click_count += 1

        for i in [0, 1]:
            # Ignore seperators
            if self.hov_cmd[i] != next_hov[i] and self.hov_cmd[i] != None and 'name' in kwargs:
                cl_hov += '%{A}'
                self.hov_cmd[i] = None

        (fg_col, bg_col) = self.clear_right
        if not self.center_is_wide:
            (fg_col, bg_col) = ('','')

        if 'side' in kwargs:
            if kwargs['side'] == 'left':
                (fg_col, bg_col) = self.clear_left
            if kwargs['side'] == 'right':
                (fg_col, bg_col) = self.clear_right

        if fg is not None:
            if fg is not False and fg[1] is not False:
                if fg[1] <= 0xFFFFFF:
                    fg_col = '%{{F#ff{0:06x}}}'.format(fg[1])
                else:
                    fg_col = '%{{F#{0:08x}}}'.format(fg[1])

        if bg is not None:
            if bg is not False and bg[1] is not False:
                if bg[1] <= 0xFFFFFF:
                    bg_col = '%{{B#ff{0:06x}}}'.format(bg[1])
                else:
                    bg_col = '%{{B#{0:08x}}}'.format(bg[1])

        reset = '%{F-B-}'
        if 'side' in kwargs:
            if kwargs['side'] == 'center':
                if 'width' in kwargs and  kwargs['width'] == 'auto':
                    self.center_is_wide = True
                if self.clear_left == ('%{F-}', '%{B-}'):
                    self.clear_left = (fg_col, bg_col)
                self.clear_right = (fg_col, bg_col)
            if kwargs['side'] == 'left':
                reset = self.clear_left[0] + self.clear_left[1]
            if kwargs['side'] == 'right':
                reset = self.clear_right[0] + self.clear_right[1]

        if not self.center_is_wide:
            reset = '%{F-B-}'
        text += fg_col + bg_col
        return text + escaped_contents + reset + ('%{A}' * click_count) + cl_hov

    def render(self, width, *args, **kwargs):
        kw2 = kwargs
        if 'segment_info' in kwargs:
            kw2['segment_info'].update({'output': kwargs.get('matcher_info')})
        else:
            kw2.update({'segment_info': {'output': kwargs.get('matcher_info')}})

        if 'side' in kwargs:
            return super(LemonbarRenderer, self).render(width=width//2 if width else None,
                    *args, **kw2)

        self.clear_left = ('%{F-}', '%{B-}')
        self.clear_right = ('%{F-}', '%{B-}')
        self.center_is_wide = False
        res = '%{{c}}{0}%{{l}}{1}%{{r}}{2}'.format(
            super(LemonbarRenderer, self).render(width=width if width else None, side='center',
                *args, **kw2),
            super(LemonbarRenderer, self).render(width=width//2 if width else None, side='left',
                *args, **kw2),
            super(LemonbarRenderer, self).render(width=width//2 if width else None, side='right',
                *args, **kw2)
        )
        return res

    def get_theme(self, matcher_info):
        if not matcher_info or matcher_info not in self.local_themes:
            return self.theme
        match = self.local_themes[matcher_info]

        try:
            return match['theme']
        except KeyError:
            match['theme'] = Theme(
                theme_config=match['config'],
                main_theme_config=self.theme_config,
                **self.theme_kwargs
            )
            return match['theme']


renderer = LemonbarRenderer
