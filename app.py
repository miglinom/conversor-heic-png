"""
Conversor de fotos HEIC (iPhone) a PNG
---------------------------------------
Aplicacion de escritorio para Windows. El usuario arrastra una carpeta
con fotos de iPhone (.heic / .heif) sobre la ventana y el programa
genera copias en formato PNG dentro de una subcarpeta "PNG convertidas".

Una vez compilado como .exe (ver build.bat), no requiere instalar
Python ni nada en la PC donde se usa.
"""

import threading
import traceback
from pathlib import Path

from PIL import Image, ImageOps
import pillow_heif

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

pillow_heif.register_heif_opener()

HEIC_EXTENSIONS = {".heic", ".heif"}

TEXTO_INICIAL = (
    "Arrastra aqui la carpeta con tus fotos\n"
    "(.HEIC / .HEIF)\n\n"
    "o hace click para elegirla"
)


def convertir_carpeta(carpeta: Path, log_callback):
    """Convierte todos los .heic/.heif de 'carpeta' (no subcarpetas) a PNG."""
    destino = carpeta / "PNG convertidas"
    destino.mkdir(exist_ok=True)

    archivos = [
        f for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() in HEIC_EXTENSIONS
    ]

    if not archivos:
        log_callback("No encontre archivos .HEIC o .HEIF en esa carpeta.")
        return 0, 0

    ok, errores = 0, 0
    for i, archivo in enumerate(archivos, start=1):
        try:
            log_callback(f"Convirtiendo {i}/{len(archivos)}: {archivo.name}")
            with Image.open(archivo) as img:
                # Corrige la rotacion segun los metadatos EXIF del iPhone
                img = ImageOps.exif_transpose(img)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.mode else "RGB")
                salida = destino / (archivo.stem + ".png")
                img.save(salida, format="PNG")
            ok += 1
        except Exception as e:
            errores += 1
            log_callback(f"  Error con {archivo.name}: {e}")

    return ok, errores


class App:
    def __init__(self, root):
        self.root = root
        root.title("Conversor de fotos iPhone a PNG")
        root.geometry("480x380")
        root.resizable(False, False)

        self.label = tk.Label(
            root,
            text=TEXTO_INICIAL,
            font=("Segoe UI", 13),
            bg="#eef3fb",
            fg="#1a1a2e",
            relief="ridge",
            borderwidth=2,
            wraplength=420,
            justify="center",
            cursor="hand2",
        )
        self.label.pack(expand=True, fill="both", padx=20, pady=20)
        self.label.bind("<Button-1>", self.elegir_carpeta)

        self.log = tk.Text(root, height=8, state="disabled", bg="#f7f7f7")
        self.log.pack(fill="x", padx=20, pady=(0, 20))

        # Evita que se lancen dos conversiones a la vez (ver procesar()).
        self.procesando = False

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)

    def escribir(self, texto):
        # Se puede llamar desde el hilo de trabajo: Tkinter no es seguro entre
        # hilos, asi que delegamos la actualizacion real al hilo principal.
        self.root.after(0, self._escribir_ui, texto)

    def _escribir_ui(self, texto):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def elegir_carpeta(self, event=None):
        carpeta = filedialog.askdirectory(title="Elegi la carpeta con tus fotos")
        if carpeta:
            self.procesar(Path(carpeta))

    def on_drop(self, event):
        ruta = event.data.strip("{}")  # tkinterdnd2 puede envolver la ruta en {}
        carpeta = Path(ruta)
        if not carpeta.is_dir():
            messagebox.showwarning(
                "Eso no es una carpeta",
                "Arrastra una carpeta completa, no un archivo suelto.",
            )
            return
        self.procesar(carpeta)

    def procesar(self, carpeta: Path):
        # Ignora clicks/drops nuevos mientras ya hay una conversion en curso.
        if self.procesando:
            return
        self.procesando = True

        self.label.config(text=f"Procesando:\n{carpeta}")
        self.escribir(f"Carpeta elegida: {carpeta}")

        def trabajo():
            try:
                ok, errores = convertir_carpeta(carpeta, self.escribir)
                self.escribir(f"\nListo. Convertidas: {ok}  |  Con error: {errores}")
                self.root.after(0, self._finalizar_ok, carpeta, ok, errores)
            except Exception:
                self.escribir("Error inesperado:\n" + traceback.format_exc())
                self.root.after(0, self._finalizar_error)

        threading.Thread(target=trabajo, daemon=True).start()

    def _finalizar_ok(self, carpeta: Path, ok: int, errores: int):
        self.label.config(text=TEXTO_INICIAL)
        messagebox.showinfo(
            "Conversion terminada",
            f"Se convirtieron {ok} fotos a PNG.\n"
            f"Las vas a encontrar dentro de:\n{carpeta / 'PNG convertidas'}"
            + (f"\n\n{errores} archivo(s) no se pudieron convertir." if errores else ""),
        )
        self.procesando = False

    def _finalizar_error(self):
        self.label.config(text=TEXTO_INICIAL)
        messagebox.showerror(
            "Error", "Ocurrio un error inesperado. Revisa el detalle en la ventana."
        )
        self.procesando = False


def main():
    root = TkinterDnD.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
