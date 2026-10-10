import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        conn, addr = server_socket.accept()

        # Read the incoming request
        data = conn.recv(1024).decode("utf-8")

        if data:
            # The first line is the request line: e.g. "GET / HTTP/1.1"
            request_line = data.split("\r\n")[0]
            parts = request_line.split(" ")

            # The URL path is the second element
            if len(parts) >= 2:
                path = parts[1]

                if path == "/":
                    conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
                elif path.startswith("/echo/"):
                    echo_str = path[len("/echo/"):]
                    body_bytes = echo_str.encode("utf-8")
                    content_length = len(body_bytes)

                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: text/plain\r\n"
                        f"Content-Length: {content_length}\r\n"
                        f"\r\n"
                        f"{echo_str}"
                    )
                    conn.sendall(response.encode("utf-8"))
                else:
                    conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

        conn.close()


if __name__ == "__main__":
    main()
