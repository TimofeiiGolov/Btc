#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cgi
from http.server import HTTPServer, SimpleHTTPRequestHandler

class UploadHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_form = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Загрузка файла</title>
</head>
<body>
    <h2>Загрузить файл</h2>
    <form method="POST" enctype="multipart/form-data" action="/upload">
        <input type="file" name="file"><br><br>
        <input type="submit" value="Загрузить">
    </form>
    <hr>
    <a href="/">Вернуться к списку файлов</a>
</body>
</html>'''
            self.wfile.write(html_form.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
            )
            file_item = form['file']
            if file_item.filename:
                filename = os.path.basename(file_item.filename)
                with open(filename, 'wb') as f:
                    f.write(file_item.file.read())
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                response = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Файл загружен</title>
</head>
<body>
    <h2>Файл {filename} загружен!</h2>
    <a href="/">Назад к списку</a>
</body>
</html>'''
                self.wfile.write(response.encode('utf-8'))
            else:
                self.send_error(400, "Файл не выбран")
        else:
            self.send_error(404)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), UploadHandler)
    print("Сервер запущен на порту 8080. Открой http://<IP>:8080/upload для загрузки файлов.")
    server.serve_forever()
