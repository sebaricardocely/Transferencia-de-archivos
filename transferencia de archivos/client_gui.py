import socket
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

#Sebastian Ricardo Alvarado Cely


# Configuración del cliente
SERVER_HOST = '127.0.0.1'  # Establezco mi local host
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
FILES_DIR = "shared_files_client"

#Debe existir el directorio de descargas
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

class FileTransferClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente de Transferencia de Archivos")
        self.master.geometry("600x400")
        
        self.create_widgets()
        
      
        threading.Thread(target=self.connect_to_server, daemon=True).start()
    
    def create_widgets(self):
        # Aquí listo los archivos que se subo,actualizao o voy a descargar.
        list_frame = tk.Frame(self.master)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.files_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        
        # Accionar de los botones
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)
        
        self.refresh_button = tk.Button(button_frame, text="Actualizar Lista", command=self.list_files)
        self.refresh_button.grid(row=0, column=0, padx=5)
        
        self.upload_button = tk.Button(button_frame, text="Subir Archivo", command=self.upload_file)
        self.upload_button.grid(row=0, column=1, padx=5)
        
        self.download_button = tk.Button(button_frame, text="Descargar Archivo", command=self.download_file)
        self.download_button.grid(row=0, column=2, padx=5)
        
        self.exit_button = tk.Button(button_frame, text="Salir", command=self.exit_client)
        self.exit_button.grid(row=0, column=3, padx=5)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Conectando al servidor...")
        self.status_bar = tk.Label(self.master, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            self.status_var.set(f"Conectado al servidor {SERVER_HOST}:{SERVER_PORT}")
            self.list_files()
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {e}")
            self.status_var.set("Error de conexión.")
    
    def list_files(self):
        try:
            self.client_socket.send("LIST".encode())
            files = self.client_socket.recv(BUFFER_SIZE).decode()
            self.files_listbox.delete(0, tk.END)
            if files:
                for file in files.split('\n'):
                    self.files_listbox.insert(tk.END, file)
            else:
                self.files_listbox.insert(tk.END, "No hay archivos en el servidor.")
            self.status_var.set("Lista de archivos actualizada.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al listar archivos: {e}")
            self.status_var.set("Error al listar archivos.")
    
    def upload_file(self):
        try:
            filepath = filedialog.askopenfilename()
            if not filepath:
                return  # El usuario canceló la operación
            
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            # Enviar comando de subida
            self.client_socket.send(f"UPLOAD {filename} {filesize}".encode())
            
            # Enviar el archivo
            with open(filepath, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    self.client_socket.sendall(bytes_read)
            
            # Esperar confirmación de subida
            response = self.client_socket.recv(BUFFER_SIZE).decode()
            if response == "UPLOAD_OK":
                messagebox.showinfo("Éxito", "Archivo subido exitosamente.")
                self.list_files()
            else:
                messagebox.showerror("Error", "Error al subir el archivo.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al subir archivo: {e}")
            self.status_var.set("Error al subir archivo.")
    
    def download_file(self):
        try:
            selected = self.files_listbox.curselection()
            if not selected:
                messagebox.showwarning("Seleccionar Archivo", "Por favor, selecciona un archivo para descargar.")
                return
            filename = self.files_listbox.get(selected[0])
            if filename == "No hay archivos en el servidor.":
                messagebox.showwarning("Sin Archivos", "No hay archivos disponibles para descargar.")
                return
            
            # Enviar comando de descarga
            self.client_socket.send(f"DOWNLOAD {filename}".encode())
            
            # Recibir respuesta del servidor
            response = self.client_socket.recv(BUFFER_SIZE).decode()
            
            if response.startswith("EXISTS"):
                filesize = int(response.split()[1])
                # Confirmar descarga
                confirm = messagebox.askyesno("Descargar", f"El archivo '{filename}' existe. ¿Deseas descargarlo?")
                if confirm:
                    self.client_socket.send("DOWNLOAD".encode())
                    
                    # Seleccionar ubicación para guardar el archivo
                    save_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".*")
                    if not save_path:
                        # El usuario canceló la descarga
                        self.client_socket.recv(filesize)  
                        return
                    
                    with open(save_path, "wb") as f:
                        bytes_read = 0
                        while bytes_read < filesize:
                            bytes_to_read = min(BUFFER_SIZE, filesize - bytes_read)
                            data = self.client_socket.recv(bytes_to_read)
                            if not data:
                                break
                            f.write(data)
                            bytes_read += len(data)
                    messagebox.showinfo("Éxito", f"Archivo descargado exitosamente y guardado en:\n{save_path}")
                    self.status_var.set(f"Archivo '{filename}' descargado.")
            elif response == "NO_EXISTS":
                messagebox.showerror("Error", "El archivo no existe en el servidor.")
                self.status_var.set("Archivo no existe.")
            else:
                messagebox.showerror("Error", "Error en la descarga.")
                self.status_var.set("Error en la descarga.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar archivo: {e}")
            self.status_var.set("Error al descargar archivo.")
    
    def exit_client(self):
        try:
            self.client_socket.send("QUIT".encode())
        except:
            pass  
        self.master.destroy()

def main():
    root = tk.Tk()
    app = FileTransferClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
