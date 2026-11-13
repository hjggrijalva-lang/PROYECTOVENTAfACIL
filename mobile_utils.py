import os
import webbrowser
from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform


def es_android():
    return platform == "android"


def es_pantalla_movil():
    """Retorna True cuando la pantalla está en formato vertical de celular."""
    return Window.width < dp(650)


def get_data_dir():
    """Retorna el directorio persistente seguro en Android o la carpeta local en PC."""
    if es_android():
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            os.makedirs(app.user_data_dir, exist_ok=True)
            return app.user_data_dir
    return os.path.abspath(".")


def get_subdir(*partes):
    """Crea y retorna una subcarpeta dentro del almacenamiento seguro de la app."""
    ruta = os.path.join(get_data_dir(), *partes)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def seleccionar_imagen_dispositivo(callback_ruta, fallback_kivy_fn=None):
    """Abre la galería nativa en Android o el explorador en PC."""
    # 1. Intentar selector nativo multiplataforma (Android Gallery / Desktop)
    try:
        from plyer import filechooser

        def _on_selection(selection):
            if selection and len(selection) > 0 and os.path.exists(selection[0]):
                callback_ruta(selection[0])

        filechooser.open_file(
            title="Seleccionar imagen",
            filters=[["Imágenes", "*.png", "*.jpg", "*.jpeg", "*.webp"]],
            on_selection=_on_selection
        )
        return
    except Exception:
        pass

    # 2. Respaldo en PC con tkinter
    if not es_android():
        try:
            from tkinter import Tk, filedialog
            root_tk = Tk()
            root_tk.withdraw()
            root_tk.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                title="Seleccionar imagen",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                    ("Todos los archivos", "*.*")
                ]
            )
            root_tk.destroy()
            if ruta:
                callback_ruta(ruta)
            return
        except Exception:
            pass

    # 3. Respaldo interno Kivy
    if callable(fallback_kivy_fn):
        fallback_kivy_fn()


def compartir_o_abrir_archivo(ruta_archivo, titulo="Comprobante VentaFácil"):
    """Comparte el comprobante en Android (WhatsApp/Impresora/PDF) o lo abre en PC."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return

    if es_android():
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            File = autoclass("java.io.File")
            StrictMode = autoclass("android.os.StrictMode")
            VmPolicyBuilder = autoclass("android.os.StrictMode$VmPolicy$Builder")

            StrictMode.setVmPolicy(VmPolicyBuilder().build())

            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/html")
            uri = Uri.fromFile(File(ruta_archivo))
            intent.putExtra(Intent.EXTRA_STREAM, uri)
            intent.putExtra(Intent.EXTRA_SUBJECT, titulo)

            chooser = Intent.createChooser(intent, titulo)
            PythonActivity.mActivity.startActivity(chooser)
            return
        except Exception:
            pass

    uri = "file:///" + os.path.abspath(ruta_archivo).replace("\\", "/")
    webbrowser.open(uri)