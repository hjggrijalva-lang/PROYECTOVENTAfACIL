from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line


class CartLogoIcon(Widget):
    """Ícono del carrito verde con las líneas de velocidad y el check."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            cx = self.center_x
            cy = self.center_y

            # Líneas de movimiento (velocidad)
            Color(0.12, 0.58, 0.28, 1)
            Line(points=[cx - 48, cy + 18, cx - 32, cy + 18], width=3.5, cap="round")
            Line(points=[cx - 42, cy + 6, cx - 28, cy + 6], width=3.5, cap="round")
            Line(points=[cx - 38, cy - 6, cx - 26, cy - 6], width=3.5, cap="round")

            # Estructura del Carrito
            Color(0.12, 0.58, 0.28, 1)
            Line(
                points=[
                    cx - 22, cy + 22,
                    cx - 12, cy + 22,
                    cx - 2, cy - 10,
                    cx + 28, cy - 10,
                    cx + 38, cy + 18,
                    cx - 12, cy + 18
                ],
                width=4.5,
                joint="round",
                cap="round"
            )
            # Ruedas
            Ellipse(pos=(cx - 5, cy - 22), size=(10, 10))
            Ellipse(pos=(cx + 20, cy - 22), size=(10, 10))

            # Círculo verde con Check de verificación
            Color(0.12, 0.58, 0.28, 1)
            Ellipse(pos=(cx + 14, cy - 18), size=(30, 30))

            Color(1, 1, 1, 1)
            Line(
                points=[
                    cx + 21, cy - 4,
                    cx + 27, cy - 10,
                    cx + 36, cy - 1
                ],
                width=3.5,
                cap="round",
                joint="round"
            )


class StoreIllustration(Widget):
    """Ilustración vectorial completa y detallada de la tienda estilo 3D suave."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            cx = self.center_x
            cy = self.center_y - 10

            # 1. NUBES DE FONDO (Ondas pastel verde y azul)
            Color(0.82, 0.94, 0.85, 0.9)  # Verde suave
            Ellipse(pos=(cx - 160, cy - 20), size=(180, 120))
            Color(0.82, 0.90, 0.98, 0.9)  # Azul suave
            Ellipse(pos=(cx - 10, cy - 30), size=(180, 110))

            # Base/Suelo de la tienda
            Color(0.92, 0.93, 0.94, 1)
            RoundedRectangle(pos=(cx - 105, cy - 80), size=(210, 15), radius=[4])

            # Escalón de entrada
            Color(0.85, 0.86, 0.88, 1)
            RoundedRectangle(pos=(cx - 75, cy - 68), size=(36, 6), radius=[2])

            # 2. ESTRUCTURA DE LA TIENDA (Paredes)
            Color(0.97, 0.96, 0.93, 1)  # Blanco cálido/crema
            RoundedRectangle(pos=(cx - 95, cy - 65), size=(190, 105), radius=[6])

            # 3. TOLDO DE FRUCTERÍA / TIENDA (Techo a franjas)
            stripes = 8
            stripe_w = 200 / stripes
            
            # Sombra debajo del toldo
            Color(0, 0, 0, 0.08)
            RoundedRectangle(pos=(cx - 102, cy + 28), size=(204, 12), radius=[6])

            # Franjas curvas del toldo
            for i in range(stripes):
                x_pos = cx - 100 + (i * stripe_w)
                if i % 2 == 0:
                    Color(0.18, 0.62, 0.28, 1)  # Verde vibrante
                else:
                    Color(0.98, 0.98, 0.98, 1)  # Blanco puro

                # Franja con bordes redondeados abajo
                RoundedRectangle(
                    pos=(x_pos, cy + 32),
                    size=(stripe_w, 32),
                    radius=[0, 0, 8, 8]
                )

            # Tejado verde superior
            Color(0.15, 0.52, 0.22, 1)
            RoundedRectangle(pos=(cx - 102, cy + 58), size=(204, 12), radius=[6])

            # 4. PUERTA PRINCIPAL (Verde Esmeralda)
            Color(0.18, 0.55, 0.45, 1)
            RoundedRectangle(pos=(cx - 78, cy - 65), size=(42, 75), radius=[4])
            
            # Marco interior y cristal de la puerta
            Color(0.85, 0.96, 0.96, 1)
            RoundedRectangle(pos=(cx - 72, cy - 30), size=(30, 34), radius=[2])
            Color(0.18, 0.55, 0.45, 1)
            Line(points=[cx - 57, cy - 30, cx - 57, cy + 4], width=1.2)

            # Manija de la puerta
            Color(0.9, 0.9, 0.9, 1)
            Ellipse(pos=(cx - 42, cy - 40), size=(4, 4))

            # 5. VENTANALES (3 Ventanas verticales)
            win_width = 24
            win_height = 42
            win_positions = [cx - 24, cx + 8, cx + 40]

            for wx in win_positions:
                # Marco exterior
                Color(0.18, 0.52, 0.62, 1)
                RoundedRectangle(pos=(wx, cy - 20), size=(win_width, win_height), radius=[3])
                # Cristal
                Color(0.82, 0.94, 0.98, 1)
                RoundedRectangle(pos=(wx + 2, cy - 18), size=(win_width - 4, win_height - 4), radius=[2])
                # Repisa inferior
                Color(0.12, 0.42, 0.52, 1)
                RoundedRectangle(pos=(wx - 2, cy - 22), size=(win_width + 4, 4), radius=[1])

            # 6. CAJA REGISTRADORA / MOSTRADOR EN EL FRENTE
            # Base del terminal
            Color(0.12, 0.22, 0.42, 1)
            RoundedRectangle(pos=(cx + 18, cy - 70), size=(55, 30), radius=[4])
            # Pantalla inclinada
            Color(0.22, 0.45, 0.72, 1)
            RoundedRectangle(pos=(cx + 28, cy - 50), size=(28, 22), radius=[3])
            # Pantalla encendida
            Color(0.85, 0.95, 1, 1)
            Rectangle(pos=(cx + 31, cy - 47), size=(22, 16))
            # Botones / Teclado
            Color(0.8, 0.85, 0.9, 1)
            Rectangle(pos=(cx + 24, cy - 65), size=(22, 8))

            # 7. MACETAS DE PLANTAS LATERALES
            # Maceta Izquierda
            Color(0.18, 0.28, 0.38, 1)
            RoundedRectangle(pos=(cx - 122, cy - 72), size=(22, 26), radius=[3])
            Color(0.22, 0.65, 0.28, 1)
            Ellipse(pos=(cx - 128, cy - 54), size=(34, 40))

            # Maceta Derecha
            Color(0.18, 0.28, 0.38, 1)
            RoundedRectangle(pos=(cx + 100, cy - 72), size=(22, 26), radius=[3])
            Color(0.22, 0.65, 0.28, 1)
            Ellipse(pos=(cx + 94, cy - 54), size=(34, 40))


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(
            orientation="vertical",
            padding=["24dp", "20dp", "24dp", "30dp"],
            spacing="10dp"
        )

        # 1. ENCABEZADO
        header_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="145dp",
            spacing="2dp"
        )

        cart_icon = CartLogoIcon(
            size_hint=(None, None),
            size=("100dp", "70dp"),
            pos_hint={"center_x": 0.5}
        )

        title_box = MDBoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=("220dp", "38dp"),
            pos_hint={"center_x": 0.5}
        )
        lbl_venta = MDLabel(
            text="Venta ",
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.08, 0.2, 0.4, 1),
            halign="right"
        )
        lbl_facil = MDLabel(
            text="Fácil",
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.12, 0.58, 0.28, 1),
            halign="left"
        )
        title_box.add_widget(lbl_venta)
        title_box.add_widget(lbl_facil)

        slogan = MDLabel(
            text="Tu negocio, más simple",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.35, 1)
        )

        header_box.add_widget(cart_icon)
        header_box.add_widget(title_box)
        header_box.add_widget(slogan)

        # 2. ILUSTRACIÓN DE TIENDA COMPLETA
        illustration = StoreIllustration(size_hint=(1, 1))

        # 3. BOTONES DE ACCIÓN
        buttons_box = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="110dp"
        )

        btn_login = MDFillRoundFlatButton(
            text="Iniciar sesión  >",
            size_hint=(1, None),
            height="48dp",
            md_bg_color=(0.12, 0.58, 0.28, 1),
            font_size="16sp",
            on_release=self.go_to_login
        )

        btn_register = MDRoundFlatButton(
            text="Crear cuenta",
            size_hint=(1, None),
            height="48dp",
            line_color=(0.12, 0.58, 0.28, 1),
            text_color=(0.08, 0.2, 0.4, 1),
            font_size="16sp",
            on_release=self.go_to_register
        )

        buttons_box.add_widget(btn_login)
        buttons_box.add_widget(btn_register)

        layout.add_widget(header_box)
        layout.add_widget(illustration)
        layout.add_widget(buttons_box)

        self.add_widget(layout)

    def go_to_login(self, *args):
        self.manager.current = "login"

    def go_to_register(self, *args):
        self.manager.current = "register"