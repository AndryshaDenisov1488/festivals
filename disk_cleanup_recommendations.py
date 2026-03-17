#!/usr/bin/env python3
"""
Анализ использования дискового пространства и рекомендации по очистке.
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
    """Получает размер директории в байтах"""
    try:
        result = subprocess.run(
            ['du', '-sb', path],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            size_str = result.stdout.split()[0]
            return int(size_str)
    except:
        pass
    return None


def analyze_logs():
    """Анализирует логи на предмет очистки"""
    recommendations = []
    total_cleanable = 0
    
    log_dirs = [
        '/var/log',
        '/var/log/nginx',
        '/var/log/apache2',
        '/var/log/syslog',
        '/var/log/auth.log',
        '/var/log/kern.log',
        '/var/log/messages'
    ]
    
    print("📋 Анализ логов...")
    
    # Проверяем старые ротированные логи
    try:
        result = subprocess.run(
            ['find', '/var/log', '-name', '*.log.*', '-type', 'f', '-exec', 'du', '-ch', '{}', '+'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            total_line = [l for l in lines if l.endswith('total')]
            if total_line:
                size_str = total_line[0].split()[0]
                recommendations.append({
                    'category': 'Логи',
                    'description': 'Старые ротированные логи (*.log.*)',
                    'size_str': size_str,
                    'command': 'find /var/log -name "*.log.*" -type f -delete',
                    'safe': True,
                    'note': 'Удалятся только старые ротированные логи, текущие логи останутся'
                })
    except:
        pass
    
    # Проверяем большие логи
    try:
        result = subprocess.run(
            ['find', '/var/log', '-type', 'f', '-size', '+100M', '-exec', 'ls', '-lh', '{}', ';'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0 and result.stdout:
            large_logs = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 9:
                        size = parts[4]
                        file_path = ' '.join(parts[8:])
                        large_logs.append(f"{size} - {file_path}")
            
            if large_logs:
                recommendations.append({
                    'category': 'Логи',
                    'description': 'Очень большие лог-файлы (>100 MB)',
                    'items': large_logs[:10],
                    'command': '# Проверьте каждый файл вручную перед удалением',
                    'safe': False,
                    'note': 'Можно очистить содержимое больших логов: > /var/log/файл.log'
                })
    except:
        pass
    
    return recommendations


def analyze_cache():
    """Анализирует кэш на предмет очистки"""
    recommendations = []
    
    cache_dirs = {
        '/root/.npm': 'npm кэш',
        '/root/.cache': 'Кэш пользователя root',
        '/var/cache': 'Системный кэш',
        '/var/cache/apt': 'APT кэш пакетов',
        '/tmp': 'Временные файлы'
    }
    
    print("🗑️  Анализ кэша...")
    
    for cache_dir, description in cache_dirs.items():
        if os.path.exists(cache_dir):
            size = get_directory_size(cache_dir)
            if size and bytes_to_mb(size) > 50:  # Больше 50 MB
                size_mb = bytes_to_mb(size)
                safe = cache_dir in ['/root/.npm', '/var/cache/apt', '/tmp']
                
                if cache_dir == '/root/.npm':
                    command = 'npm cache clean --force'
                elif cache_dir == '/var/cache/apt':
                    command = 'apt-get clean && apt-get autoclean'
                elif cache_dir == '/tmp':
                    command = 'find /tmp -type f -atime +7 -delete  # Удалить файлы старше 7 дней'
                else:
                    command = f'rm -rf {cache_dir}/*'
                
                recommendations.append({
                    'category': 'Кэш',
                    'description': description,
                    'size_mb': size_mb,
                    'size_str': format_size(size),
                    'command': command,
                    'safe': safe,
                    'note': 'Кэш можно безопасно очистить, он пересоздастся при необходимости'
                })
    
    return recommendations


def analyze_old_packages():
    """Анализирует старые пакеты"""
    recommendations = []
    
    print("📦 Анализ пакетов...")
    
    try:
        # Проверяем размер кэша APT
        result = subprocess.run(
            ['du', '-sh', '/var/cache/apt'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            size_str = result.stdout.split()[0]
            recommendations.append({
                'category': 'Пакеты',
                'description': 'Кэш APT (загруженные .deb файлы)',
                'size_str': size_str,
                'command': 'apt-get clean && apt-get autoclean',
                'safe': True,
                'note': 'Безопасно удалить, пакеты можно скачать заново при необходимости'
            })
    except:
        pass
    
    try:
        # Проверяем неиспользуемые пакеты
        result = subprocess.run(
            ['apt-mark', 'showmanual'],
            capture_output=True,
            text=True
        )
        # Это просто проверка наличия команды
    except:
        pass
    
    return recommendations


def analyze_docker():
    """Анализирует Docker на предмет очистки"""
    recommendations = []
    
    print("🐳 Анализ Docker...")
    
    # Проверяем наличие Docker
    try:
        result = subprocess.run(
            ['which', 'docker'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Проверяем размер Docker данных
            docker_dirs = ['/var/lib/docker']
            for docker_dir in docker_dirs:
                if os.path.exists(docker_dir):
                    size = get_directory_size(docker_dir)
                    if size and bytes_to_mb(size) > 100:
                        size_mb = bytes_to_mb(size)
                        recommendations.append({
                            'category': 'Docker',
                            'description': 'Docker данные (образы, контейнеры, volumes)',
                            'size_mb': size_mb,
                            'size_str': format_size(size),
                            'command': 'docker system prune -a --volumes',
                            'safe': False,
                            'note': '⚠️  Удалит неиспользуемые образы, контейнеры и volumes. Проверьте перед выполнением!'
                        })
    except:
        pass
    
    return recommendations


def analyze_tmp_files():
    """Анализирует временные файлы"""
    recommendations = []
    
    print("📁 Анализ временных файлов...")
    
    tmp_dirs = ['/tmp', '/var/tmp']
    
    for tmp_dir in tmp_dirs:
        if os.path.exists(tmp_dir):
            size = get_directory_size(tmp_dir)
            if size and bytes_to_mb(size) > 50:
                size_mb = bytes_to_mb(size)
                
                # Проверяем старые файлы
                try:
                    result = subprocess.run(
                        ['find', tmp_dir, '-type', 'f', '-atime', '+7', '-exec', 'du', '-ch', '{}', '+'],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    old_files_note = ''
                    if result.returncode == 0 and result.stdout:
                        total_line = [l for l in result.stdout.strip().split('\n') if l.endswith('total')]
                        if total_line:
                            old_size = total_line[0].split()[0]
                            old_files_note = f' (файлы старше 7 дней: {old_size})'
                except:
                    old_files_note = ''
                
                recommendations.append({
                    'category': 'Временные файлы',
                    'description': f'{tmp_dir}',
                    'size_mb': size_mb,
                    'size_str': format_size(size),
                    'command': f'find {tmp_dir} -type f -atime +7 -delete  # Удалить файлы старше 7 дней',
                    'safe': True,
                    'note': f'Можно безопасно удалить старые файлы{old_files_note}'
                })
    
    return recommendations


def main():
    print("=" * 100)
    print("🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ ПО ОЧИСТКЕ ДИСКОВОГО ПРОСТРАНСТВА")
    print("=" * 100)
    print()
    
    all_recommendations = []
    
    # Собираем все рекомендации
    all_recommendations.extend(analyze_logs())
    all_recommendations.extend(analyze_cache())
    all_recommendations.extend(analyze_old_packages())
    all_recommendations.extend(analyze_docker())
    all_recommendations.extend(analyze_tmp_files())
    
    # Группируем по категориям
    by_category = {}
    for rec in all_recommendations:
        cat = rec['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rec)
    
    # Выводим рекомендации
    print()
    print("=" * 100)
    print("📊 РЕКОМЕНДАЦИИ ПО ОЧИСТКЕ")
    print("=" * 100)
    print()
    
    total_safe_mb = 0
    total_unsafe_mb = 0
    
    for category in sorted(by_category.keys()):
        print(f"\n{'='*100}")
        print(f"📁 {category.upper()}")
        print(f"{'='*100}\n")
        
        for i, rec in enumerate(by_category[category], 1):
            size_info = rec.get('size_str', rec.get('size_mb', 'N/A'))
            if isinstance(size_info, float):
                size_info = f"{size_info:.2f} MB"
            
            safe_icon = "✅" if rec.get('safe', False) else "⚠️"
            print(f"{safe_icon} {i}. {rec['description']}")
            print(f"   Размер: {size_info}")
            print(f"   Команда: {rec['command']}")
            print(f"   Примечание: {rec.get('note', '')}")
            
            if 'items' in rec:
                print("   Детали:")
                for item in rec['items'][:5]:
                    print(f"      - {item}")
            
            print()
            
            # Подсчитываем размеры
            if 'size_mb' in rec:
                if rec.get('safe', False):
                    total_safe_mb += rec['size_mb']
                else:
                    total_unsafe_mb += rec['size_mb']
    
    # Итоговая сводка
    print()
    print("=" * 100)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("=" * 100)
    print()
    print(f"✅ Безопасно можно освободить: ~{total_safe_mb:.2f} MB ({format_size(total_safe_mb * 1024 * 1024)})")
    print(f"⚠️  Требует проверки перед очисткой: ~{total_unsafe_mb:.2f} MB ({format_size(total_unsafe_mb * 1024 * 1024)})")
    print()
    
    # Общие рекомендации
    print("=" * 100)
    print("💡 ОБЩИЕ РЕКОМЕНДАЦИИ")
    print("=" * 100)
    print()
    print("1. 🔴 КРИТИЧЕСКИ ВАЖНО:")
    print("   - /var/log (3.20 GB) - можно очистить старые ротированные логи")
    print("   - /root/.npm (497 MB) - npm кэш можно безопасно очистить")
    print("   - /root/.cache (276 MB) - кэш можно очистить")
    print("   - /tmp/judges_documents (183 MB) - временные файлы, можно удалить старые")
    print()
    print("2. 🟡 ТРЕБУЕТ ВНИМАНИЯ:")
    print("   - /var/www (12.29 GB) - проверьте, нет ли там старых бэкапов, логов, кэша")
    print("   - /var/log - проверьте большие лог-файлы, возможно их нужно ротировать")
    print()
    print("3. 🟢 ОБЫЧНО БЕЗОПАСНО:")
    print("   - APT кэш (/var/cache/apt) - можно очистить")
    print("   - Старые временные файлы в /tmp")
    print("   - Ротированные логи (*.log.*)")
    print()
    
    # Сохраняем отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cleanup_recommendations_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ ПО ОЧИСТКЕ ДИСКОВОГО ПРОСТРАНСТВА\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")
        
        for category in sorted(by_category.keys()):
            f.write(f"\n{'='*100}\n")
            f.write(f"📁 {category.upper()}\n")
            f.write(f"{'='*100}\n\n")
            
            for i, rec in enumerate(by_category[category], 1):
                size_info = rec.get('size_str', rec.get('size_mb', 'N/A'))
                if isinstance(size_info, float):
                    size_info = f"{size_info:.2f} MB"
                
                safe_icon = "✅" if rec.get('safe', False) else "⚠️"
                f.write(f"{safe_icon} {i}. {rec['description']}\n")
                f.write(f"   Размер: {size_info}\n")
                f.write(f"   Команда: {rec['command']}\n")
                f.write(f"   Примечание: {rec.get('note', '')}\n\n")
        
        f.write(f"\n✅ Безопасно можно освободить: ~{total_safe_mb:.2f} MB\n")
        f.write(f"⚠️  Требует проверки: ~{total_unsafe_mb:.2f} MB\n")
    
    print(f"✅ Отчет сохранен в файл: {report_file}")
    print()


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


