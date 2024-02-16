import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import json
from datetime import datetime
import threading

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/' or parsed_url.path == '/index.html':
            self.send_html_file('index.html')
        elif parsed_url.path == '/message.html':
            self.send_html_file('message.html')
        elif parsed_url.path == '/logo.png':
            self.send_static('logo.png')
        elif parsed_url.path == '/style.css':
            self.send_static('style.css')
        else:
            self.send_html_file('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = urllib.parse.parse_qs(post_data.decode())
        print(data)
        send_to_socket_server(data['username'][0], data['message'][0])
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()

    def send_html_file(self, file_name, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(file_name, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, file_name):
        file_path = file_name  # Файлы находятся в той же директории
        mime_type, _ = mimetypes.guess_type(file_path)
        self.send_response(200)
        self.send_header('Content-type', mime_type or 'application/octet-stream')
        self.end_headers()
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())

    def _send_file(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        self.send_response(200)
        self.send_header('Content-type', mime_type or 'application/octet-stream')
        self.end_headers()
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())

def send_to_socket_server(username, message):
    data = json.dumps({'username': username, 'message': message})
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data.encode(), ('localhost', 5000))

def start_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('localhost', 5000))
        while True:
            data, _ = server_socket.recvfrom(1024)
            data_dict = json.loads(data.decode())
            print(f"Received message: {data_dict}")
            save_to_json(data_dict)

def save_to_json(data):
    path = 'storage/data.json'
    try:
        with open(path, 'r+') as file:
            content = json.load(file)
            content[str(datetime.now())] = data
            file.seek(0)
            json.dump(content, file, indent=4)
    except FileNotFoundError:
        with open(path, 'w') as file:
            json.dump({str(datetime.now()): data}, file, indent=4)


if __name__ == '__main__':
    # Запуск сокет-сервера в отдельном потоке
    socket_server_thread = threading.Thread(target=start_socket_server)
    socket_server_thread.start()

    # Запуск HTTP-сервера
    server = HTTPServer(('localhost', 3000), HttpHandler)
    print("Starting HTTP server on port 3000...")
    server.serve_forever()