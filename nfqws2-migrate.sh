#!/bin/bash
# nfqws2-migrate.sh - Миграция всех конфигураций nfqws

CONVERTER="$(dirname "$0")/nfqws_converter.py"

# Функция для конвертации файла
convert_file() {
    local input="$1"
    local output="${input%.*}.nfqws2.conf"
    
    echo "🔄 Конвертирую $input -> $output"
    python3 "$CONVERTER" --input "$input" --output "$output"
    
    if [ $? -eq 0 ]; then
        echo "✅ Успешно: $output"
        return 0
    else
        echo "❌ Ошибка при конвертации $input"
        return 1
    fi
}

# Функция для проверки зависимостей
check_deps() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Требуется Python3"
        exit 1
    fi
    
    if [ ! -f "$CONVERTER" ]; then
        echo "❌ Конвертер не найден: $CONVERTER"
        exit 1
    fi
}

# Основная логика
main() {
    check_deps
    
    echo "🚀 Миграция конфигураций nfqws -> nfqws2"
    echo "========================================"
    
    # Поиск конфигурационных файлов nfqws
    echo "🔍 Поиск файлов конфигурации..."
    
    find /etc /opt/etc /usr/local/etc -name "*nfqws*.conf" -type f 2>/dev/null | \
    while read config; do
        # Пропускаем уже конвертированные файлы
        if [[ "$config" != *".nfqws2.conf" ]]; then
            convert_file "$config"
        fi
    done
    
    echo "========================================"
    echo "📋 Проверьте следующие файлы:"
    find /etc /opt/etc /usr/local/etc -name "*.nfqws2.conf" -type f 2>/dev/null
}

# Запуск
main "$@"