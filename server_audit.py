#!/usr/bin/env python3
"""
Глубокий анализ сервера Linux.
Собирает информацию о сервисах, портах, процессах, проектах и безопасности.
"""

import os
import sys
import subprocess
import json
import socket
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class ServerAuditor:
    def __init__(self):
        self.report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': {},
            'services': {},
            'ports': {},
            'processes': {},
            'projects': {},
            'security': {},
            'network': {},
            'storage': {},
            'users': {},
            'cron': {},
            'errors': []
        }
    
    def run_command(self, cmd, shell=False, capture_stderr=True):
        """Выполняет команду и возвращает результат"""
        try:
            if isinstance(cmd, str) and not shell:
                cmd = cmd.split()
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30,
                stderr=subprocess.STDOUT if capture_stderr else subprocess.PIPE
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if not capture_stderr else None,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': 'Timeout', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e), 'returncode': -1}
    
    def get_system_info(self):
        """Собирает информацию о системе"""
        print("📊 Сбор информации о системе...")
        
        info = {}
        
        # OS информация
        result = self.run_command('uname -a')
        if result['success']:
            info['uname'] = result['output'].strip()
        
        # Версия ОС
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                info['os_release'] = {}
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        info['os_release'][key] = value.strip('"')
        
        # Uptime
        result = self.run_command('uptime')
        if result['success']:
            info['uptime'] = result['output'].strip()
        
        # CPU информация
        result = self.run_command('lscpu')
        if result['success']:
            info['cpu'] = {}
            for line in result['output'].split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info['cpu'][key.strip()] = value.strip()
        
        # Memory
        result = self.run_command('free -h')
        if result['success']:
            info['memory'] = result['output'].strip()
        
        # Disk usage
        result = self.run_command('df -h')
        if result['success']:
            info['disk_usage'] = result['output'].strip()
        
        self.report['system_info'] = info
    
    def get_services(self):
        """Собирает информацию о systemd сервисах"""
        print("🔧 Анализ systemd сервисов...")
        
        services = {
            'active': [],
            'inactive': [],
            'failed': [],
            'enabled': [],
            'disabled': [],
            'running': [],
            'details': {},
            'raw_output': {}
        }
        
        # Метод 1: Используем --no-legend для чистого вывода
        result = self.run_command('systemctl list-units --type=service --state=running --no-pager --no-legend')
        if result['success']:
            services['raw_output']['running'] = result['output'][:1000]  # Сохраняем первые 1000 символов
            for line in result['output'].split('\n'):
                line = line.strip()
                if line and '.service' in line:
                    # Формат: service-name.service    loaded active running Description
                    # Ищем первое слово, которое заканчивается на .service
                    parts = line.split()
                    if parts:
                        # Первое слово должно быть именем сервиса
                        service_name = parts[0]
                        if service_name.endswith('.service'):
                            if service_name not in services['active']:
                                services['active'].append(service_name)
                                services['running'].append(service_name)
        
        # Метод 2: Все активные сервисы (не только running)
        result = self.run_command('systemctl list-units --type=service --state=active --no-pager --no-legend')
        if result['success']:
            services['raw_output']['active'] = result['output'][:1000]
            for line in result['output'].split('\n'):
                line = line.strip()
                if line and '.service' in line:
                    parts = line.split()
                    if parts:
                        service_name = parts[0]
                        if service_name.endswith('.service'):
                            if service_name not in services['active']:
                                services['active'].append(service_name)
        
        # Метод 3: Все сервисы (включая неактивные)
        result = self.run_command('systemctl list-units --type=service --all --no-pager --no-legend')
        if result['success']:
            for line in result['output'].split('\n'):
                line = line.strip()
                if line and '.service' in line:
                    parts = line.split(None, 4)
                    if len(parts) >= 3:
                        service_name = parts[0]
                        if not service_name.endswith('.service'):
                            continue
                        load_state = parts[1] if len(parts) > 1 else ''
                        active_state = parts[2] if len(parts) > 2 else ''
                        
                        if active_state == 'active':
                            if service_name not in services['active']:
                                services['active'].append(service_name)
                        elif active_state == 'inactive':
                            if service_name not in services['inactive']:
                                services['inactive'].append(service_name)
                        elif active_state == 'failed':
                            if service_name not in services['failed']:
                                services['failed'].append(service_name)
        
        # Метод 4: Получаем список всех сервисов и их статус enabled/disabled
        result = self.run_command('systemctl list-unit-files --type=service --no-pager --no-legend')
        all_services = []
        if result['success']:
            for line in result['output'].split('\n'):
                line = line.strip()
                if line and '.service' in line:
                    parts = line.split()
                    if parts and parts[0].endswith('.service'):
                        service_name = parts[0]
                        all_services.append(service_name)
                        enabled = parts[1] if len(parts) > 1 else ''
                        if enabled == 'enabled':
                            if service_name not in services['enabled']:
                                services['enabled'].append(service_name)
                        elif enabled == 'disabled':
                            if service_name not in services['disabled']:
                                services['disabled'].append(service_name)
        
        # Метод 5: Проверяем через is-active для всех сервисов (но ограничиваем для скорости)
        if len(services['active']) == 0 and len(all_services) > 0:
            print(f"   Альтернативная проверка через is-active для {min(len(all_services), 200)} сервисов...")
            checked = 0
            for service in all_services[:200]:  # Проверяем первые 200
                result = self.run_command(f'systemctl is-active {service} 2>/dev/null')
                if result['success']:
                    status = result['output'].strip()
                    if status == 'active':
                        if service not in services['active']:
                            services['active'].append(service)
                            services['running'].append(service)
                checked += 1
                if checked % 50 == 0:
                    print(f"      Проверено {checked}/{min(len(all_services), 200)}...")
        
        # Метод 6: Прямой поиск через systemctl status для известных сервисов
        known_services = ['judges-bot', 'nginx', 'postgresql', 'mysql', 'apache2', 'docker']
        for service_name in known_services:
            result = self.run_command(f'systemctl is-active {service_name} 2>/dev/null')
            if result['success'] and result['output'].strip() == 'active':
                full_name = f'{service_name}.service'
                if full_name not in services['active']:
                    services['active'].append(full_name)
                    if full_name not in services['running']:
                        services['running'].append(full_name)
        
        # Детальная информация о каждом активном сервисе (ограничиваем до 30 для скорости)
        if services['active']:
            print(f"   Сбор детальной информации о {min(len(services['active']), 30)} активных сервисах...")
            for service in services['active'][:30]:
                result = self.run_command(f'systemctl show {service} --property=ExecStart,WorkingDirectory,User,MainPID,ActiveState,SubState --no-pager 2>/dev/null')
                if result['success']:
                    service_info = {}
                    for line in result['output'].split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key == 'ExecStart':
                                service_info['exec_start'] = value.strip()
                            elif key == 'WorkingDirectory':
                                service_info['working_directory'] = value.strip()
                            elif key == 'User':
                                service_info['user'] = value.strip()
                            elif key == 'MainPID':
                                service_info['pid'] = value.strip()
                            elif key == 'ActiveState':
                                service_info['active_state'] = value.strip()
                            elif key == 'SubState':
                                service_info['sub_state'] = value.strip()
                    
                    if service_info:
                        services['details'][service] = service_info
        
        self.report['services'] = services
    
    def get_ports(self):
        """Собирает информацию о занятых портах"""
        print("🔌 Анализ портов...")
        
        ports = {
            'listening': [],
            'established': [],
            'by_process': defaultdict(list),
            'by_port': {}
        }
        
        # Используем ss (более современный)
        result = self.run_command('ss -tulpn 2>/dev/null')
        if not result['success']:
            result = self.run_command('netstat -tulpn 2>/dev/null')
        
        if result['success']:
            lines = result['output'].split('\n')
            # Пропускаем заголовок
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    proto = parts[0].upper()
                    state = parts[1].upper() if len(parts) > 1 else ''
                    local_addr = parts[4] if len(parts) > 4 else ''
                    process_info = ' '.join(parts[5:]) if len(parts) > 5 else ''
                    
                    # Извлекаем PID и имя процесса
                    pid = None
                    process_name = 'unknown'
                    if 'pid=' in process_info:
                        try:
                            pid_part = process_info.split('pid=')[1].split(',')[0]
                            pid = int(pid_part)
                        except:
                            pass
                    if 'users:' in process_info:
                        try:
                            users_part = process_info.split('users:')[1].strip()
                            # Формат: (("python3",pid=123,fd=3))
                            if '(' in users_part and ')' in users_part:
                                process_name = users_part.split('"')[1] if '"' in users_part else 'unknown'
                        except:
                            pass
                    
                    if 'LISTEN' in state or state == 'LISTEN':
                        port_info = {
                            'protocol': proto,
                            'address': local_addr,
                            'state': state,
                            'process': process_name,
                            'pid': pid,
                            'full_info': process_info
                        }
                        ports['listening'].append(port_info)
                        
                        # Извлекаем порт
                        if ':' in local_addr:
                            try:
                                addr_part = local_addr.split(':')[-1]
                                if addr_part:
                                    port = int(addr_part)
                                    ports['by_port'][port] = port_info
                                    ports['by_process'][process_name].append({
                                        'port': port,
                                        'protocol': proto,
                                        'address': local_addr,
                                        'pid': pid
                                    })
                            except:
                                pass
        
        # Дополнительная проверка через lsof (если доступен)
        result = self.run_command('lsof -i -P -n 2>/dev/null | head -200')
        if result['success']:
            ports['lsof_info'] = result['output'].strip()
            # Парсим lsof для дополнительной информации
            for line in result['output'].split('\n')[1:]:
                if 'LISTEN' in line or 'ESTABLISHED' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        process_name = parts[0]
                        pid = parts[1]
                        protocol = parts[7] if len(parts) > 7 else ''
                        address = parts[8] if len(parts) > 8 else ''
                        
                        if 'LISTEN' in line and address:
                            # Проверяем, нет ли уже этого порта
                            if ':' in address:
                                try:
                                    port = int(address.split(':')[-1])
                                    if port not in ports['by_port']:
                                        ports['listening'].append({
                                            'protocol': protocol,
                                            'address': address,
                                            'state': 'LISTEN',
                                            'process': process_name,
                                            'pid': pid,
                                            'source': 'lsof'
                                        })
                                except:
                                    pass
        
        # Также проверяем через /proc/net
        try:
            if os.path.exists('/proc/net/tcp'):
                with open('/proc/net/tcp', 'r') as f:
                    for line in f.readlines()[1:]:  # Пропускаем заголовок
                        parts = line.split()
                        if len(parts) >= 2:
                            local_addr = parts[1]
                            state = parts[3] if len(parts) > 3 else ''
                            # state 0A = LISTEN
                            if state == '0A':
                                # Формат: 0100007F:1F90 (hex)
                                if ':' in local_addr:
                                    try:
                                        port_hex = local_addr.split(':')[1]
                                        port = int(port_hex, 16)
                                        if port not in ports['by_port']:
                                            ports['listening'].append({
                                                'protocol': 'TCP',
                                                'address': f'*:{port}',
                                                'state': 'LISTEN',
                                                'process': 'unknown',
                                                'source': '/proc/net/tcp'
                                            })
                                    except:
                                        pass
        except:
            pass
        
        self.report['ports'] = ports
    
    def get_processes(self):
        """Собирает информацию о процессах"""
        print("⚙️  Анализ процессов...")
        
        processes = {
            'by_user': defaultdict(list),
            'python': [],
            'node': [],
            'nginx': [],
            'apache': [],
            'mysql': [],
            'postgresql': [],
            'postgres': [],
            'docker': [],
            'total': 0,
            'raw_output': ''
        }
        
        # Метод 1: ps aux (основной)
        result = self.run_command('ps auxww')
        if result['success']:
            processes['raw_output'] = result['output'][:5000]  # Сохраняем первые 5000 символов
            lines = result['output'].split('\n')
            
            for line in lines[1:]:  # Пропускаем заголовок
                if not line.strip():
                    continue
                
                # Более гибкий парсинг
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    user = parts[0]
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    vsz = parts[4]
                    rss = parts[5]
                    tty = parts[6]
                    stat = parts[7]
                    start = parts[8]
                    time = parts[9]
                    command = ' '.join(parts[10:])
                    
                    process_info = {
                        'pid': pid,
                        'user': user,
                        'cpu': cpu,
                        'mem': mem,
                        'vsz': vsz,
                        'rss': rss,
                        'command': command[:200]  # Ограничиваем длину команды
                    }
                    
                    processes['by_user'][user].append(process_info)
                    processes['total'] += 1
                    
                    # Категоризация (более точная)
                    cmd_lower = command.lower()
                    cmd_parts = cmd_lower.split()
                    
                    # Python процессы - более точная проверка
                    python_keywords = ['python', 'python3', 'python2', '.py', 'pypy', 'pip']
                    if any(keyword in cmd_lower for keyword in python_keywords):
                        # Проверяем, что это не просто упоминание в пути
                        if any(cmd_lower.startswith(x) or f'/{x}' in cmd_lower or f'\\{x}' in cmd_lower 
                               for x in ['python', 'python3', 'python2']) or '.py' in cmd_lower:
                            if process_info not in processes['python']:
                                processes['python'].append(process_info)
                    
                    # Node.js процессы
                    if any(x in cmd_lower for x in ['node', 'npm', 'nodejs', 'pm2', 'yarn']):
                        if process_info not in processes['node']:
                            processes['node'].append(process_info)
                    
                    # Nginx
                    if 'nginx' in cmd_lower:
                        if process_info not in processes['nginx']:
                            processes['nginx'].append(process_info)
                    
                    # Apache
                    if any(x in cmd_lower for x in ['apache', 'httpd']):
                        if process_info not in processes['apache']:
                            processes['apache'].append(process_info)
                    
                    # MySQL/MariaDB
                    if any(x in cmd_lower for x in ['mysql', 'mariadb', 'mysqld']):
                        if process_info not in processes['mysql']:
                            processes['mysql'].append(process_info)
                    
                    # PostgreSQL
                    if any(x in cmd_lower for x in ['postgres', 'postgresql', 'postmaster']):
                        if process_info not in processes['postgresql']:
                            processes['postgresql'].append(process_info)
                        if 'postgres' in cmd_lower and process_info not in processes['postgres']:
                            processes['postgres'].append(process_info)
                    
                    # Docker
                    if any(x in cmd_lower for x in ['docker', 'dockerd', 'containerd']):
                        if process_info not in processes['docker']:
                            processes['docker'].append(process_info)
        
        # Метод 2: Дополнительная проверка через pgrep для Python
        print("   Дополнительная проверка Python процессов через pgrep...")
        for python_cmd in ['python3', 'python', 'python2']:
            result = self.run_command(f'pgrep -af {python_cmd}')
            if result['success'] and result['output'].strip():
                for line in result['output'].split('\n'):
                    line = line.strip()
                    if line:
                        # Формат: PID команда
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            pid = parts[0]
                            command = parts[1]
                            
                            # Проверяем, нет ли уже этого процесса
                            if not any(p['pid'] == pid for p in processes['python']):
                                process_info = {
                                    'pid': pid,
                                    'user': 'unknown',
                                    'cpu': '0.0',
                                    'mem': '0.0',
                                    'vsz': '0',
                                    'rss': '0',
                                    'command': command[:200],
                                    'source': 'pgrep'
                                }
                                processes['python'].append(process_info)
        
        # Метод 3: Проверка через /proc
        print("   Проверка процессов через /proc...")
        try:
            for pid_dir in os.listdir('/proc'):
                if pid_dir.isdigit():
                    pid = pid_dir
                    try:
                        # Читаем cmdline
                        cmdline_path = f'/proc/{pid}/cmdline'
                        if os.path.exists(cmdline_path):
                            with open(cmdline_path, 'r') as f:
                                cmdline = f.read().replace('\x00', ' ').strip()
                                if cmdline:
                                    cmd_lower = cmdline.lower()
                                    
                                    # Проверяем Python
                                    if any(x in cmd_lower for x in ['python', 'python3', '.py']):
                                        if not any(p['pid'] == pid for p in processes['python']):
                                            process_info = {
                                                'pid': pid,
                                                'user': 'unknown',
                                                'cpu': '0.0',
                                                'mem': '0.0',
                                                'vsz': '0',
                                                'rss': '0',
                                                'command': cmdline[:200],
                                                'source': '/proc'
                                            }
                                            processes['python'].append(process_info)
                    except:
                        pass
        except:
            pass
        
        self.report['processes'] = processes
    
    def scan_directory(self, path, max_depth=3, current_depth=0):
        """Рекурсивно сканирует директорию"""
        projects = []
        
        if not os.path.exists(path) or not os.path.isdir(path):
            return projects
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                # Пропускаем системные директории
                if item.startswith('.') and item not in ['.git', '.env']:
                    continue
                
                if os.path.isdir(item_path) and current_depth < max_depth:
                    # Проверяем, является ли это проектом
                    project_indicators = [
                        'requirements.txt', 'package.json', 'composer.json',
                        'Dockerfile', '.git', 'main.py', 'app.py', 'index.php',
                        'config.py', 'settings.py', '.env'
                    ]
                    
                    is_project = False
                    project_type = 'unknown'
                    project_files = []
                    
                    try:
                        for indicator in project_indicators:
                            indicator_path = os.path.join(item_path, indicator)
                            if os.path.exists(indicator_path):
                                is_project = True
                                project_files.append(indicator)
                                
                                if indicator == 'requirements.txt' or indicator == 'main.py' or indicator == 'config.py':
                                    project_type = 'python'
                                elif indicator == 'package.json':
                                    project_type = 'nodejs'
                                elif indicator == 'composer.json':
                                    project_type = 'php'
                                elif indicator == 'Dockerfile':
                                    project_type = 'docker'
                    except:
                        pass
                    
                    if is_project:
                        # Получаем размер
                        size = 0
                        file_count = 0
                        try:
                            for root, dirs, files in os.walk(item_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    try:
                                        size += os.path.getsize(file_path)
                                        file_count += 1
                                    except:
                                        pass
                        except:
                            pass
                        
                        projects.append({
                            'path': item_path,
                            'name': item,
                            'type': project_type,
                            'size_mb': round(size / 1024 / 1024, 2),
                            'files': project_files,
                            'file_count': file_count
                        })
                    else:
                        # Рекурсивно сканируем поддиректории
                        if current_depth < max_depth - 1:
                            projects.extend(self.scan_directory(item_path, max_depth, current_depth + 1))
        
        except PermissionError:
            pass
        except Exception as e:
            self.report['errors'].append(f"Ошибка при сканировании {path}: {e}")
        
        return projects
    
    def get_projects(self):
        """Сканирует директории на наличие проектов"""
        print("📁 Поиск проектов...")
        
        projects = {
            '/root': [],
            '/opt': [],
            '/var': [],
            '/home': []
        }
        
        # Сканируем основные директории
        for directory in ['/root', '/opt', '/var', '/home']:
            if os.path.exists(directory):
                print(f"   Сканирование {directory}...")
                found = self.scan_directory(directory, max_depth=3)
                projects[directory] = found
        
        # Дополнительно проверяем /var/www
        if os.path.exists('/var/www'):
            found = self.scan_directory('/var/www', max_depth=2)
            projects['/var/www'] = found
        
        self.report['projects'] = projects
    
    def get_security_info(self):
        """Собирает информацию о безопасности"""
        print("🔒 Анализ безопасности...")
        
        security = {
            'firewall': {},
            'ssh': {},
            'users': {},
            'sudo': {},
            'fail2ban': {},
            'updates': {}
        }
        
        # Firewall (ufw/iptables)
        result = self.run_command('ufw status verbose')
        if result['success']:
            security['firewall']['ufw'] = result['output'].strip()
        else:
            result = self.run_command('iptables -L -n -v')
            if result['success']:
                security['firewall']['iptables'] = result['output'].strip()[:1000]  # Первые 1000 символов
        
        # SSH конфигурация
        if os.path.exists('/etc/ssh/sshd_config'):
            with open('/etc/ssh/sshd_config', 'r') as f:
                ssh_config = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ' ' in line or '\t' in line:
                            parts = line.split(None, 1)
                            if len(parts) == 2:
                                key = parts[0].lower()
                                value = parts[1]
                                ssh_config[key] = value
                security['ssh']['config'] = ssh_config
        
        # SSH ключи
        if os.path.exists('/root/.ssh'):
            authorized_keys = []
            if os.path.exists('/root/.ssh/authorized_keys'):
                with open('/root/.ssh/authorized_keys', 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            authorized_keys.append(line.strip()[:100])  # Первые 100 символов
            security['ssh']['authorized_keys_count'] = len(authorized_keys)
            security['ssh']['authorized_keys'] = authorized_keys[:10]  # Первые 10
        
        # Пользователи с sudo
        result = self.run_command('getent group sudo')
        if result['success']:
            security['sudo']['group_members'] = result['output'].strip()
        
        # Fail2ban
        result = self.run_command('systemctl status fail2ban --no-pager')
        if result['success']:
            security['fail2ban']['status'] = result['output'].strip()[:500]
        
        # Обновления системы
        result = self.run_command('apt list --upgradable 2>/dev/null | head -20')
        if result['success']:
            security['updates']['available'] = result['output'].strip()
        
        self.report['security'] = security
    
    def get_network_info(self):
        """Собирает сетевую информацию"""
        print("🌐 Анализ сети...")
        
        network = {
            'interfaces': {},
            'routes': {},
            'dns': {}
        }
        
        # Сетевые интерфейсы
        result = self.run_command('ip addr show')
        if result['success']:
            network['interfaces']['ip_addr'] = result['output'].strip()
        
        # Маршруты
        result = self.run_command('ip route show')
        if result['success']:
            network['routes'] = result['output'].strip()
        
        # DNS
        if os.path.exists('/etc/resolv.conf'):
            with open('/etc/resolv.conf', 'r') as f:
                network['dns']['resolv_conf'] = f.read().strip()
        
        self.report['network'] = network
    
    def get_storage_info(self):
        """Собирает информацию о хранилище"""
        print("💾 Анализ хранилища...")
        
        storage = {}
        
        # Разделы дисков
        result = self.run_command('lsblk')
        if result['success']:
            storage['block_devices'] = result['output'].strip()
        
        # Использование дисков
        result = self.run_command('df -h')
        if result['success']:
            storage['disk_usage'] = result['output'].strip()
        
        # Inode usage
        result = self.run_command('df -i')
        if result['success']:
            storage['inode_usage'] = result['output'].strip()
        
        self.report['storage'] = storage
    
    def get_users_info(self):
        """Собирает информацию о пользователях"""
        print("👥 Анализ пользователей...")
        
        users = {
            'all': [],
            'with_shell': [],
            'recent_login': {}
        }
        
        # Все пользователи
        result = self.run_command('getent passwd')
        if result['success']:
            for line in result['output'].split('\n'):
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        uid = parts[2]
                        gid = parts[3]
                        home = parts[5]
                        shell = parts[6]
                        
                        user_info = {
                            'username': username,
                            'uid': uid,
                            'gid': gid,
                            'home': home,
                            'shell': shell
                        }
                        
                        users['all'].append(user_info)
                        
                        if shell not in ['/usr/sbin/nologin', '/bin/false', '/sbin/nologin']:
                            users['with_shell'].append(username)
        
        # Последние логины
        result = self.run_command('lastlog | head -20')
        if result['success']:
            users['recent_login']['lastlog'] = result['output'].strip()
        
        self.report['users'] = users
    
    def get_disk_usage(self, min_size_mb=300):
        """Анализирует использование дискового пространства"""
        print(f"💾 Анализ дискового пространства (показываем > {min_size_mb} МБ)...")
        
        disk_usage = {
            'large_directories': [],
            'by_path': {},
            'total_size_gb': 0,
            'summary': {},
            'root_directories': []
        }
        
        # Основные директории для анализа
        scan_paths = ['/root', '/opt', '/var', '/home', '/usr', '/tmp', '/var/log']
        
        for scan_path in scan_paths:
            if not os.path.exists(scan_path):
                continue
            
            print(f"   Анализ {scan_path}...")
            
            # Используем du для быстрого анализа
            result = self.run_command(f'du -sh {scan_path}/* 2>/dev/null | sort -hr | head -50')
            if result['success']:
                for line in result['output'].split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Формат: SIZE PATH
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        size_str = parts[0]
                        path = parts[1]
                        
                        # Парсим размер
                        size_mb = 0
                        try:
                            if size_str.endswith('G'):
                                size_mb = float(size_str[:-1]) * 1024
                            elif size_str.endswith('M'):
                                size_mb = float(size_str[:-1])
                            elif size_str.endswith('K'):
                                size_mb = float(size_str[:-1]) / 1024
                            else:
                                # Предполагаем байты
                                size_mb = float(size_str) / 1024 / 1024
                        except:
                            continue
                        
                        if size_mb >= min_size_mb:
                            disk_usage['large_directories'].append({
                                'path': path,
                                'size_mb': round(size_mb, 2),
                                'size_str': size_str,
                                'parent': scan_path
                            })
                            
                            # Группируем по родительским путям
                            if scan_path not in disk_usage['by_path']:
                                disk_usage['by_path'][scan_path] = []
                            disk_usage['by_path'][scan_path].append({
                                'path': path,
                                'size_mb': round(size_mb, 2),
                                'size_str': size_str
                            })
        
        # Сортируем по размеру
        disk_usage['large_directories'].sort(key=lambda x: x['size_mb'], reverse=True)
        
        # Подсчитываем общий размер
        total_size_mb = sum(item['size_mb'] for item in disk_usage['large_directories'])
        disk_usage['total_size_gb'] = round(total_size_mb / 1024, 2)
        
        # Сводка по путям
        for path, items in disk_usage['by_path'].items():
            total_path_mb = sum(item['size_mb'] for item in items)
            disk_usage['summary'][path] = {
                'total_mb': round(total_path_mb, 2),
                'total_gb': round(total_path_mb / 1024, 2),
                'count': len(items)
            }
        
        # Дополнительно: анализ корневых директорий
        result = self.run_command('du -sh /* 2>/dev/null | sort -hr | head -20')
        if result['success']:
            for line in result['output'].split('\n'):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    size_str = parts[0]
                    path = parts[1]
                    
                    # Парсим размер
                    size_mb = 0
                    try:
                        if size_str.endswith('G'):
                            size_mb = float(size_str[:-1]) * 1024
                        elif size_str.endswith('M'):
                            size_mb = float(size_str[:-1])
                        elif size_str.endswith('K'):
                            size_mb = float(size_str[:-1]) / 1024
                        else:
                            size_mb = float(size_str) / 1024 / 1024
                    except:
                        continue
                    
                    if size_mb >= min_size_mb:
                        disk_usage['root_directories'].append({
                            'path': path,
                            'size_mb': round(size_mb, 2),
                            'size_str': size_str
                        })
        
        # Сортируем корневые директории
        disk_usage['root_directories'].sort(key=lambda x: x['size_mb'], reverse=True)
        
        self.report['disk_usage'] = disk_usage
    
    def get_cron_info(self):
        """Собирает информацию о cron задачах"""
        print("⏰ Анализ cron задач...")
        
        cron = {
            'root_crontab': '',
            'system_cron': [],
            'user_crontabs': []
        }
        
        # Root crontab
        result = self.run_command('crontab -l', shell=True)
        if result['success']:
            cron['root_crontab'] = result['output'].strip()
        
        # System cron
        cron_dirs = ['/etc/cron.d', '/etc/cron.daily', '/etc/cron.hourly', '/etc/cron.weekly', '/etc/cron.monthly']
        for cron_dir in cron_dirs:
            if os.path.exists(cron_dir):
                try:
                    files = os.listdir(cron_dir)
                    cron['system_cron'].append({
                        'directory': cron_dir,
                        'files': files
                    })
                except:
                    pass
        
        self.report['cron'] = cron
    
    def generate_report(self, output_file='server_audit_report.txt'):
        """Генерирует текстовый отчет"""
        print(f"\n📄 Генерация отчета: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ОТЧЕТ ОБ АУДИТЕ СЕРВЕРА\n")
            f.write(f"Дата: {self.report['timestamp']}\n")
            f.write("=" * 80 + "\n\n")
            
            # Системная информация
            f.write("=" * 80 + "\n")
            f.write("1. СИСТЕМНАЯ ИНФОРМАЦИЯ\n")
            f.write("=" * 80 + "\n\n")
            for key, value in self.report['system_info'].items():
                f.write(f"{key.upper()}:\n")
                if isinstance(value, dict):
                    for k, v in value.items():
                        f.write(f"  {k}: {v}\n")
                else:
                    f.write(f"{value}\n")
                f.write("\n")
            
            # Сервисы
            f.write("=" * 80 + "\n")
            f.write("2. SYSTEMD СЕРВИСЫ\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Активных сервисов: {len(self.report['services'].get('active', []))}\n")
            f.write(f"Неактивных сервисов: {len(self.report['services'].get('inactive', []))}\n")
            f.write(f"Упавших сервисов: {len(self.report['services'].get('failed', []))}\n")
            f.write(f"Включенных сервисов: {len(self.report['services'].get('enabled', []))}\n")
            f.write(f"Выключенных сервисов: {len(self.report['services'].get('disabled', []))}\n\n")
            
            if self.report['services'].get('active'):
                f.write("Активные сервисы:\n")
                for service in self.report['services']['active']:
                    f.write(f"  ✅ {service}\n")
                    if service in self.report['services'].get('details', {}):
                        details = self.report['services']['details'][service]
                        if 'exec_start' in details:
                            f.write(f"     Команда: {details['exec_start']}\n")
                        if 'working_directory' in details:
                            f.write(f"     Рабочая директория: {details['working_directory']}\n")
                        if 'user' in details:
                            f.write(f"     Пользователь: {details['user']}\n")
                f.write("\n")
            else:
                f.write("⚠️  Активные сервисы не найдены (возможно, проблема с парсингом)\n")
                f.write("Попытка альтернативного метода...\n")
                # Альтернативный способ
                result = self.run_command('systemctl list-units --type=service --state=running --no-pager')
                if result['success']:
                    f.write("Сырой вывод systemctl:\n")
                    f.write(result['output'][:2000])
                f.write("\n\n")
            
            if self.report['services'].get('enabled'):
                f.write("Включенные сервисы (автозапуск):\n")
                for service in self.report['services']['enabled'][:30]:
                    f.write(f"  🔄 {service}\n")
                f.write("\n")
            
            # Портs
            f.write("=" * 80 + "\n")
            f.write("3. ЗАНЯТЫЕ ПОРТЫ\n")
            f.write("=" * 80 + "\n\n")
            listening = self.report['ports'].get('listening', [])
            f.write(f"Прослушивающих портов: {len(listening)}\n\n")
            
            if listening:
                f.write("Порты в режиме LISTEN:\n")
                # Группируем по процессам
                by_process = defaultdict(list)
                for port_info in listening:
                    process = port_info.get('process', 'unknown')
                    by_process[process].append(port_info)
                
                for process, ports_list in sorted(by_process.items()):
                    f.write(f"\n  📌 {process}:\n")
                    for port_info in ports_list:
                        addr = port_info.get('address', 'unknown')
                        proto = port_info.get('protocol', 'unknown')
                        pid = port_info.get('pid', 'N/A')
                        f.write(f"     {proto:6} {addr:25} (PID: {pid})\n")
                f.write("\n")
            else:
                f.write("⚠️  Прослушивающие порты не найдены (возможно, проблема с парсингом)\n")
                f.write("Попытка альтернативного метода...\n")
                # Альтернативный способ
                result = self.run_command('ss -tulpn 2>&1')
                if result['success']:
                    f.write("Сырой вывод ss:\n")
                    f.write(result['output'][:2000])
                f.write("\n\n")
            
            # Процессы
            f.write("=" * 80 + "\n")
            f.write("4. ПРОЦЕССЫ\n")
            f.write("=" * 80 + "\n\n")
            
            processes = self.report['processes']
            f.write(f"Всего процессов: {processes.get('total', 0)}\n")
            f.write(f"Python процессов: {len(processes.get('python', []))}\n")
            f.write(f"Node.js процессов: {len(processes.get('node', []))}\n")
            f.write(f"Nginx процессов: {len(processes.get('nginx', []))}\n")
            f.write(f"Apache процессов: {len(processes.get('apache', []))}\n")
            f.write(f"MySQL процессов: {len(processes.get('mysql', []))}\n")
            f.write(f"PostgreSQL процессов: {len(processes.get('postgresql', []))}\n")
            f.write(f"Docker процессов: {len(processes.get('docker', []))}\n\n")
            
            if processes.get('python'):
                f.write("Python процессы:\n")
                for proc in processes['python']:
                    f.write(f"  PID {proc['pid']:6} ({proc['user']:10}) CPU: {proc['cpu']:5}% MEM: {proc['mem']:5}% - {proc['command'][:120]}\n")
                f.write("\n")
            
            if processes.get('postgresql') or processes.get('postgres'):
                f.write("PostgreSQL процессы:\n")
                all_postgres = processes.get('postgresql', []) + processes.get('postgres', [])
                seen_pids = set()
                for proc in all_postgres:
                    if proc['pid'] not in seen_pids:
                        f.write(f"  PID {proc['pid']:6} ({proc['user']:10}) CPU: {proc['cpu']:5}% MEM: {proc['mem']:5}% - {proc['command'][:120]}\n")
                        seen_pids.add(proc['pid'])
                f.write("\n")
            
            if processes.get('nginx'):
                f.write("Nginx процессы:\n")
                for proc in processes['nginx']:
                    f.write(f"  PID {proc['pid']:6} ({proc['user']:10}) CPU: {proc['cpu']:5}% MEM: {proc['mem']:5}% - {proc['command'][:120]}\n")
                f.write("\n")
            
            if processes.get('node'):
                f.write("Node.js процессы:\n")
                for proc in processes['node']:
                    f.write(f"  PID {proc['pid']:6} ({proc['user']:10}) CPU: {proc['cpu']:5}% MEM: {proc['mem']:5}% - {proc['command'][:120]}\n")
                f.write("\n")
            
            # Процессы по пользователям
            if processes.get('by_user'):
                f.write("Процессы по пользователям:\n")
                for user, procs in sorted(processes['by_user'].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                    f.write(f"  {user}: {len(procs)} процессов\n")
                f.write("\n")
            
            # Проекты
            f.write("=" * 80 + "\n")
            f.write("5. НАЙДЕННЫЕ ПРОЕКТЫ\n")
            f.write("=" * 80 + "\n\n")
            
            for directory, projects in self.report['projects'].items():
                if projects:
                    f.write(f"{directory}:\n")
                    for project in projects:
                        f.write(f"  📁 {project['name']}\n")
                        f.write(f"     Путь: {project['path']}\n")
                        f.write(f"     Тип: {project['type']}\n")
                        f.write(f"     Размер: {project['size_mb']} MB\n")
                        f.write(f"     Файлов: {project['file_count']}\n")
                        f.write(f"     Индикаторы: {', '.join(project['files'])}\n")
                        f.write("\n")
            
            # Безопасность
            f.write("=" * 80 + "\n")
            f.write("6. БЕЗОПАСНОСТЬ\n")
            f.write("=" * 80 + "\n\n")
            
            security = self.report['security']
            if security.get('firewall'):
                f.write("Firewall:\n")
                for key, value in security['firewall'].items():
                    f.write(f"  {key}: {value[:500]}\n")
                f.write("\n")
            
            if security.get('ssh'):
                f.write("SSH:\n")
                ssh = security['ssh']
                if 'config' in ssh:
                    f.write("  Конфигурация:\n")
                    for key, value in list(ssh['config'].items())[:10]:
                        f.write(f"    {key}: {value}\n")
                if 'authorized_keys_count' in ssh:
                    f.write(f"  Авторизованных ключей: {ssh['authorized_keys_count']}\n")
                f.write("\n")
            
            # Пользователи
            f.write("=" * 80 + "\n")
            f.write("7. ПОЛЬЗОВАТЕЛИ\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Всего пользователей: {len(self.report['users'].get('all', []))}\n")
            f.write(f"Пользователей с shell: {len(self.report['users'].get('with_shell', []))}\n")
            if self.report['users'].get('with_shell'):
                f.write("Пользователи с shell:\n")
                for user in self.report['users']['with_shell'][:20]:
                    f.write(f"  - {user}\n")
                f.write("\n")
            
            # Дисковое пространство
            f.write("=" * 80 + "\n")
            f.write("8. ДИСКОВОЕ ПРОСТРАНСТВО (> 300 МБ)\n")
            f.write("=" * 80 + "\n\n")
            
            disk_usage = self.report.get('disk_usage', {})
            
            if disk_usage.get('large_directories'):
                f.write(f"📊 Всего найдено директорий > 300 МБ: {len(disk_usage['large_directories'])}\n")
                f.write(f"💾 Общий размер: {disk_usage.get('total_size_gb', 0)} ГБ\n\n")
                
                # Сводка по путям
                if disk_usage.get('summary'):
                    f.write("📁 СВОДКА ПО ПУТЯМ:\n")
                    f.write("-" * 80 + "\n")
                    for path, summary in sorted(disk_usage['summary'].items(), key=lambda x: x[1]['total_mb'], reverse=True):
                        f.write(f"  {path}:\n")
                        f.write(f"    Всего: {summary['total_gb']} ГБ ({summary['total_mb']} МБ)\n")
                        f.write(f"    Директорий: {summary['count']}\n")
                    f.write("\n")
                
                # Корневые директории
                if disk_usage.get('root_directories'):
                    f.write("📂 КОРНЕВЫЕ ДИРЕКТОРИИ (> 300 МБ):\n")
                    f.write("-" * 80 + "\n")
                    for item in disk_usage['root_directories']:
                        f.write(f"  {item['size_str']:>10}  {item['path']}\n")
                    f.write("\n")
                
                # Детальный список по путям
                if disk_usage.get('by_path'):
                    f.write("📋 ДЕТАЛЬНЫЙ СПИСОК ПО ПУТЯМ:\n")
                    f.write("-" * 80 + "\n")
                    for path in sorted(disk_usage['by_path'].keys()):
                        items = disk_usage['by_path'][path]
                        items.sort(key=lambda x: x['size_mb'], reverse=True)
                        f.write(f"\n  📁 {path}:\n")
                        for item in items:
                            f.write(f"     {item['size_str']:>10}  {item['path']}\n")
                    f.write("\n")
                
                # Топ-20 самых больших директорий
                if disk_usage.get('large_directories'):
                    f.write("🏆 ТОП-20 САМЫХ БОЛЬШИХ ДИРЕКТОРИЙ:\n")
                    f.write("-" * 80 + "\n")
                    for i, item in enumerate(disk_usage['large_directories'][:20], 1):
                        f.write(f"  {i:2}. {item['size_str']:>10}  {item['path']}\n")
                    f.write("\n")
            else:
                f.write("✅ Директорий > 300 МБ не найдено\n\n")
            
            # Cron
            f.write("=" * 80 + "\n")
            f.write("9. CRON ЗАДАЧИ\n")
            f.write("=" * 80 + "\n\n")
            if self.report['cron'].get('root_crontab'):
                f.write("Root crontab:\n")
                f.write(self.report['cron']['root_crontab'])
                f.write("\n\n")
            
            if self.report['cron'].get('system_cron'):
                f.write("Системные cron задачи:\n")
                for cron_info in self.report['cron']['system_cron']:
                    f.write(f"  {cron_info['directory']}:\n")
                    for file in cron_info['files'][:10]:
                        f.write(f"    - {file}\n")
                f.write("\n")
            
            # Ошибки
            if self.report['errors']:
                f.write("=" * 80 + "\n")
                f.write("9. ОШИБКИ ПРИ СБОРЕ ДАННЫХ\n")
                f.write("=" * 80 + "\n\n")
                for error in self.report['errors']:
                    f.write(f"  ⚠️  {error}\n")
                f.write("\n")
        
        # Также сохраняем JSON
        json_file = output_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Отчет сохранен: {output_file}")
        print(f"✅ JSON сохранен: {json_file}")

def main():
    """Основная функция"""
    print("=" * 80)
    print("🔍 ГЛУБОКИЙ АНАЛИЗ СЕРВЕРА")
    print("=" * 80)
    print()
    
    # Проверяем права root
    if os.geteuid() != 0:
        print("⚠️  Внимание: Скрипт запущен не от root. Некоторые данные могут быть недоступны.")
        print()
    
    auditor = ServerAuditor()
    
    try:
        auditor.get_system_info()
        auditor.get_services()
        auditor.get_ports()
        auditor.get_processes()
        auditor.get_projects()
        auditor.get_security_info()
        auditor.get_network_info()
        auditor.get_storage_info()
        auditor.get_users_info()
        auditor.get_disk_usage(min_size_mb=300)
        auditor.get_cron_info()
        
        # Генерируем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'server_audit_report_{timestamp}.txt'
        auditor.generate_report(report_file)
        
        print()
        print("=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("=" * 80)
        print()
        print("📊 Сводка:")
        print(f"   Активных сервисов: {len(auditor.report['services'].get('active', []))}")
        print(f"   Занятых портов: {len(auditor.report['ports'].get('listening', []))}")
        print(f"   Найдено проектов: {sum(len(projs) for projs in auditor.report['projects'].values())}")
        print(f"   Python процессов: {len(auditor.report['processes'].get('python', []))}")
        disk_usage = auditor.report.get('disk_usage', {})
        if disk_usage.get('large_directories'):
            print(f"   Директорий > 300 МБ: {len(disk_usage['large_directories'])}")
            print(f"   Общий размер: {disk_usage.get('total_size_gb', 0)} ГБ")
        print()
        
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

