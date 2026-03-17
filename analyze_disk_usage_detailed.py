#!/usr/bin/env python3
"""
Детальный анализ использования дискового пространства.
Показывает подробную структуру самых больших директорий.
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict


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
        result = subprocess.run(
            ['du', '-sb', path],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            size_str = result.stdout.split()[0]
            return int(size_str)
    except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
        return None
    return None


def analyze_directory_tree(path, max_depth=3, min_size_mb=10):
    """Рекурсивно анализирует дерево директорий"""
    results = []
    path = Path(path)
    
    if not path.exists():
        return results
    
    def scan_recursive(current_path, depth=0):
        if depth > max_depth:
            return
        
        try:
            # Получаем размер текущей директории
            size = get_directory_size(str(current_path))
            if size is None:
                return
            
            size_mb = bytes_to_mb(size)
            
            if size_mb >= min_size_mb:
                results.append({
                    'path': str(current_path),
                    'size_bytes': size,
                    'size_mb': size_mb,
                    'depth': depth
                })
            
            # Если не достигли максимальной глубины, сканируем поддиректории
            if depth < max_depth:
                try:
                    for item in current_path.iterdir():
                        if item.is_dir() and not item.is_symlink():
                            # Пропускаем некоторые системные директории
                            if item.name in ['.git', 'node_modules', '__pycache__', '.cache'] and depth > 0:
                                continue
                            scan_recursive(item, depth + 1)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError) as e:
            pass
    
    scan_recursive(path)
    return results


def analyze_directory_contents(path, top_n=30):
    """Анализирует содержимое директории и показывает топ-N самых больших элементов"""
    path = Path(path)
    if not path.exists():
        return []
    
    results = []
    
    try:
        # Используем du для получения размеров всех элементов
        result = subprocess.run(
            ['du', '-sh', '--max-depth=1', path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            items = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    size_str = parts[0]
                    item_path = parts[1].strip()
                    
                    # Пропускаем саму директорию
                    if item_path == str(path):
                        continue
                    
                    # Конвертируем размер в байты
                    size_bytes = parse_size(size_str)
                    if size_bytes:
                        items.append({
                            'path': item_path,
                            'size_str': size_str,
                            'size_bytes': size_bytes,
                            'size_mb': bytes_to_mb(size_bytes)
                        })
            
            # Сортируем по размеру
            items.sort(key=lambda x: x['size_bytes'], reverse=True)
            results = items[:top_n]
    except Exception as e:
        print(f"   ⚠️  Ошибка при анализе {path}: {e}")
    
    return results


def parse_size(size_str):
    """Парсит размер из строки вида '1.5G', '500M', '2K' в байты"""
    size_str = size_str.strip().upper()
    if not size_str:
        return None
    
    multipliers = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024
    }
    
    # Извлекаем число и единицу
    number_str = ''
    unit = ''
    
    for char in size_str:
        if char.isdigit() or char == '.':
            number_str += char
        else:
            unit = char
            break
    
    if not number_str:
        return None
    
    try:
        number = float(number_str)
        multiplier = multipliers.get(unit, 1)
        return int(number * multiplier)
    except ValueError:
        return None


def get_file_count(path):
    """Подсчитывает количество файлов и директорий"""
    file_count = 0
    dir_count = 0
    
    try:
        for root, dirs, files in os.walk(path):
            file_count += len(files)
            dir_count += len(dirs)
            # Ограничиваем для производительности
            if file_count > 100000:
                break
    except (PermissionError, OSError):
        pass
    
    return file_count, dir_count


def analyze_large_files(path, min_size_mb=100):
    """Находит самые большие файлы в директории"""
    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024
    
    try:
        result = subprocess.run(
            ['find', path, '-type', 'f', '-size', f'+{min_size_mb}M', '-exec', 'du', '-h', '{}', ';'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    size_str = parts[0]
                    file_path = parts[1]
                    size_bytes = parse_size(size_str)
                    if size_bytes:
                        large_files.append({
                            'path': file_path,
                            'size_str': size_str,
                            'size_bytes': size_bytes,
                            'size_mb': bytes_to_mb(size_bytes)
                        })
        
        large_files.sort(key=lambda x: x['size_bytes'], reverse=True)
    except Exception as e:
        pass
    
    return large_files[:50]  # Топ-50


def main():
    print("=" * 100)
    print("📊 ДЕТАЛЬНЫЙ АНАЛИЗ ИСПОЛЬЗОВАНИЯ ДИСКОВОГО ПРОСТРАНСТВА")
    print("=" * 100)
    print()
    
    # Директории для детального анализа
    target_dirs = [
        '/var',
        '/var/www',
        '/var/log',
        '/usr',
        '/opt',
        '/root'
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"disk_usage_detailed_{timestamp}.txt"
    
    report_lines = []
    
    def print_and_save(text):
        print(text)
        report_lines.append(text)
    
    for target_dir in target_dirs:
        path = Path(target_dir)
        if not path.exists():
            print_and_save(f"⚠️  Путь не существует: {target_dir}\n")
            continue
        
        print_and_save("=" * 100)
        print_and_save(f"📁 ДЕТАЛЬНЫЙ АНАЛИЗ: {target_dir}")
        print_and_save("=" * 100)
        print_and_save("")
        
        # Общий размер
        total_size = get_directory_size(str(path))
        if total_size:
            total_mb = bytes_to_mb(total_size)
            print_and_save(f"💾 Общий размер: {format_size(total_size)} ({total_mb:.2f} MB)")
            
            # Количество файлов и директорий
            file_count, dir_count = get_file_count(str(path))
            print_and_save(f"📄 Файлов: {file_count:,} | 📂 Директорий: {dir_count:,}")
            print_and_save("")
        
        # Анализ содержимого (топ-30 самых больших поддиректорий)
        print_and_save("🔍 Топ-30 самых больших поддиректорий:")
        print_and_save("-" * 100)
        contents = analyze_directory_contents(str(path), top_n=30)
        
        if contents:
            for i, item in enumerate(contents, 1):
                rel_path = os.path.relpath(item['path'], str(path))
                if rel_path == '.':
                    rel_path = os.path.basename(item['path'])
                print_and_save(f"{i:2d}. {item['size_str']:>10} ({item['size_mb']:>10.2f} MB)  {rel_path}")
        else:
            print_and_save("   (не удалось получить данные)")
        
        print_and_save("")
        
        # Большие файлы (больше 100 MB)
        print_and_save("📦 Самые большие файлы (>100 MB):")
        print_and_save("-" * 100)
        large_files = analyze_large_files(str(path), min_size_mb=100)
        
        if large_files:
            for i, file_info in enumerate(large_files[:20], 1):  # Топ-20
                rel_path = os.path.relpath(file_info['path'], str(path))
                print_and_save(f"{i:2d}. {file_info['size_str']:>10} ({file_info['size_mb']:>10.2f} MB)  {rel_path}")
        else:
            print_and_save("   (файлов >100 MB не найдено)")
        
        print_and_save("")
        print_and_save("")
        
        # Специальный анализ для /var/log
        if target_dir == '/var/log':
            print_and_save("📋 Детальный анализ логов:")
            print_and_save("-" * 100)
            log_contents = analyze_directory_contents('/var/log', top_n=50)
            if log_contents:
                for i, item in enumerate(log_contents, 1):
                    rel_path = os.path.relpath(item['path'], '/var/log')
                    print_and_save(f"{i:2d}. {item['size_str']:>10} ({item['size_mb']:>10.2f} MB)  {rel_path}")
            print_and_save("")
        
        # Специальный анализ для /var/www
        if target_dir == '/var/www':
            print_and_save("🌐 Детальный анализ веб-проектов:")
            print_and_save("-" * 100)
            www_contents = analyze_directory_contents('/var/www', top_n=50)
            if www_contents:
                for i, item in enumerate(www_contents, 1):
                    rel_path = os.path.relpath(item['path'], '/var/www')
                    # Дополнительный анализ для каждого проекта
                    if item['size_mb'] > 100:
                        sub_contents = analyze_directory_contents(item['path'], top_n=10)
                        print_and_save(f"{i:2d}. {item['size_str']:>10} ({item['size_mb']:>10.2f} MB)  {rel_path}")
                        if sub_contents:
                            for j, sub_item in enumerate(sub_contents[:5], 1):
                                sub_rel = os.path.relpath(sub_item['path'], item['path'])
                                print_and_save(f"    └─ {sub_item['size_str']:>8} ({sub_item['size_mb']:>8.2f} MB)  {sub_rel}")
                    else:
                        print_and_save(f"{i:2d}. {item['size_str']:>10} ({item['size_mb']:>10.2f} MB)  {rel_path}")
            print_and_save("")
        
        # Специальный анализ для /usr
        if target_dir == '/usr':
            print_and_save("📚 Детальный анализ /usr:")
            print_and_save("-" * 100)
            usr_contents = analyze_directory_contents('/usr', top_n=30)
            if usr_contents:
                for i, item in enumerate(usr_contents, 1):
                    rel_path = os.path.relpath(item['path'], '/usr')
                    print_and_save(f"{i:2d}. {item['size_str']:>10} ({item['size_mb']:>10.2f} MB)  {rel_path}")
            print_and_save("")
    
    # Сохраняем отчет
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        f.write('\n')
        f.write("=" * 100 + '\n')
        f.write(f"Отчет создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + '\n')
    
    print_and_save("")
    print_and_save("=" * 100)
    print_and_save(f"✅ Детальный отчет сохранен в файл: {report_file}")
    print_and_save("=" * 100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Анализ прерван пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

