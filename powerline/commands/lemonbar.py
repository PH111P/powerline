import argparse


def get_argparser(ArgumentParser=argparse.ArgumentParser):
    parser = ArgumentParser(
        description='Powerline BAR bindings.'
    )
    parser.add_argument(
        '--i3', action='store_true',
        help='Unused.'
    )
    parser.add_argument(
        '--no_i3', action='store_true',
        help='Don\'t Subscribe for i3 events.'
    )
    parser.add_argument(
        '--use_defaults', '-d', action='store_true',
        help='Do also supply the bar with the default extra arguments.'
    )
    parser.add_argument(
        '--clicks', action='store_true',
        help="Unused."
    )
    parser.add_argument(
        '--no_clicks', action='store_true',
        help='Don\'t redirect lemonbar output to /bin/sh'
    )
    parser.add_argument(
        '--alt_output', '-o', action='store_true',
        help='Use alternative output detection'
    )
    parser.add_argument(
        '--height', '-H', default='18',
        metavar='PIXELS', help='Bar height. Defaults to 18.'
    )
    parser.add_argument(
        '--correction', '-c', default='1',
        help='Correction factor for default font sizes.'
    )
    parser.add_argument(
        '--relative_height', '-R', action='store_true',
        help='Interpret the given height as relative height in percent.'
    )
    parser.add_argument(
        '--interval', '-i',
        type=float, default=5,
        metavar='SECONDS', help='Refresh interval.'
    )
    parser.add_argument(
        '--bar_command', '-C',
        default='lemonbar',
        metavar='CMD', help='Name of the lemonbar executable to use.'
    )
    parser.add_argument(
        'args', nargs=argparse.REMAINDER,
        help='Extra arguments for lemonbar. Should be preceded with ``--`` '
             'argument in order not to be confused with script own arguments.\n'
             'Defaults to -a 40 -b -f \'DejaVu Sans Mono-{height*.6}\' -f \'PowerlineSymbols-{height*.75}\' -f \'FontAwesome-{height*.65}\'.'
    )
    return parser
