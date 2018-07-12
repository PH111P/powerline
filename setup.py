#!/usr/bin/env python

from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import subprocess
import logging
import shlex

from traceback import print_exc
from setuptools import setup, find_packages


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(CURRENT_DIR, 'README.md'), 'rb').read().decode('utf-8')
except IOError:
    README = ''

OLD_PYTHON = sys.version_info < (2, 7)


def compile_client():
    '''Compile the C powerline-client script.'''

    if hasattr(sys, 'getwindowsversion'):
        raise NotImplementedError()
    else:
        from distutils.ccompiler import new_compiler
        compiler = new_compiler().compiler
        cflags = os.environ.get('CFLAGS', str('-O3'))
        # A normal split would do a split on each space which might be incorrect. The
        # shlex will not split if a space occurs in an arguments value.
        subprocess.check_call(compiler + shlex.split(cflags) + ['-std=c11', 'client/powerline.c', '-o', 'scripts/powerline'])

try:
    compile_client()
except Exception as e:
    print('Compiling C version of powerline-client failed')
    logging.exception(e)
    # FIXME Catch more specific exceptions
    import shutil
    if hasattr(shutil, 'which'):
        which = shutil.which
    else:
        sys.path.append(CURRENT_DIR)
        from powerline.lib.shell import which
    if which('socat') and which('sed') and which('sh'):
        print('Using powerline.sh script instead of C version (requires socat, sed and sh)')
        shutil.copyfile('client/powerline.sh', 'scripts/powerline')
        can_use_scripts = True
    else:
        print('Using powerline.py script instead of C version')
        shutil.copyfile('client/powerline.py', 'scripts/powerline')
        can_use_scripts = True
else:
    can_use_scripts = False

setup(
    name='powerline-status-i3',
    version='1.8.0',
    description='The ultimate statusline/prompt utility. A fork containing more features for the i3 window manager.',
    long_description=README,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    download_url='https://github.com/ph111p/powerline/archive/develop.zip',
    author='Philip Wellnitz',
    author_email='philipwellnitz@gmx.de',
    url='https://github.com/ph111p/powerline',
    license='MIT',
    # XXX Python 3 doesn’t allow compiled C files to be included in the scripts
    # list below. This is because Python 3 distutils tries to decode the file to
    # ASCII, and fails when powerline-client is a binary.
    #
    # XXX Python 2 fucks up script contents*. Not using it to install scripts
    # any longer.
    # * Consider the following input:
    #     % alias hex1=$'hexdump -e \'"" 1/1 "%02X\n"\''
    #     % diff <(hex1 ./scripts/powerline) <(hex1 ~/.local/bin/powerline)
    #   This will show output like
    #     375c375
    #     < 0D
    #     ---
    #     > 0A
    #   (repeated, with diff segment header numbers growing up).
    #
    # FIXME Current solution does not work with `pip install -e`. Still better
    # then solution that is not working at all.
    scripts=[
        'scripts/powerline-lint',
        'scripts/powerline-daemon',
        'scripts/powerline-render',
        'scripts/powerline-config',
        'scripts/powerline-lemonbar',
        'scripts/powerline-gcal-auth'
    ] + (['scripts/powerline'] if can_use_scripts else []),
    data_files=(([] if can_use_scripts else [('bin', ['scripts/powerline'])])),
    keywords='',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    install_requires=['i3ipc', 'python-xlib']+(['argparse'] if OLD_PYTHON else []),
    extras_require={
        'volume segment': [
            'pyalsaaudio'
        ],
        'docs': [
            'Sphinx',
            'sphinx_rtd_theme',
        ],
        'appoints segment support, Google Calendar': [
            'google-api-python-client'
        ],
        'cpu load segment support': [
            'psutil'
        ],
        'wifi segment support': [
            'iwlib'
        ]
    },
    test_suite='tests' if not OLD_PYTHON else None,
)
