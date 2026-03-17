#!/usr/bin/env python3
"""
Скрипт для анализа использования дискового пространства на сервере.
Сканирует все директории и показывает размер каждой папки.
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def format_size(size_bytes):
    """Форматирует размер в удобочитаемый формат"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def bytes_to_mb(size_bytes):
    """Конвертирует байты в мегабайты"""
    return size_bytes / (1024 * 1024)


def get_directory_size(path):
    """Получает размер директории в байтах используя du"""
    try:
        # Используем du для получения размера в байтах
        result = subprocess.run(
            ['du', '-sb', path],
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        if result.returncode == 0:
            size_str = result.stdout.split()[0]
            return int(size_str)
    except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
        print(f"   ⚠️  Ошибка при получении размера {path}: {e}")
    return 0


def scan_directories(root_paths, min_size_mb=0):
    """Сканирует указанные директории и возвращает список с размерами"""
    results = []
    
    for root_path in root_paths:
        root_path = Path(root_path)
        if not root_path.exists():
            print(f"⚠️  Путь не существует: {root_path}")
            continue
        
        print(f"📁 Сканирование {root_path}...")
        
        # Получаем размер корневой директории
        root_size = get_directory_size(str(root_path))
        root_size_mb = bytes_to_mb(root_size)
        
        if root_size_mb >= min_size_mb:
            results.append({
                'path': str(root_path),
                'size_bytes': root_size,
                'size_mb': root_size_mb
            })
        
        # Сканируем поддиректории
        try:
            for item in root_path.iterdir():
                if item.is_dir() and not item.is_symlink():
                    # Пропускаем системные директории, которые могут быть проблемными
                    if item.name in ['proc', 'sys', 'dev']:
                        continue
                    
                    item_path = str(item)
                    print(f"   📂 {item.name}...", end='\r')
                    
                    size = get_directory_size(item_path)
                    size_mb = bytes_to_mb(size)
                    
                    if size_mb >= min_size_mb:
                        results.append({
                            'path': item_path,
                            'size_bytes': size,
                            'size_mb': size_mb
                        })
                    
                    print(f"   ✅ {item.name}: {format_size(size)}" + " " * 20)
        except PermissionError as e:
            print(f"   ⚠️  Нет доступа к {root_path}: {e}")
        except Exception as e:
            print(f"   ⚠️  Ошибка при сканировании {root_path}: {e}")
    
    return results


def get_filesystem_info():
    """Получает информацию о файловой системе"""
    try:
        result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                headers = lines[0].split()
                values = lines[1].split()
                if len(headers) == len(values):
                    info = dict(zip(headers, values))
                    return info
    except Exception as e:
        print(f"⚠️  Ошибка при получении информации о файловой системе: {e}")
    return {}


def main():
    print("=" * 80)
    print("📊 АНАЛИЗ ИСПОЛЬЗОВАНИЯ ДИСКОВОГО ПРОСТРАНСТВА")
    print("=" * 80)
    print()
    
    # Проверяем, запущен ли скрипт от root
    if os.geteuid() != 0:
        print("⚠️  Внимание: Скрипт запущен не от root. Некоторые директории могут быть недоступны.")
        print()
    
    # Получаем информацию о файловой системе
    print("💾 Информация о файловой системе:")
    fs_info = get_filesystem_info()
    if fs_info:
        print(f"   Файловая система: {fs_info.get('Filesystem', 'N/A')}")
        print(f"   Размер: {fs_info.get('Size', 'N/A')}")
        print(f"   Использовано: {fs_info.get('Used', 'N/A')}")
        print(f"   Доступно: {fs_info.get('Avail', 'N/A')}")
        print(f"   Использовано %: {fs_info.get('Use%', 'N/A')}")
        print(f"   Смонтировано в: {fs_info.get('Mounted', 'N/A')}")
    print()
    
    # Директории для сканирования
    root_paths = [
        '/',
        '/root',
        '/opt',
        '/var',
        '/home',
        '/usr',
        '/tmp',
        '/srv',
        '/boot',
        '/etc'
    ]
    
    # Минимальный размер для отображения (в MB)
    min_size_mb = 0  # Показывать все
    
    print("🔍 Начинаем сканирование...")
    print()
    
    results = scan_directories(root_paths, min_size_mb)
    
    # Сортируем по размеру (от большего к меньшему)
    results.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    print()
    print("=" * 80)
    print("📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 80)
    print()
    
    # Группируем результаты по корневым директориям
    grouped = {}
    for item in results:
        root = '/'
        for rp in ['/root', '/opt', '/var', '/home', '/usr', '/tmp', '/srv', '/boot', '/etc']:
            if item['path'].startswith(rp):
                root = rp
                break
        
        if root not in grouped:
            grouped[root] = []
        grouped[root].append(item)
    
    # Выводим результаты
    total_size = 0
    for root in sorted(grouped.keys()):
        items = grouped[root]
        root_total = sum(item['size_bytes'] for item in items)
        total_size += root_total
        
        print(f"\n📁 {root} (всего: {format_size(root_total)})")
        print("-" * 80)
        
        for i, item in enumerate(items[:50], 1):  # Показываем топ-50 для каждой директории
            size_str = format_size(item['size_bytes'])
            size_mb = item['size_mb']
            print(f"{i:3d}. {size_str:>12} ({size_mb:>10.2f} MB)  {item['path']}")
        
        if len(items) > 50:
            print(f"... и еще {len(items) - 50} директорий")
    
    print()
    print("=" * 80)
    print(f"📊 ОБЩИЙ РАЗМЕР ПРОСКАНИРОВАННЫХ ДИРЕКТОРИЙ: {format_size(total_size)}")
    print("=" * 80)
    
    # Сохраняем в файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"disk_usage_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("📊 ОТЧЕТ ОБ ИСПОЛЬЗОВАНИИ ДИСКОВОГО ПРОСТРАНСТВА\n")
        f.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if fs_info:
            f.write("💾 Информация о файловой системе:\n")
            for key, value in fs_info.items():
                f.write(f"   {key}: {value}\n")
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("📊 РЕЗУЛЬТАТЫ АНАЛИЗА\n")
        f.write("=" * 80 + "\n\n")
        
        for root in sorted(grouped.keys()):
            items = grouped[root]
            root_total = sum(item['size_bytes'] for item in items)
            
            f.write(f"\n📁 {root} (всего: {format_size(root_total)})\n")
            f.write("-" * 80 + "\n")
            
            for i, item in enumerate(items, 1):
                size_str = format_size(item['size_bytes'])
                size_mb = item['size_mb']
                f.write(f"{i:3d}. {size_str:>12} ({size_mb:>10.2f} MB)  {item['path']}\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(f"📊 ОБЩИЙ РАЗМЕР ПРОСКАНИРОВАННЫХ ДИРЕКТОРИЙ: {format_size(total_size)}\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n✅ Отчет сохранен в файл: {report_file}")
    print()
    
    # Показываем топ-20 самых больших директорий
    print("=" * 80)
    print("🏆 ТОП-20 САМЫХ БОЛЬШИХ ДИРЕКТОРИЙ")
    print("=" * 80)
    for i, item in enumerate(results[:20], 1):
        size_str = format_size(item['size_bytes'])
        size_mb = item['size_mb']
        print(f"{i:2d}. {size_str:>12} ({size_mb:>10.2f} MB)  {item['path']}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Сканирование прервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

