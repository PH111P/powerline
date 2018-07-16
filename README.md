Powerline
=========

[![Build Status](https://travis-ci.org/PH111P/powerline.svg?branch=develop)](https://travis-ci.org/PH111P/powerline)
[![Documentation Status](https://readthedocs.org/projects/powerline-i3/badge/?version=latest)](http://powerline-i3.readthedocs.io/en/latest/?badge=latest)


This is a fork of Kim Silkebækken's (kim.silkebaekken+vim@gmail.com) powerline
(https://github.com/powerline/powerline).

**Powerline is a statusline plugin for vim, and provides statuslines and
prompts for several other applications, including zsh, bash, tmux, IPython,
Awesome, i3 and Qtile. However, this fork is designed to be used in particular
as a replacement for i3's i3bar.**

Features
--------

For general features, consult the documentation. These are
the features that were added in this fork.

* List all workspaces, _and icons of applications currently running on a workspace (using FontAwesome)_
* More multi-monitor options for the workspace segment.
* Enhanced battery segment, having the same features as the i3bar one. Further, this segment
  now works with multiple batteries.
* Enhanced wifi segment to match i3bar's.
* Added a volume segment.
* Added GPMDP support in the player segment.
* Merged and improved [ZyX-I's revinfo branch](https://github.com/ZyX-I/powerline/tree/revinfo), replacing the VCS segment.
* Added an auto-rotate segment.
* Click support (see documentation below)
* Simplified gradients: specify start and end colors (and optionally intermediate colors) as hex values, values in-between colors (and corresponding cterm colors) will be generated automatically.
* Support for global menus

Changes requiring documentation
-------------------------------

This fork extends the files used by the powerline to configure the color scheme in various ways:
* `attrs` is now optional, i.e., it can be omitted
* `click` is a new optional field to configure the behavior of a highlight group on a click.
 Where `click` is a dictionary mapping the values `left`, `right`, `middle`, `scroll up` or `scroll down`
 to a string to be executed by a shell. (Currently only the lemonbar binding supports this. You can disable clicks via the `no_clicks` flag.)
 Further, the string to be executed may contain a placeholder for the segment's content. This placeholder uses python's
 `string.format` syntax. You may also pass some special commands to the bar/to specific segments directly via special bar commands starting with `#bar;`.
* You may pass an `alt_output` flag to `powerline-lemonbar`, then it uses the `-O` flag for setting the output for the bar.
* The colors in `fg` and `bg` can be specified directly through hex values using `0x` as a prefix (`0xRRGGBB` or `0xAARRGGBB`). These hex values will be translated back into xterm color indices whenever possible.
* The bar has an additional `center` region where segments may be placed. The center region uses pipes (`|`) as separators per default.
* The `active_window_title` segment includes optional functionality for global menus. Consult the section below for details on the required configuration.

Examples
--------

A configuration to let the workspace segment act like the i3bar's (`workspace_name` is a special value that gets set to the correct workspace name by the workspace segment.):

      "workspace": { "fg": "0xe4e4e4", "bg": "0x0087af", "click": { "left": "i3-msg workspace {workspace_name}", "right": "i3-msg move to workspace {workspace_name}" } },
      "workspace:urgent": { "bg": "0x0087af", "fg": "0xffaf00", "click": { "left": "i3-msg workspace {workspace_name}", "right": "i3-msg move to workspace {workspace_name}" } },

A handy configuration of the volume segment:

      "volume_gradient": { "fg": "green_yellow_red", "bg": "0x005f87", "click": { "scroll up": "pactl set-sink-volume 0 +1%", "scroll down": "pactl set-sink-volume 0 -1%"} },

Note that the `lemonbar` allows for only a fixed number of clickable areas, which has to be specified as an argument (via `-a`).

Installation
------------

This fork is available from the AUR (`powerline-i3-git`).
Alternatively, you may use `pip` for the installation:

	pip install git+https://github.com/PH111P/powerline.git@develop

Note that using this fork (or the powerline in general) requires some additional packages to be installed,
namely:

* [powerline-fonts](https://www.archlinux.org/packages/community/x86_64/powerline-fonts/)
* [ttf-font-awesome-4](https://aur.archlinux.org/packages/ttf-font-awesome-4/) (Version 5 relocated some symbols)
* i3 or i3-gaps
* [lemonbar-clicks-git](https://aur.archlinux.org/packages/lemonbar-clicks-git/) ([Lemonbar](https://github.com/ph111p/bar) supporting fontconfig fonts)
* [python-xlib](https://github.com/python-xlib/python-xlib)
* [i3ipc-python-git](https://github.com/acrisci/i3ipc-python) (workspace segment, available from AUR)

Optionally, the following packages should be installed if you want to use the corresponding segments.

* python-iwlib (wifi segment)
* python-pyalsaaudio (volume segment, available from AUR)
* xorg-xinput (screen rotation segment, used to map input devices to outputs)
* python-google-api-python-client (Google Calendar segment; this segment also requires a valid dev key to work)
* python-psutil (cpu load segment)
* python-pygit2 (better performance of the vcs segment)
* appmenu-qt4 (global menu support in qt4 apps)
* appmenu-qt5 (global menu support in qt5 apps)
* appmenu-gtk-module-git (global menu support in gtk apps)
* libdbusmenu-glib (global menu support for chrome/chromium)
* libdbusmenu-gtk3 (global menu support for chrome/chromium)
* libdbusmenu-gtk2 (global menu support for chrome/chromium)
* pygtk (global menu support)
* python-gobject (global menu support)


To actually _use_ the powerline in your i3 setup, replace the following lines in your `.config/i3/config`

      bar {
          status_command i3status
      }

with this line (you may want to adjust the height and the font size):

      exec "powerline-lemonbar --height 16 -- -b -f 'DejaVu Sans Mono-11' -f 'PowerlineSymbols-12' -f 'FontAwesome-11'"

Note that ``Font Awesome`` is used to display some icons, thus changing it to some other font will likely break these icons.

**Attention: `-f 'PowerlineSymbols-12'` is required if you have the non-git version of the powerline-fonts package installed. If you have the git version of that package installed (from the AUR), use `-f 'DejaVu Sans Mono for Powerline-11'` instead.**

To use global menus in the bar, also start the `powerline-globmenu` script at startup.
Further, add the following to your `.bashrc`:

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

Consult the `global_menu` default theme on how to configure the `active_window_title` segment.

Configuration
-------------

Basic powerline configuration is done via `JSON` files located at `.config/powerline/`. It is a good idea to start by copying the default configuration located at `powerline_root/powerline/config_files/` to `.config/powerline/`.
If you installed the powerline from the AUR or via pip, `powerline_root` should be `/usr/lib/python3.6/site-packages/` or something similar, depending on your python version.

This should yield you the following directory structure:

```
.config/powerline/
├── colorschemes
│   ├── ...
│   └── wm
|       └── default.json  // Your configuration goes here
├── colors.json
├── config.json
└── themes
    ├── ...
    └── wm
        └── default.json  // Your configuration goes here

```

The files in the subdirectories of `themes` are used to specify which segments shall be shown; the files in subdirectories of `colorschemes` are used to specify which colors (as defined in `colors.json`) shall be used to display a segment.

Note that your local configuration only overrides the global configuration, it does not replace it, i.e. if you don't configure something locally, the global default will be used instead.

Consult the [documentation](https://powerline-i3.readthedocs.io/en/latest/configuration.html#quick-setup-guide) for more details. See also the [segment reference](https://powerline-i3.readthedocs.io/en/latest/configuration/segments.html) for available segments and their configuration.

Some screens
------------
Some big, blue, beautiful powerlines.
![Everything](https://github.com/PH111P/powerline/blob/develop/docs/source/_static/img/pl-i3demo1.png)
![Modes](https://github.com/PH111P/powerline/blob/develop/docs/source/_static/img/pl-i3demo2.png)
This is as far as it could get. However, this is a rare use case.
![Full](https://github.com/PH111P/powerline/blob/develop/docs/source/_static/img/pl-i3demo3.png)

