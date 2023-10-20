=========
qubesctl
=========

NAME
====
qubesctl - directly call salt commands from dom0

qubesctl should be run instead of salt-call --local, and accepts the
same arguments as that tool.

SYNOPSIS
========
| qubesctl [options]

OPTIONS
=======
-h, --help
    Show this help message and exit

--show-output
Show output of management commands

--force-color
Show output in colour, and allow control characters from qubes.
This option is UNSAFE

--skip-dom0
Skip dom0 configuration.

--targets <qubes>
Comma separated list of qubes to target

--templates
Target all templates

--app
Target all AppVMs

--all
Target all non disposable VMs, (Templates and AppVMs)

--max-concurrency <number>
Maximum number of VMs configured simultaneously. Default: 4

--skip-top-check
Do not skip targeted qubes during a highstate if it appears they are not targeted by any state.

AUTHORS
=======
| unman <unman@thirdeyesecurity.org> 
