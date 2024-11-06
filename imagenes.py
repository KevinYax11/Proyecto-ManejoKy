import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime
import struct

class AnalizadorGIF:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Analizador de Archivos GIF")
        self.window.geometry("1000x700")
        self.window.configure(bg="#f7f7f7")

        # Almacenamiento de datos
        self.data_file = "datos_gif.json"
        self.gif_data = self.cargar_datos()

        self.setup_ui()
        self.verificar_primera_ejecucion()

    def setup_ui(self):
        # Configuración de la interfaz de usuario
        self.left_frame = ttk.Frame(self.window, padding="5")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.right_frame = ttk.Frame(self.window, padding="5")
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Estilos
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TFrame", background="#f7f7f7")

        # Botón para añadir carpeta
        self.add_folder_btn = ttk.Button(self.left_frame, text="Añadir Carpeta", command=self.agregar_carpeta)
        self.add_folder_btn.pack(fill=tk.X, pady=10)

        # Función de búsqueda
        self.search_entry = ttk.Entry(self.left_frame)
        self.search_entry.pack(fill=tk.X, pady=5)
        self.search_btn = ttk.Button(self.left_frame, text="Buscar", command=self.buscar_archivos)
        self.search_btn.pack(fill=tk.X, pady=5)

        # Treeview para mostrar archivos
        self.tree = ttk.Treeview(self.left_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Visualización de información
        self.info_frame = ttk.LabelFrame(self.right_frame, text="Información del GIF", padding="10")
        self.info_frame.pack(fill=tk.BOTH, expand=True)

        # Crear campos de entrada
        self.entries = {}
        self.field_map = {
            "Versión": "version",
            "Ancho": "width",
            "Alto": "height",
            "Cantidad de Colores": "color_count",
            "Compresión": "compression",
            "Formato Numérico": "number_format",
            "Color de Fondo": "background_color",
            "Cantidad de Imágenes": "image_count",
            "Fecha de Creación": "creation_date",
            "Fecha de Modificación": "modified_date",
            "Comentarios": "comments"
        }

        for campo, key in self.field_map.items():
            frame = ttk.Frame(self.info_frame)
            frame.pack(fill=tk.X, pady=3)

            label = ttk.Label(frame, text=f"{campo}:", width=20)
            label.pack(side=tk.LEFT, padx=5)

            entry = ttk.Entry(frame, font=("Helvetica", 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            self.entries[key] = entry

        # Botón para guardar cambios
        self.save_btn = ttk.Button(self.info_frame, text="Guardar Cambios", command=self.guardar_cambios)
        self.save_btn.pack(pady=15)

    def verificar_primera_ejecucion(self):
        if not os.path.exists(self.data_file):
            self.agregar_carpeta()

    def cargar_datos(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def guardar_datos(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.gif_data, f, indent=4)

    def agregar_carpeta(self):
        folder = filedialog.askdirectory()
        if folder:
            self.escanear_carpeta(folder)
            self.actualizar_arbol()
            self.guardar_datos()

    def escanear_carpeta(self, folder):
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.gif'):
                    file_path = os.path.join(root, file)
                    self.analizar_gif(file_path)

    def analizar_gif(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                # Leer encabezado GIF
                header = f.read(6)
                if header[:3] != b'GIF':
                    return

                version = header[3:6].decode()

                # Leer descriptor de pantalla lógica
                width, height = struct.unpack('<HH', f.read(4))
                packed_field = f.read(1)[0]
                color_table_size = 2 ** ((packed_field & 7) + 1)

                # Información del archivo
                file_stat = os.stat(file_path)

                gif_info = {
                    'version': version,
                    'width': width,
                    'height': height,
                    'color_count': color_table_size,
                    'compression': 'LZW',
                    'number_format': 'Little-endian',
                    'background_color': hex(packed_field),
                    'image_count': self.contar_imagenes(f),
                    'creation_date': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'comments': self.extraer_comentarios(f)
                }

                self.gif_data[file_path] = gif_info

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo analizar {file_path}: {str(e)}")

    def contar_imagenes(self, f):
        count = 0
        try:
            while True:
                byte = f.read(1)
                if not byte:
                    break
                if byte == b'\x2C':  # Marcador de descriptor de imagen
                    count += 1
                elif byte == b'\x3B':  # Trailer de GIF
                    break
        except:
            pass
        f.seek(0)
        return count

    def extraer_comentarios(self, f):
        comments = []
        try:
            while True:
                byte = f.read(1)
                if not byte:
                    break
                if byte == b'\x21':  # Introductor de extensión
                    ext_type = f.read(1)
                    if ext_type == b'\xFE':  # Extensión de comentario
                        size = f.read(1)[0]
                        if size:
                            comments.append(f.read(size).decode('ascii', errors='ignore'))
                elif byte == b'\x3B':  # Trailer de GIF
                    break
        except:
            pass
        f.seek(0)
        return '; '.join(comments) if comments else ''

    def actualizar_arbol(self):
        self.tree.delete(*self.tree.get_children())

        # Agrupar archivos por carpeta
        folders = {}
        for path in self.gif_data:
            folder = os.path.dirname(path)
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(path)

        # Añadir al árbol
        for folder in sorted(folders):
            folder_item = self.tree.insert('', 'end', text=folder)
            for path in sorted(folders[folder]):
                self.tree.insert(folder_item, 'end', text=os.path.basename(path), values=(path,))

    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            if item['values']:
                path = item['values'][0]
                info = self.gif_data.get(path, {})

                for key, entry in self.entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, str(info.get(key, '')))

    def guardar_cambios(self):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            if item['values']:
                path = item['values'][0]

                # Actualizar los datos en el diccionario y luego en el archivo JSON
                for key, entry in self.entries.items():
                    self.gif_data[path][key] = entry.get()

                self.guardar_datos()
                messagebox.showinfo("Éxito", "¡Cambios guardados correctamente!")

    def buscar_archivos(self):
        query = self.search_entry.get().lower()
        if not query:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for path, info in self.gif_data.items():
            if query in path.lower() or any(query in str(value).lower() for value in info.values()):
                folder = os.path.dirname(path)
                folder_item = self.tree.insert('', 'end', text=folder)
                self.tree.insert(folder_item, 'end', text=os.path.basename(path), values=(path,))

    def run(self):
        self.window.mainloop()

app = AnalizadorGIF()
app.run()