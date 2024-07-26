#!/bin/bash

if [[ -z $1 ]]; then
  echo "Использование: "
  echo "$0 <путь_до_python_файла>"
  echo
  echo "Перезапускает указанный скрипт, если он крашнулся. Простейшая вещь, всем рекомендую :)"
  exit 1
fi

while true; do
  git pull >temp.log && python $1 2>>temp.log
  lastcode=$?

  if [[ $lastcode = 0 ]]; then
    echo "$1 завершился без ошибок. Выключаем..."
    exit
  elif [[ $lastcode = 2 ]]; then
    echo "Код 2, выходим..."
    exit 2
  fi
  echo "$1 умер (Код ошибки $lastcode)"
done
