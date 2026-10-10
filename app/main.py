import os
import socket
import sys
import threading


def handle_client(conn: socket.socket, directory: str | None) -> None:
    try:
        data = conn.recv(1024).decode("utf-8")

        if data:
            lines = data.split("\r\n")
            request_line = lines[0]
            parts = request_line.split(" ")

            # Parse headers case-insensitively
            headers = {}
            for line in lines[1:]:
                if not line:
                    break
                if ": " in line:
                    key, val = line.split(": ", 1)
                    headers[key.lower()] = val

            if len(parts) >= 2:
                path = parts[1]

                if path == "/":
                    conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

                elif path.startswith("/echo/"):
                    echo_str = path[len("/echo/"):]
                    body_bytes = echo_str.encode("utf-8")
                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body_bytes)}\r\n"
                        f"\r\n"
                        f"{echo_str}"
                    )
                    conn.sendall(response.encode("utf-8"))

                elif path == "/user-agent":
                    user_agent = headers.get("user-agent", "")
                    body_bytes = user_agent.encode("utf-8")
                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body_bytes)}\r\n"
                        f"\r\n"
                        f"{user_agent}"
                    )
                    conn.sendall(response.encode("utf-8"))

                elif path.startswith("/files/"):
                    filename = path[len("/files/"):]
                    if directory:
                        filepath = os.path.join(directory, filename)
                        if os.path.isfile(filepath):
                            with open(filepath, "rb") as f:
                                body = f.read()

                            header = (
                                f"HTTP/1.1 200 OK\r\n"
                                f"Content-Type: application/octet-stream\r\n"
                                f"Content-Length: {len(body)}\r\n"
                                f"\r\n"
                            ).encode("utf-8")

                            conn.sendall(header + body)
                        else:
                            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                    else:
                        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

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
