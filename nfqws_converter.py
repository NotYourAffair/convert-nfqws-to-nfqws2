#!/usr/bin/env python3
"""
Конвертер конфигураций nfqws -> nfqws2
Основано на анализе API из репозиториев GitHub
"""

import re
import sys
import argparse
from typing import Dict, List, Optional, Tuple

class NfqwsConverter:
    """Конвертер параметров nfqws в nfqws2"""
    
    # Маппинг параметров из nfqws в nfqws2
    PARAM_MAPPING = {
        # Основные параметры
        '--hostlist': '--hostlist',
        '--dpi-desync': None,  # Обрабатывается отдельно
        
        # Multisplit параметры
        '--dpi-desync-split-seqovl': '--multisplit-seqovl',
        '--dpi-desync-split-pos': '--multisplit-pos',
        '--dpi-desync-fooling': '--multisplit-fooling',
        '--dpi-desync-repeats': '--multisplit-repeats',
        '--dpi-desync-split-seqovl-pattern': '--multisplit-seqovl-pattern',
        
        # Fake TLS параметры
        '--dpi-desync-fake-tls': '--fake-tls',
        '--dpi-desync-fake-pattern': '--fake-pattern',
        '--dpi-desync-fake-pos': '--fake-pos',
        '--dpi-desync-fake-ackseq': '--fake-ackseq',
        
        # Другие параметры DPI
        '--dpi-desync-ttl': '--ttl',
        '--dpi-desync-mss': '--mss',
        '--dpi-desync-ws': '--ws',
        '--dpi-desync-auto-ttl': '--auto-ttl',
        
        # Blackhole параметры
        '--dpi-desync-blackhole': '--blackhole',
        
        # Разные
        '--dpi-desync-ip-frag': '--ip-frag',
        '--dpi-desync-ip-opt': '--ip-opt',
    }
    
    # Параметры, которые удаляются (устаревшие или несовместимые)
    DEPRECATED_PARAMS = [
        '--dpi-desync-old',
        '--dpi-desync-auto',
    ]
    
    # Значения по умолчанию для некоторых параметров в nfqws2
    DEFAULT_VALUES = {
        '--multisplit-repeats': '3',
        '--multisplit-fooling': 'ts',
    }
    
    @staticmethod
    def parse_desync_modes(desync_arg: str) -> List[str]:
        """Парсит значение --dpi-desync и конвертирует в параметры nfqws2"""
        modes = desync_arg.split(',')
        result_params = []
        
        for mode in modes:
            mode = mode.strip()
            if mode == 'fake':
                result_params.append('--fake-tls')
            elif mode == 'multisplit':
                result_params.append('--multisplit')
            elif mode == 'blackhole':
                result_params.append('--blackhole')
            elif mode == 'ipfrag':
                result_params.append('--ip-frag')
            elif mode == 'auto':
                # В nfqws2 auto режим может быть реализован иначе
                result_params.append('--auto-ttl')
            # Игнорируем неизвестные режимы
        
        return result_params
    
    @staticmethod
    def convert_param(param: str, value: str) -> List[Tuple[str, str]]:
        """Конвертирует один параметр из nfqws в nfqws2"""
        param = param.strip()
        value = value.strip() if value else ''
        
        # Проверяем устаревшие параметры
        if param in NfqwsConverter.DEPRECATED_PARAMS:
            print(f"⚠️  Пропущен устаревший параметр: {param}")
            return []
        
        # Особый случай: --dpi-desync
        if param == '--dpi-desync':
            modes = NfqwsConverter.parse_desync_modes(value)
            return [(mode, '') for mode in modes]
        
        # Проверяем маппинг
        if param in NfqwsConverter.PARAM_MAPPING:
            new_param = NfqwsConverter.PARAM_MAPPING[param]
            if new_param:
                return [(new_param, value)]
            else:
                # Параметр обрабатывается отдельно (как --dpi-desync)
                return []
        
        # Для неизвестных параметров пытаемся сохранить
        if param.startswith('--dpi-desync-'):
            # Пробуем удалить префикс dpi-desync-
            new_param = param.replace('--dpi-desync-', '--', 1)
            print(f"⚠️  Параметр {param} передан как есть: {new_param}")
            return [(new_param, value)]
        
        # Все остальные параметры передаём как есть
        return [(param, value)]
    
    @staticmethod
    def convert_config(config_line: str) -> str:
        """Конвертирует одну строку конфигурации"""
        # Удаляем комментарии
        if '#' in config_line:
            config_line = config_line[:config_line.index('#')]
        
        config_line = config_line.strip()
        if not config_line:
            return ''
        
        # Разбиваем на параметры
        parts = []
        current_part = ''
        in_quotes = False
        escape_next = False
        
        for char in config_line:
            if escape_next:
                current_part += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"' or char == "'":
                in_quotes = not in_quotes
                current_part += char
            elif char == ' ' and not in_quotes:
                if current_part:
                    parts.append(current_part)
                    current_part = ''
            else:
                current_part += char
        
        if current_part:
            parts.append(current_part)
        
        # Конвертируем параметры
        converted_parts = []
        i = 0
        while i < len(parts):
            param = parts[i]
            
            # Проверяем, есть ли значение у параметра
            if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                value = parts[i + 1]
                i += 2
            else:
                value = ''
                i += 1
            
            # Конвертируем параметр
            converted = NfqwsConverter.convert_param(param, value)
            for new_param, new_value in converted:
                converted_parts.append(new_param)
                if new_value:
                    converted_parts.append(new_value)
        
        return ' '.join(converted_parts)
    
    @staticmethod
    def convert_file(input_file: str, output_file: str):
        """Конвертирует весь файл конфигурации"""
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        converted_lines = []
        for line_num, line in enumerate(lines, 1):
            try:
                converted = NfqwsConverter.convert_config(line)
                if converted:
                    converted_lines.append(converted)
            except Exception as e:
                print(f"❌ Ошибка в строке {line_num}: {e}")
                print(f"   Строка: {line.strip()}")
                converted_lines.append(f"# Ошибка конвертации: {line.strip()}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(converted_lines))
        
        print(f"✅ Конвертация завершена. Результат в {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Конвертер конфигураций nfqws в nfqws2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --input /etc/nfqws.conf --output /etc/nfqws2.conf
  %(prog)s --string "--hostlist=hosts.list --dpi-desync=fake,multisplit"
        
Базируется на анализе API:
  • nfqws: https://github.com/bol-van/nfqws
  • nfqws2: https://github.com/wfjsw/nfqws2
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', '-i', help='Входной файл конфигурации nfqws')
    group.add_argument('--string', '-s', help='Строка конфигурации для конвертации')
    
    parser.add_argument('--output', '-o', help='Выходной файл для nfqws2')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    
    args = parser.parse_args()
    
    converter = NfqwsConverter()
    
    if args.string:
        converted = converter.convert_config(args.string)
        print("📋 Конвертированная конфигурация:")
        print(converted)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(converted)
            print(f"\n💾 Сохранено в {args.output}")
    
    elif args.input:
        if not args.output:
            parser.error("--output требуется при использовании --input")
        
        converter.convert_file(args.input, args.output)

if __name__ == '__main__':
    main()