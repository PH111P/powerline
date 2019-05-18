import argparse


def get_argparser(ArgumentParser=argparse.ArgumentParser):
    parser = ArgumentParser(
        description='Google Calendar Segment Authenticator'
    )
    parser.add_argument(
        '--path', metavar='PATH',
        help='Path to use'
    )
    parser.add_argument(
        'client_id',
        help='Client id'
    )
    parser.add_argument(
        'client_secret',
        help='Client secret'
    )
    return parser
