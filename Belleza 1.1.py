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

        # Línea de tiempo
        self.timeline = tk.Scale(frame_control, from_=0, to=0, orient=tk.HORIZONTAL, command=self.change_frame)
        self.timeline.pack(side=tk.LEFT)

        # Botones para cargar, guardar y exportar
        file_menu = tk.Menu(master, tearoff=0)
        master.config(menu=file_menu)
        file_menu.add_command(label="Cargar Animación", command=self.load_animation)
        file_menu.add_command(label="Guardar Animación", command=self.save_animation)
        file_menu.add_command(label="Exportar Animación", command=self.export_animation)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=master.quit)

        # Botón para reproducir/pausar la animación
        self.play_pause_button = tk.Button(master, text="Reproducir", command=self.play_pause_animation)
        self.play_pause_button.pack(side=tk.BOTTOM)

        # Eventos del canvas
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.release)

        # Crear el primer fotograma
        self.create_new_frame()

    def create_new_frame(self):
        self.current_frame = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.frames.append(self.current_frame)
        self.current_frame_index = len(self.frames) - 1
        self.update_canvas()
        self.update_timeline()

    def use_pencil(self):
        self.current_tool = "pencil"

    def use_brush(self):
        self.current_tool = "brush"

    def use_eraser(self):
        self.current_tool = "eraser"

    def choose_color(self):
        self.color = colorchooser.askcolor(title="Selecciona un color")[1]

    def set_brush_size(self, value):
        self.brush_size = int(value)

    def set_pencil_size(self, value):
        self.pencil_size = int(value)

    def paint(self, event):
        if self.current_tool == "pencil":
            size = self.pencil_size
        else:
            size = self.brush_size

        x, y = event.x, event.y
        if self.last_x and self.last_y:
            draw = ImageDraw.Draw(self.current_frame)
            if self.current_tool == "eraser":
                draw.line((self.last_x, self.last_y, x, y), fill="white", width=size)
            else:
                draw.line((self.last_x, self.last_y, x, y), fill=self.color, width=size)
        self.last_x, self.last_y = x, y
        self.update_canvas()

    def release(self, event):
        self.last_x = None
        self.last_y = None

    def update_canvas(self):
        self.tk_image = ImageTk.PhotoImage(self.current_frame)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

    def update_timeline(self):
        self.timeline.config(from_=0, to=len(self.frames) - 1)
        self.timeline.set(self.current_frame_index)

    def change_frame(self, value):
        self.current_frame_index = int(value)
        self.current_frame = self.frames[self.current_frame_index]
        self.update_canvas()

    def play_pause_animation(self):
        if self.playing:
            self.playing = False
            self.play_pause_button.config(text="Reproducir")
            self.stop_animation()
        else:
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
        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.current_frame = self.frames[self.current_frame_index]
        self.update_canvas()
        self.update_timeline()
        if self.playing:
            self.animation_timer = self.master.after(int(self.frame_duration * 1000), self.next_frame)

    def load_animation(self):
        try:
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("Archivos de animación", "*.json")])
            if file_path:
                with open(file_path, "r") as f:
                    animation_data = json.load(f)

                # Cargar los fotogramas
                self.frames = []
                for frame_data in animation_data["frames"]:
                    frame_bytes = base64.b64decode(frame_data)
                    frame_image = Image.open(io.BytesIO(frame_bytes))
                    self.frames.append(frame_image)

                # Actualizar la animación
                self.current_frame_index = 0
                self.current_frame = self.frames[self.current_frame_index]
                self.update_canvas()
                self.update_timeline()

                messagebox.showinfo("Éxito", "La animación se ha cargado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar la animación: {e}")

    def save_animation(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Archivos de animación", "*.json")])
            if file_path:
                animation_data = {
                    "frames": [
                        base64.b64encode(frame.tobytes()).decode("utf-8")
                        for frame in self.frames
                    ]
                }

                with open(file_path, "w") as f:
                    json.dump(animation_data, f)

                messagebox.showinfo("Éxito", "La animación se ha guardado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la animación: {e}")

    def export_animation(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif"), ("PNG files", "*.png")])
            if file_path:
                # Convertir los fotogramas a GIF o PNG
                if file_path.endswith(".gif"):
                    self.frames[0].save(file_path, save_all=True, append_images=self.frames[1:], optimize=False, duration=int(self.frame_duration * 1000), loop=0)
                else:
                    for i, frame in enumerate(self.frames):
                        frame.save(f"{file_path[:-4]}_{i}.png")

                messagebox.showinfo("Éxito", "La animación se ha exportado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar la animación: {e}")
    

    def delete_frame(self):
        if len(self.frames) > 1:
            del self.frames[self.current_frame_index]
            if self.current_frame_index == len(self.frames):
                self.current_frame_index -= 1
            self.current_frame = self.frames[self.current_frame_index]
            self.update_canvas()
            self.update_timeline()
        else:
            messagebox.showwarning("Advertencia", "No puedes eliminar el único fotograma.")

root = tk.Tk()
app = AnimationApp(root)
root.mainloop()
