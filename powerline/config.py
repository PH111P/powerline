import os


POWERLINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINDINGS_DIRECTORY = os.path.join(POWERLINE_ROOT, 'powerline', 'bindings')
TMUX_CONFIG_DIRECTORY = os.path.join(BINDINGS_DIRECTORY, 'tmux')
DEFAULT_SYSTEM_CONFIG_DIR = None
