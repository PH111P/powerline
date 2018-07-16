**********************
Window manager widgets
**********************

Awesome widget
==============

.. note:: Powerline currently only supports awesome 3.5 and 4+.

.. note:: The Powerline widget will spawn a shell script that runs in the
   background and updates the statusline with ``awesome-client``.

Add the following to :file:`rc.lua`, where ``{repository_root}`` is the absolute
path to Powerline installation directory (see :ref:`repository root
<repository-root>`):

.. code-block:: lua

   package.path = package.path .. ';{repository_root}/powerline/bindings/awesome/?.lua'
   require('powerline')

Then add the ``powerline_widget`` to ``wibox``:

.. code-block:: lua

   -- awesome3.5
   right_layout:add(powerline_widget)

   -- awesome4+
   s.mywibox:setup {
   ...
     { -- Right widgets
       ...
       powerline_widget,
     },
   }

Qtile widget
============

Add the following to :file:`~/.config/qtile/config.py`:

.. code-block:: python

   from libqtile.bar import Bar
   from libqtile.config import Screen
   from libqtile.widget import Spacer

   from powerline.bindings.qtile.widget import PowerlineTextBox

   screens = [
       Screen(
           top=Bar([
                   PowerlineTextBox(update_interval=2, side='left'),
                   Spacer(),
                   PowerlineTextBox(update_interval=2, side='right'),
               ],
               35 # width
           ),
       ),
   ]

.. _lemonbar-usage:

lemonbar (formerly bar-aint-recursive)
======================================

To run the bar simply start the binding script:

.. code-block:: shell
    powerline-lemonbar


You can specify options to be passed to ``lemonbar`` after ``--``, like so:

.. code-block:: shell
    powerline-lemonbar --height 16 -- -a 40 -f 'DejaVu Sans Mono-11' -f 'PowerlineSymbols-12' -f 'FontAwesome-11'"


Note that, if you don't specify any options, ``powerline-lemonbar`` will default to the above.


To run with i3, simply ``exec`` this in the i3 config file:

.. code-block:: shell

    exec powerline-lemonbar


Running the binding in i3-mode will require `i3ipc <https://github.com/acrisci/i3ipc-python>`_
(or the outdated `i3-py <https://github.com/ziberna/i3-py>`_).

See the `lemonbar documentation <https://github.com/LemonBoy/bar>`_ for more
information and options.

To enhance the global menu, add the following to your ``.bashrc``:

.. code-block:: shell

    if [ -n "$GTK_MODULES" ]; then
        GTK_MODULES="${GTK_MODULES}:appmenu-gtk-module"
    else
        GTK_MODULES="appmenu-gtk-module"
    fi

    if [ -z "$UBUNTU_MENUPROXY" ]; then
        UBUNTU_MENUPROXY=1
    fi

    export GTK_MODULES
    export UBUNTU_MENUPROXY


Further, add the following line to your i3 config

.. code-block:: shell

    exec --no-startup-id powerline-globmenu



=======

All ``powerline-lemonbar`` arguments:

.. automan:: powerline.commands.lemonbar
   :prog: powerline-lemonbar
   :minimal: true

