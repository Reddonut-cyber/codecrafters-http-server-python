import os
import socket
import sys
import threading


def handle_client(conn: socket.socket, directory: str | None) -> None:
    try:
        raw_data = conn.recv(4096)
        if not raw_data:
            return

        # Separate headers and body using \r\n\r\n
        delimiter = b"\r\n\r\n"
        if delimiter not in raw_data:
            return

        header_bytes, body_bytes = raw_data.split(delimiter, 1)
        header_text = header_bytes.decode("utf-8")
        lines = header_text.split("\r\n")

        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) < 2:
            return

        method = parts[0]
        path = parts[1]

        # Parse headers case-insensitively
        headers = {}
        for line in lines[1:]:
            if ": " in line:
                key, val = line.split(": ", 1)
                headers[key.lower()] = val

        # Ensure complete body is read based on Content-Length
        content_length = int(headers.get("content-length", 0))
        while len(body_bytes) < content_length:
            chunk = conn.recv(4096)
            if not chunk:
                break
            body_bytes += chunk

        # Route matching
        if path == "/":
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

        elif path.startswith("/echo/"):
            echo_str = path[len("/echo/"):]
            body = echo_str.encode("utf-8")
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"\r\n"
                f"{echo_str}"
            )
            conn.sendall(response.encode("utf-8"))

        elif path == "/user-agent":
            user_agent = headers.get("user-agent", "")
            body = user_agent.encode("utf-8")
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"\r\n"
                f"{user_agent}"
            )
            conn.sendall(response.encode("utf-8"))

        elif path.startswith("/files/"):
            filename = path[len("/files/"):]
            if not directory:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                return

            filepath = os.path.join(directory, filename)

            if method == "GET":
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        file_content = f.read()

                    header = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(file_content)}\r\n"
                        f"\r\n"
                    ).encode("utf-8")
                    conn.sendall(header + file_content)
                else:
                    conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

            elif method == "POST":
                with open(filepath, "wb") as f:
                    f.write(body_bytes)
                conn.sendall(b"HTTP/1.1 201 Created\r\n\r\n")

            else:
                conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")

        else:
            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    finally:
        conn.close()


def main():
    directory = None
    if "--directory" in sys.argv:
        dir_index = sys.argv.index("--directory") + 1
        if dir_index < len(sys.argv):
            directory = sys.argv[dir_index]

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(conn, directory)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
