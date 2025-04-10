#!/bin/bash

CSGO_PATH="$HOME/.steam/steam/steamapps/common/Counter-Strike Global Offensive Beta - Dedicated Server"

cd "$CSGO_PATH" || { echo "Ошибка: не удалось перейти в $CSGO_PATH"; exit 1; }
screen -d -m ./start.sh
