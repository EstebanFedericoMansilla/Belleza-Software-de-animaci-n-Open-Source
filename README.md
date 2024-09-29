import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw
import json
import base64
import io
import moviepy.editor as mpy
import numpy as np
import time

class AnimationApp:
    def __init__(self, master):
        self.master = master
        master.title("Belleza 1.1")

        # Parámetros de la animación
        self.canvas_width = 800
        self.canvas_height = 600
        self.fps = 24  # Fotogramas por segundo
        self.frame_duration = 1/self.fps  # Duración de cada fotograma en segundos

        # Inicializar variables
        self.frames = []
        self.current_frame_index = 0
        self.current_frame = None
        self.tk_image = None
        self.color = "black"
        self.current_tool = "pencil"
        self.last_x = None
        self.last_y = None
        self.brush_size = 2  # Tamaño del pincel
        self.pencil_size = 2  # Tamaño del lápiz
        self.playing = False  # Indicador de si la animación está en reproducción
        self.animation_timer = None  # Timer para la reproducción
        self.layers = [[]]  # Lista de capas (cada capa es una lista de fotogramas)
        self.current_layer_index = 0

        # Crear canvas
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()

        # Crear barra de herramientas
        toolbar = tk.Frame(master)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Botones de herramientas
        pencil_button = tk.Button(toolbar, text="Lápiz", command=self.use_pencil)
        pencil_button.pack(side=tk.LEFT)

        brush_button = tk.Button(toolbar, text="Pincel", command=self.use_brush)
        brush_button.pack(side=tk.LEFT)

        eraser_button = tk.Button(toolbar, text="Borrador", command=self.use_eraser)
        eraser_button.pack(side=tk.LEFT)

        color_button = tk.Button(toolbar, text="Color", command=self.choose_color)
        color_button.pack(side=tk.LEFT)

        # Control de tamaño del pincel
        self.brush_size_label = tk.Label(toolbar, text="Tamaño del pincel:")
        self.brush_size_label.pack(side=tk.LEFT)

        self.brush_size_scale = tk.Scale(toolbar, from_=1, to=50, orient=tk.HORIZONTAL, command=self.set_brush_size, showvalue=0)
        self.brush_size_scale.pack(side=tk.LEFT)

        # Control de tamaño del Lápiz
        self.pencil_size_label = tk.Label(toolbar, text="Tamaño del Lápiz:")
        self.pencil_size_label.pack(side=tk.LEFT)

        self.pencil_size_scale = tk.Scale(toolbar, from_=1, to=50, orient=tk.HORIZONTAL, command=self.set_pencil_size, showvalue=0)
        self.pencil_size_scale.pack(side=tk.LEFT)

        # Crear barra de control de fotogramas
        frame_control = tk.Frame(master)
        frame_control.pack(side=tk.TOP, fill=tk.X)

        # Botón para crear un nuevo fotograma
        new_frame_button = tk.Button(frame_control, text="Nuevo Fotograma", command=self.create_new_frame)
        new_frame_button.pack(side=tk.LEFT)

        # Botón para eliminar un fotograma
        delete_frame_button = tk.Button(frame_control, text="Eliminar Fotograma", command=self.delete_frame)
        delete_frame_button.pack(side=tk.LEFT)

        # Botón para crear una nueva capa
        new_layer_button = tk.Button(frame_control, text="Nueva Capa", command=self.create_new_layer)
        new_layer_button.pack(side=tk.LEFT)

        # Botón para eliminar una capa
        delete_layer_button = tk.Button(frame_control, text="Eliminar Capa", command=self.delete_layer)
        delete_layer_button.pack(side=tk.LEFT)

        # Línea de tiempo
        self.timeline = tk.Canvas(frame_control, width=self.canvas_width, height=30, bg="lightgray")
        self.timeline.pack(side=tk.LEFT)
        self.timeline.bind("<Button-1>", self.select_layer)

        # Botones para cargar, guardar y exportar
        load_button = tk.Button(frame_control, text="Cargar", command=self.load_animation)
        load_button.pack(side=tk.LEFT)

        save_button = tk.Button(frame_control, text="Guardar", command=self.save_animation)
        save_button.pack(side=tk.LEFT)

        export_button = tk.Button(frame_control, text="Exportar", command=self.export_animation)
        export_button.pack(side=tk.LEFT)

        # Botón para reproducir/pausar la animación
        self.play_pause_button = tk.Button(frame_control, text="Reproducir", command=self.play_pause_animation)
        self.play_pause_button.pack(side=tk.LEFT)

        # Vincular eventos del canvas
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.release_paint)
        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<KeyPress-Left>", self.previous_frame)
        self.canvas.bind("<KeyPress-Right>", self.next_frame)
        self.canvas.bind("<KeyPress-space>", self.play_pause_animation)

        # Crear el primer fotograma
        self.create_new_frame()

        # Cargar los fotogramas
        self.load_frames()

        # Actualizar la animación
        self.update_animation()

    def use_pencil(self):
        self.current_tool = "pencil"

    def use_brush(self):
        self.current_tool = "brush"

    def use_eraser(self):
        self.current_tool = "eraser"

    def choose_color(self):
        self.color = colorchooser.askcolor(title="Seleccionar Color")[1]

    def set_brush_size(self, value):
        self.brush_size = int(value)

    def set_pencil_size(self, value):
        self.pencil_size = int(value)

    def create_new_frame(self):
        # Crear un nuevo lienzo para el fotograma
        new_frame = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        draw = ImageDraw.Draw(new_frame)

        # Agregar el nuevo fotograma a la lista de fotogramas de la capa actual
        self.layers[self.current_layer_index].append(new_frame)

        # Actualizar el índice del fotograma actual
        self.current_frame_index = len(self.layers[self.current_layer_index]) - 1

        # Actualizar el fotograma actual
        self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]

        # Limpiar el canvas
        self.canvas.delete("all")

        # Mostrar el fotograma actual en el canvas
        self.update_canvas()

        # Actualizar la línea de tiempo
        self.update_timeline()

    def delete_frame(self):
        if len(self.layers[self.current_layer_index]) > 0:
            # Eliminar el fotograma actual de la lista
            if len(self.layers[self.current_layer_index]) > 0 and self.current_frame_index < len(self.layers[self.current_layer_index]):
                self.layers[self.current_layer_index].pop(self.current_frame_index)

            # Actualizar el índice del fotograma actual
            self.current_frame_index = max(0, self.current_frame_index - 1)

            # Actualizar el fotograma actual
            if self.current_frame_index >= 0:
                self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
            else:
                self.current_frame = None

            # Limpiar el canvas
            self.canvas.delete("all")

            # Mostrar el fotograma actual en el canvas
            self.update_canvas()

            # Actualizar la línea de tiempo
            self.update_timeline()

    def create_new_layer(self):
        # Crear una nueva capa vacía
        self.layers.append([])

        # Actualizar el índice de la capa actual
        self.current_layer_index = len(self.layers) - 1

        # Crear un nuevo fotograma para la nueva capa
        self.create_new_frame()

    def delete_layer(self):
        if len(self.layers) > 1:
            # Eliminar la capa actual
            self.layers.pop(self.current_layer_index)

            # Actualizar el índice de la capa actual
            self.current_layer_index = max(0, self.current_layer_index - 1)

            # Actualizar el fotograma actual
            self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]

            # Limpiar el canvas
            self.canvas.delete("all")

            # Mostrar el fotograma actual en el canvas
            self.update_canvas()

            # Actualizar la línea de tiempo
            self.update_timeline()

    def select_layer(self, event):
        # Calcular el índice de la capa seleccionada
        layer_index = int(event.y / 30)

        # Verificar si se seleccionó una capa válida
        if 0 <= layer_index < len(self.layers):
            self.current_layer_index = layer_index
            self.current_frame_index = 0
            self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
            self.update_canvas()
            self.update_timeline()

    def load_animation(self):
        # Abrir un cuadro de diálogo para seleccionar un archivo
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("all files", "*.*"))
        )

        # Si se seleccionó un archivo, cargar la animación
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Cargar las capas de la animación
            self.layers = []
            for layer_data in data["layers"]:
                layer = []
                for frame_data in layer_data:
                    frame_image = Image.open(io.BytesIO(base64.b64decode(frame_data)))
                    layer.append(frame_image)
                self.layers.append(layer)

            # Actualizar el índice del fotograma actual
            self.current_frame_index = 0
            self.current_layer_index = 0

            # Actualizar el fotograma actual
            self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]

            # Limpiar el canvas
            self.canvas.delete("all")

            # Mostrar el fotograma actual en el canvas
            self.update_canvas()

            # Actualizar la línea de tiempo
            self.update_timeline()

    def save_animation(self):
        # Abrir un cuadro de diálogo para guardar un archivo
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("all files", "*.*"))
        )

        # Si se seleccionó un archivo, guardar la animación
        if file_path:
            data = {"layers": []}
            for layer in self.layers:
                layer_data = []
                for frame in layer:
                    buffer = io.BytesIO()
                    frame.save(buffer, format="PNG")
                    frame_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    layer_data.append(frame_data)
                data["layers"].append(layer_data)

            with open(file_path, "w") as f:
                json.dump(data, f)

    def export_animation(self):
        # Abrir un cuadro de diálogo para guardar un archivo
        file_path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=(("GIF files", "*.gif"), ("PNG files", "*.png"), ("all files", "*.*"))
        )

        # Si se seleccionó un archivo, exportar la animación
        if file_path:
            if file_path.endswith(".gif"):
                # Exportar la animación como GIF
                self.export_as_gif(file_path)
            elif file_path.endswith(".png"):
                # Exportar la animación como secuencia de PNG
                self.export_as_png_sequence(file_path)

    def export_as_gif(self, file_path):
        # Crear una lista de fotogramas para el GIF
        frames = []
        for layer in self.layers:
            for frame in layer:
                frames.append(ImageTk.PhotoImage(frame))

        # Crear el GIF
        gif = frames[0]
        gif.save(file_path, save_all=True, append_images=frames[1:], optimize=False, duration=self.frame_duration * 1000, loop=0)

    def export_as_png_sequence(self, file_path):
        # Exportar cada fotograma como una imagen PNG
        for i, layer in enumerate(self.layers):
            for j, frame in enumerate(layer):
                frame.save(f"{file_path}_layer{i}_frame{j}.png")

    def paint(self, event):
        if self.current_tool == "pencil":
            self.draw_line(event.x, event.y, self.pencil_size)
        elif self.current_tool == "brush":
            self.draw_circle(event.x, event.y, self.brush_size)
        elif self.current_tool == "eraser":
            self.draw_circle(event.x, event.y, self.brush_size, "white")

    def start_paint(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def release_paint(self, event):
        self.last_x = None
        self.last_y = None

    def draw_line(self, x, y, size):
        if self.last_x is not None and self.last_y is not None:
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=size, fill=self.color, capstyle=tk.ROUND)
            self.last_x = x
            self.last_y = y

            # Dibujar en el fotograma actual
            draw = ImageDraw.Draw(self.current_frame)
            draw.line((self.last_x, self.last_y, x, y), fill=self.color, width=size)

    def draw_circle(self, x, y, size, color=None):
        if color is None:
            color = self.color
        self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline=color)

        # Dibujar en el fotograma actual
        draw = ImageDraw.Draw(self.current_frame)
        draw.ellipse((x - size, y - size, x + size, y + size), fill=color, outline=color)

    def update_canvas(self):
        if self.current_frame is not None:
            # Convertir el fotograma actual a una imagen Tkinter
            self.tk_image = ImageTk.PhotoImage(self.current_frame)

            # Mostrar la imagen en el canvas
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def update_timeline(self):
        # Limpiar la línea de tiempo
        self.timeline.delete("all")

        # Dibujar los fotogramas en la línea de tiempo
        for i, layer in enumerate(self.layers):
            for j, frame in enumerate(layer):
                # Calcular la posición del fotograma en la línea de tiempo
                x = (j / len(layer)) * self.canvas_width

                # Dibujar un rectángulo para representar el fotograma
                self.timeline.create_rectangle(x, i * 30, x + 10, (i + 1) * 30, fill="blue" if i == self.current_layer_index and j == self.current_frame_index else "gray")

    def load_frames(self):
        # Cargar los fotogramas de la animación
        if len(self.layers[self.current_layer_index]) > 0:
            self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
            self.update_canvas()

    def update_animation(self):
        if self.playing:
            # Actualizar el índice del fotograma actual
            self.current_frame_index = (self.current_frame_index + 1) % len(self.layers[self.current_layer_index])

            # Actualizar el fotograma actual
            self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]

            # Limpiar el canvas
            self.canvas.delete("all")

            # Mostrar el fotograma actual en el canvas
            self.update_canvas()

            # Actualizar la línea de tiempo
            self.update_timeline()

            # Programar la siguiente actualización
            self.animation_timer = self.master.after(int(self.frame_duration * 1000), self.update_animation)

    def play_pause_animation(self):
        if self.playing:
            # Pausar la animación
            self.playing = False
            self.play_pause_button.config(text="Reproducir")
            self.stop_animation()
        else:
            # Reproducir la animación
            self.playing = True
            self.play_pause_button.config(text="Pausar")
            self.start_animation()

    def start_animation(self):
        if self.animation_timer is None:
            self.animation_timer = self.master.after(int(self.frame_duration * 1000), self.next_frame)

    def stop_animation(self):
        if self.animation_timer is not None:
            self.master.after_cancel(self.animation_timer)
            self.animation_timer = None

    def next_frame(self):
        self.current_frame_index = (self.current_frame_index + 1) % len(self.layers[self.current_layer_index])
        self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
        self.update_canvas()
        self.update_timeline()
        if self.playing:
            self.animation_timer = self.master.after(int(self.frame_duration * 1000), self.next_frame)

    def previous_frame(self, event=None):
        # Ir al fotograma anterior
        self.current_frame_index = (self.current_frame_index - 1) % len(self.layers[self.current_layer_index])
        self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
        self.update_canvas()
        self.update_timeline()

    def next_frame(self, event=None):
        # Ir al siguiente fotograma
        self.current_frame_index = (self.current_frame_index + 1) % len(self.layers[self.current_layer_index])
        self.current_frame = self.layers[self.current_layer_index][self.current_frame_index]
        self.update_canvas()
        self.update_timeline()

root = tk.Tk()
app = AnimationApp(root)
root.mainloop()
