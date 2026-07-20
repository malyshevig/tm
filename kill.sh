
#!/bin/bash

# Имя процесса (точное совпадение) или паттерн
TARGET_PROCESS="python" 
# Максимальное количество попыток, чтобы не уйти в бесконечный цикл
MAX_ATTEMPTS=10 
# Задержка между попытками в секундах
SLEEP_TIME=2 

echo "Начинаем массовое завершение процессов: $TARGET_PROCESS"

attempt=0
# Цикл работает, пока pgrep находит хотя бы один процесс
while pgrep -x "$TARGET_PROCESS" > /dev/null; do
    attempt=$((attempt + 1))
    
    if [ $attempt -le 5 ]; then
        echo "[Попытка $attempt] Отправляем SIGTERM (корректное завершение)..."
        pkill -x "$TARGET_PROCESS"
    else
        echo "[Попытка $attempt] Отправляем SIGKILL (принудительное убийство)..."
        pkill -9 -x "$TARGET_PROCESS"
    fi
    
    sleep $SLEEP_TIME
    
    if [ $attempt -ge $MAX_ATTEMPTS ]; then
        echo "Достигнут лимит попыток. Останавливаем скрипт."
        break
    fi
done

echo "Готово. Процессов '$TARGET_PROCESS' в системе не осталось."
