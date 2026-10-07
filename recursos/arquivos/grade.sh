#!/bin/sh
# Abre a grade de aplicativos ou a busca do d3bian-init-oasis-xfce (rofi).
#
#   d3bian-grade grade    todos os aplicativos em grade (Super+A)
#   d3bian-grade busca    aplicativos, janelas e comandos (Super+Espaco)
#
# Chamado com o rofi ja aberto, fecha: o mesmo atalho abre e fecha.
modo="${1:-grade}"
case "$modo" in grade|busca) ;; *) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;; esac

command -v rofi >/dev/null || { echo "falta o rofi: sudo apt install rofi" >&2; exit 1; }
if pgrep -u "$(id -u)" -x rofi >/dev/null; then
  pkill -u "$(id -u)" -x rofi
  exit 0
fi

tema="$HOME/.config/rofi/oasis-$modo.rasi"
[ -f "$tema" ] || tema=""
if [ "$modo" = grade ]; then
  exec rofi -show drun -modes drun -show-icons -drun-display-format '{name}' \
    ${tema:+-theme "$tema"}
fi
exec rofi -show drun -modes 'drun,window,run' -show-icons -drun-display-format '{name}' \
  -display-drun 'Aplicativos' -display-window 'Janelas' -display-run 'Comandos' \
  ${tema:+-theme "$tema"}
