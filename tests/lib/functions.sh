#!/bin/bash -e
# vim: set ts=4 sw=4 sts=4 et :

#
# Shared functions
#

# Copyright (C) 2014 - 2015 Jason Mehring <nrgaway@gmail.com>
# License: GPL-2+
# Authors: Jason Mehring
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

DISTS_FEDORA=(
    'fc20'
    'fc21'
    'fc22'
    'fc23'
)

DISTS_DEBIAN=(
    'wheezy'
    'jessie'
    'trusty'
    'utopic'
    'vivid'
)

# ==============================================================================
# Define colors
# ==============================================================================
colors() {
   ## Thanks to:
   ## http://mywiki.wooledge.org/BashFAQ/037
   ## Variables for terminal requests.
   [[ -t 2 ]] && {
       export alt=$(      tput smcup  || tput ti      ) # Start alt display
       export ealt=$(     tput rmcup  || tput te      ) # End   alt display
       export hide=$(     tput civis  || tput vi      ) # Hide cursor
       export show=$(     tput cnorm  || tput ve      ) # Show cursor
       export save=$(     tput sc                     ) # Save cursor
       export load=$(     tput rc                     ) # Load cursor
       export bold=$(     tput bold   || tput md      ) # Start bold
       export stout=$(    tput smso   || tput so      ) # Start stand-out
       export estout=$(   tput rmso   || tput se      ) # End stand-out
       export under=$(    tput smul   || tput us      ) # Start underline
       export eunder=$(   tput rmul   || tput ue      ) # End   underline
       export reset=$(    tput sgr0   || tput me      ) # Reset cursor
       export blink=$(    tput blink  || tput mb      ) # Start blinking
       export italic=$(   tput sitm   || tput ZH      ) # Start italic
       export eitalic=$(  tput ritm   || tput ZR      ) # End   italic
   [[ ${TERM} != *-m ]] && {
       export red=$(      tput setaf 1|| tput AF 1    )
       export green=$(    tput setaf 2|| tput AF 2    )
       export yellow=$(   tput setaf 3|| tput AF 3    )
       export blue=$(     tput setaf 4|| tput AF 4    )
       export magenta=$(  tput setaf 5|| tput AF 5    )
       export cyan=$(     tput setaf 6|| tput AF 6    )
   }
       export white=$(    tput setaf 7|| tput AF 7    )
       export default=$(  tput op                     )
       export eed=$(      tput ed     || tput cd      )   # Erase to end of display
       export eel=$(      tput el     || tput ce      )   # Erase to end of line
       export ebl=$(      tput el1    || tput cb      )   # Erase to beginning of line
       export ewl=$eel$ebl                                # Erase whole line
       export draw=$(     tput -S <<< '   enacs
                                   smacs
                                   acsc
                                   rmacs' || { \
                   tput eA; tput as;
                   tput ac; tput ae;         } )   # Drawing characters
       export back=$'\b'
   } 2>/dev/null ||:

   export build_already_defined_colors="true"
}

if [ ! "$build_already_defined_colors" = "true" ]; then
   colors
fi

# ==============================================================================
# Display messages in color
# ==============================================================================
output() {
    echo -e ""$@""
}

outputc() {
    color=${1}
    shift
    output "${!color}"$@"${reset}" || :
}

info() {
    output "${bold}${blue}INFO: "$@"${reset}" || :
}

debug() {
    output "${bold}${green}DEBUG: "$@"${reset}" || :
}

warn() {
    output "${stout}${yellow}WARNING: "$@"${reset}" || :
}

error() {
    output "${bold}${red}ERROR: "$@"${reset}" || :
}

elementIn () {
  # $1: element to check for
  # $2: array to check for element in
  local element
  for element in "${@:2}"; do [[ "$element" == "$1" ]] && return 0; done
  return 1
}
