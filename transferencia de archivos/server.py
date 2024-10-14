import socket
import os
import threading

#Sebastian Ricardo Alvarado Cely

# Configuración del servidor
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
FILES_DIR = "shared_files"

#El directorio de archivos debe existir
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def handle_client(client_socket, client_address):
    print(f"[+] Conexión establecida con {client_address}")

    while True:
        try:
            # Recibir el comando del cliente
            received = client_socket.recv(BUFFER_SIZE).decode()
            if not received:
                break  # El cliente se desconecta

            print(f"Recibido: {received} de {client_address}")

            command, *args = received.split()

            if command == "LIST":
                # Enviar la lista de archivos
                files = os.listdir(FILES_DIR)
                files_list = "\n".join(files)
                client_socket.send(files_list.encode())

            elif command == "UPLOAD":
                # Formato: UPLOAD carga realizada con exito
                filename = args[0]
                filesize = int(args[1])

                # Ruta completa del archivo
                filepath = os.path.join(FILES_DIR, filename)

                # Recibir el archivo
                with open(filepath, "wb") as f:
                    bytes_read = 0
                    while bytes_read < filesize:
                        bytes_to_read = min(BUFFER_SIZE, filesize - bytes_read)
                        data = client_socket.recv(bytes_to_read)
                        if not data:
                            break
                        f.write(data)
                        bytes_read += len(data)
                client_socket.send("UPLOAD_OK".encode())

            elif command == "DOWNLOAD":
                # Formato: DOWNLOAD y el nombre del archivo
                filename = args[0]
                filepath = os.path.join(FILES_DIR, filename)

                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    client_socket.send(f"EXISTS {filesize}".encode())

                    # Esperar confirmación del cliente
                    client_response = client_socket.recv(BUFFER_SIZE).decode()
                    if client_response == "DOWNLOAD":
                        with open(filepath, "rb") as f:
                            while True:
                                bytes_read = f.read(BUFFER_SIZE)
                                if not bytes_read:
                                    break
                                client_socket.sendall(bytes_read)
                else:
                    client_socket.send("NO_EXISTS".encode())

            elif command == "QUIT":
                break

            else:
                client_socket.send("Comando no reconocido.".encode())

        except Exception as e:
            print(f"Error con {client_address}: {e}")
            break

    client_socket.close()
    print(f"[-] Conexión cerrada con {client_address}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"[*] Servidor escuchando en {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
