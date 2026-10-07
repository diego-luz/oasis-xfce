#!/bin/sh
# Abre a grade de aplicativos ou a busca do d3bian-init-oasis-xfce (rofi).
#
#   d3bian-grade grade    todos os aplicativos em grade (Super+A)
#   d3bian-grade busca    aplicativos, janelas e comandos (Super+Espaco)
#
# Chamado com a grade ou a busca ja aberta, fecha: o mesmo atalho abre e
# fecha. So o rofi aberto por aqui fecha (anotado num arquivo de pid); outro
# rofi da pessoa fica.
modo="${1:-grade}"
case "$modo" in grade|busca) ;; *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;; esac

command -v rofi >/dev/null || { echo "falta o rofi: sudo apt install rofi" >&2; exit 1; }
pasta="${XDG_RUNTIME_DIR:-}"
[ -n "$pasta" ] && [ -d "$pasta" ] && [ -O "$pasta" ] || pasta="$HOME/.cache"
pidf="$pasta/d3bian-grade.pid"
pid=$(cat "$pidf" 2>/dev/null || true)
case "$pid" in
  ''|*[!0-9]*) ;;
  *)
    # o pid ainda e de um rofi desta conta (e nao um numero reaproveitado)
    if [ -O "/proc/$pid" ] && [ "$(cat "/proc/$pid/comm" 2>/dev/null)" = rofi ]; then
      kill "$pid" 2>/dev/null || true
      rm -f "$pidf"
      exit 0
    fi ;;
esac

tema="$HOME/.config/rofi/oasis-$modo.rasi"
[ -f "$tema" ] || tema=""
# os icones do tema de agora do Xfce (o rofi nao le o xsettings)
icones=$(xfconf-query -c xsettings -p /Net/IconThemeName 2>/dev/null || true)
if [ "$modo" = grade ]; then
  rofi -show drun -modes drun -show-icons -drun-display-format '{name}' \
    -display-drun 'Aplicativos' ${icones:+-icon-theme "$icones"} ${tema:+-theme "$tema"} &
else
  rofi -show drun -modes 'drun,window,run' -show-icons -drun-display-format '{name}' \
    -display-drun 'Aplicativos' -display-window 'Janelas' -display-run 'Comandos' \
    ${icones:+-icon-theme "$icones"} ${tema:+-theme "$tema"} &
fi
pid=$!
mkdir -p "$pasta"
echo "$pid" > "$pidf"
wait "$pid"
codigo=$?
# so tira o arquivo se ainda e deste rofi (outro pode ter aberto depois)
[ "$(cat "$pidf" 2>/dev/null)" = "$pid" ] && rm -f "$pidf"
exit "$codigo"
