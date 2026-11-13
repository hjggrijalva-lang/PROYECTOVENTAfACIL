from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import Screen


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        anchor = MDAnchorLayout(anchor_x="center", anchor_y="center")
        
        main_layout = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=("300dp", "420dp"),
            spacing="20dp",
            padding="20dp",
        )

        # Branding
        title = MDLabel(
            text="Venta Fácil",
            font_style="H4",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=(0.18, 0.44, 0.20, 1),
        )

        subtitle = MDLabel(
            text="Tu negocio, más simple",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Secondary",
        )

        # Botones
        btn_login = MDFillRoundFlatButton(
            text="Iniciar sesión  >",
            size_hint=(1, None),
            height="48dp",
            md_bg_color=(0.18, 0.44, 0.20, 1),
            on_release=self.go_to_login,
        )

        btn_register = MDRoundFlatButton(
            text="Crear cuenta",
            size_hint=(1, None),
            height="48dp",
            line_color=(0.7, 0.7, 0.7, 1),
            text_color=(0.2, 0.2, 0.2, 1),
            on_release=self.go_to_register,
        )

        main_layout.add_widget(title)
        main_layout.add_widget(subtitle)
        main_layout.add_widget(btn_login)
        main_layout.add_widget(btn_register)

        anchor.add_widget(main_layout)
        self.add_widget(anchor)

    def go_to_login(self, *args):
        if self.manager.has_screen("login"):
            self.manager.current = "login"
        else:
            print("Pantalla de Login aún no registrada.")

    def go_to_register(self, *args):
        if self.manager.has_screen("register"):
            self.manager.current = "register"
        else:
            print("Pantalla de Registro aún no registrada.")