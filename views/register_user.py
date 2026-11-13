from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import database


class PinDigitField(MDTextField):
    """Campo individual para 1 dígito de PIN con retroceso inteligente."""
    def __init__(self, prev_field=None, **kwargs):
        super().__init__(**kwargs)
        self.prev_field = prev_field

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "backspace" and not self.text and self.prev_field is not None:
            self.prev_field.text = ""
            self.prev_field.focus = True
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


class RegisterUserScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._updating_pin = False
        self.dialog = None
        self.password_visible = False
        self.rol_seleccionado = "admin"

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.98, 0.98, 0.99, 1))

        # Barra superior
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(6), dp(16), dp(6)]
        )
        btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.ir_a_login()
        )
        lbl_header = MDLabel(
            text="Crear Nuevo Usuario",
            font_style="H6",
            bold=True,
            pos_hint={"center_y": 0.5}
        )
        top_bar.add_widget(btn_back)
        top_bar.add_widget(lbl_header)
        root.add_widget(top_bar)

        # Contenido desplazable
        scroll = MDScrollView()
        container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(48), dp(10), dp(48), dp(28)],
            spacing=dp(12),
            size_hint_y=None
        )
        container.bind(minimum_height=container.setter("height"))

        # 1. Nombre y Apellido
        container.add_widget(self._crear_etiqueta("Nombre y Apellido"))
        self.input_nombre = MDTextField(
            hint_text="Ej. Henry Pérez",
            mode="round",
            icon_left="account-outline",
            size_hint_y=None,
            height=dp(48)
        )
        container.add_widget(self.input_nombre)

        # 2. Nombre del Negocio
        container.add_widget(self._crear_etiqueta("Nombre de tu Negocio / Tienda"))
        self.input_negocio = MDTextField(
            hint_text="Ej. Abarrotes Henry",
            mode="round",
            icon_left="storefront-outline",
            size_hint_y=None,
            height=dp(48)
        )
        container.add_widget(self.input_negocio)

        # 3. Selector de Rol (Administrador / Cajero)
        container.add_widget(self._crear_etiqueta("Tipo de Usuario (Rol)"))
        roles_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(44)
        )
        self.btn_rol_admin = MDFillRoundFlatButton(
            text="Administrador",
            icon="shield-account",
            size_hint_x=0.5,
            height=dp(44),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self.seleccionar_rol("admin")
        )
        self.btn_rol_cajero = MDFillRoundFlatButton(
            text="Cajero",
            icon="account-cash",
            size_hint_x=0.5,
            height=dp(44),
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.22, 1),
            on_release=lambda x: self.seleccionar_rol("cajero")
        )
        roles_row.add_widget(self.btn_rol_admin)
        roles_row.add_widget(self.btn_rol_cajero)
        container.add_widget(roles_row)

        self.lbl_rol_desc = MDLabel(
            text="Acceso total: Dashboard, Inventario, Precios, Reportes y Usuarios.",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(20)
        )
        container.add_widget(self.lbl_rol_desc)

        # 4. Correo electrónico o Teléfono
        container.add_widget(self._crear_etiqueta("Correo electrónico o Teléfono"))
        self.input_email = MDTextField(
            hint_text="Ej. henry@hotmail.com",
            mode="round",
            icon_left="email-outline",
            size_hint_y=None,
            height=dp(48)
        )
        container.add_widget(self.input_email)

        # 5. Contraseña
        pass_header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        pass_header.add_widget(MDLabel(text="Contraseña", font_style="Subtitle2", bold=True))
        pass_header.add_widget(
            MDLabel(
                text="Mínimo 8 caracteres",
                font_style="Caption",
                halign="right",
                theme_text_color="Hint"
            )
        )
        container.add_widget(pass_header)

        pass_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(48)
        )
        self.input_password = MDTextField(
            hint_text="Ingresa tu contraseña",
            mode="round",
            icon_left="lock-outline",
            password=True,
            size_hint_y=None,
            height=dp(48)
        )
        self.input_password.bind(text=self.actualizar_fuerza_password)

        self.btn_toggle_pass = MDIconButton(
            icon="eye-off-outline",
            pos_hint={"center_y": 0.5},
            on_release=self.alternar_ver_password
        )
        pass_row.add_widget(self.input_password)
        pass_row.add_widget(self.btn_toggle_pass)
        container.add_widget(pass_row)

        # Barra de fortaleza de contraseña
        strength_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(5)
        )
        self.strength_bars = []
        for _ in range(4):
            bar = MDBoxLayout(md_bg_color=(0.85, 0.87, 0.89, 1))
            self.strength_bars.append(bar)
            strength_row.add_widget(bar)
        container.add_widget(strength_row)

        # 6. PIN de 4 dígitos separados
        pin_title_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(28),
            padding=[0, dp(4), 0, 0]
        )
        pin_icon = MDIconButton(
            icon="shield-key-outline",
            icon_size="20sp",
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            disabled=True
        )
        pin_title_row.add_widget(pin_icon)
        pin_title_row.add_widget(
            MDLabel(
                text="PIN de Acceso Rápido para Caja / POS",
                font_style="Subtitle2",
                bold=True
            )
        )
        container.add_widget(pin_title_row)

        container.add_widget(
            MDLabel(
                text="Para desbloquear el punto de venta en segundos (4 dígitos)",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(20)
            )
        )

        pin_wrapper = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            padding=[0, dp(4), 0, dp(4)]
        )
        pin_wrapper.add_widget(MDBoxLayout())

        pin_boxes_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(14),
            size_hint=(None, None),
            size=(dp(266), dp(54))
        )

        self.pin_fields = []
        prev = None
        for i in range(4):
            field = PinDigitField(
                prev_field=prev,
                mode="round",
                halign="center",
                font_size="20sp",
                input_filter="int",
                size_hint=(None, None),
                size=(dp(56), dp(54))
            )
            field.bind(text=lambda inst, val, idx=i: self.on_pin_text(idx, inst, val))
            self.pin_fields.append(field)
            pin_boxes_row.add_widget(field)
            prev = field

        pin_wrapper.add_widget(pin_boxes_row)
        pin_wrapper.add_widget(MDBoxLayout())
        container.add_widget(pin_wrapper)

        # 7. Botón Registrar
        btn_registrar = MDFillRoundFlatButton(
            text="REGISTRAR USUARIO",
            font_size="15sp",
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            on_release=self.procesar_registro
        )
        container.add_widget(btn_registrar)

        # 8. Enlace a Iniciar Sesión
        login_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(4)
        )
        login_row.add_widget(MDBoxLayout())
        login_row.add_widget(
            MDLabel(
                text="¿Ya tienes cuenta?",
                font_style="Body2",
                theme_text_color="Secondary",
                size_hint_x=None,
                width=dp(130)
            )
        )
        btn_login = MDFlatButton(
            text="Iniciar Sesión",
            theme_text_color="Custom",
            text_color=(0.10, 0.45, 0.85, 1),
            on_release=lambda x: self.ir_a_login()
        )
        login_row.add_widget(btn_login)
        login_row.add_widget(MDBoxLayout())
        container.add_widget(login_row)

        scroll.add_widget(container)
        root.add_widget(scroll)
        self.add_widget(root)

    def _crear_etiqueta(self, texto):
        return MDLabel(
            text=texto,
            font_style="Subtitle2",
            bold=True,
            size_hint_y=None,
            height=dp(22)
        )

    def seleccionar_rol(self, rol):
        self.rol_seleccionado = rol
        if rol == "admin":
            self.btn_rol_admin.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_rol_admin.text_color = (1, 1, 1, 1)
            self.btn_rol_cajero.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_rol_cajero.text_color = (0.20, 0.25, 0.22, 1)
            self.lbl_rol_desc.text = "Acceso total: Dashboard, Inventario, Precios, Reportes y Usuarios."
        else:
            self.btn_rol_cajero.md_bg_color = (0.13, 0.52, 0.89, 1)
            self.btn_rol_cajero.text_color = (1, 1, 1, 1)
            self.btn_rol_admin.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_rol_admin.text_color = (0.20, 0.25, 0.22, 1)
            self.lbl_rol_desc.text = "Acceso operativo: Punto de Venta (POS), Cobros y Cierre de Caja."

    def alternar_ver_password(self, *args):
        self.password_visible = not self.password_visible
        self.input_password.password = not self.password_visible
        self.btn_toggle_pass.icon = "eye-outline" if self.password_visible else "eye-off-outline"

    def actualizar_fuerza_password(self, instance, texto):
        longitud = len(texto)
        activos = 0
        if longitud >= 1:
            activos = 1
        if longitud >= 4:
            activos = 2
        if longitud >= 6:
            activos = 3
        if longitud >= 8:
            activos = 4

        color_activo = (0.13, 0.55, 0.25, 1) if activos == 4 else (0.90, 0.55, 0.15, 1)
        color_inactivo = (0.85, 0.87, 0.89, 1)

        for idx, bar in enumerate(self.strength_bars):
            bar.md_bg_color = color_activo if idx < activos else color_inactivo

    def on_pin_text(self, index, instance, value):
        if self._updating_pin:
            return
        self._updating_pin = True
        try:
            digitos = "".join(ch for ch in value if ch.isdigit())
            if not digitos:
                instance.text = ""
                return

            if len(digitos) > 1:
                idx = index
                for d in digitos:
                    if idx < 4:
                        self.pin_fields[idx].text = d
                        idx += 1
                if idx < 4:
                    self.pin_fields[idx].focus = True
                else:
                    self.pin_fields[3].focus = False
            else:
                instance.text = digitos
                if index < 3:
                    self.pin_fields[index + 1].focus = True
                else:
                    instance.focus = False
        finally:
            self._updating_pin = False

    def procesar_registro(self, *args):
        nombre = self.input_nombre.text.strip()
        negocio = self.input_negocio.text.strip()
        email = self.input_email.text.strip()
        password = self.input_password.text.strip()
        pin = "".join(f.text.strip() for f in self.pin_fields)

        if not nombre or not negocio or not email:
            self.mostrar_dialogo(
                "Campos Incompletos",
                "Por favor completa tu Nombre, el Nombre de tu Negocio y tu Correo o Teléfono."
            )
            return

        if len(password) < 8:
            self.mostrar_dialogo(
                "Contraseña muy corta",
                "La contraseña debe tener al menos 8 caracteres."
            )
            return

        if len(pin) != 4 or not pin.isdigit():
            self.mostrar_dialogo(
                "PIN Incompleto",
                "Ingresa los 4 dígitos numéricos para tu PIN de acceso rápido al POS."
            )
            return

        exito, mensaje = database.register_usuario(
            nombre, negocio, email, password, pin, rol=self.rol_seleccionado
        )

        if exito:
            rol_nombre = "Administrador" if self.rol_seleccionado == "admin" else "Cajero"
            self.limpiar_formulario()
            self.mostrar_dialogo(
                "¡Usuario Registrado!",
                f"{mensaje}\n\n• Rol asignado: {rol_nombre}\n• PIN de acceso rápido: {pin}",
                ir_login=True
            )
        else:
            self.mostrar_dialogo("No se pudo registrar", mensaje)

    def limpiar_formulario(self):
        self.input_nombre.text = ""
        self.input_negocio.text = ""
        self.input_email.text = ""
        self.input_password.text = ""
        self.seleccionar_rol("admin")
        self._updating_pin = True
        for f in self.pin_fields:
            f.text = ""
        self._updating_pin = False

    def mostrar_dialogo(self, titulo, texto, ir_login=False):
        def cerrar(inst):
            self.dialog.dismiss()
            if ir_login:
                self.ir_a_login()

        self.dialog = MDDialog(
            title=titulo,
            text=texto,
            buttons=[
                MDFillRoundFlatButton(
                    text="CONTINUAR" if ir_login else "ENTENDIDO",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=cerrar
                )
            ]
        )
        self.dialog.open()

    def ir_a_login(self):
        if not self.manager:
            return
        for nombre in ("login", "welcome", "dashboard"):
            if nombre in self.manager.screen_names:
                self.manager.current = nombre
                return


RegisterScreen = RegisterUserScreen