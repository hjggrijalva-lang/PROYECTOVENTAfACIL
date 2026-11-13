import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modo_login = "pin"
        self.usuario_seleccionado = None
        self.dialog = None
        self.confirm_dialog = None

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.95, 0.96, 0.98, 1))

        # ---------------------------------------------------------
        # 1. BARRA SUPERIOR (Header)
        # ---------------------------------------------------------
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            padding=[dp(8), dp(6), dp(12), dp(6)],
            spacing=dp(6),
            md_bg_color=(1, 1, 1, 1)
        )
        btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.volver_inicio()
        )
        lbl_header = MDLabel(
            text="Iniciar Sesión • VentaFácil",
            font_style="Subtitle1",
            bold=True,
            shorten=True,
            pos_hint={"center_y": 0.5}
        )
        btn_nuevo_user = MDRoundFlatButton(
            text="+ Nuevo Usuario",
            font_size="12sp",
            line_color=(0.13, 0.55, 0.25, 1),
            text_color=(0.13, 0.55, 0.25, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.ir_a_pantalla("register")
        )

        header.add_widget(btn_back)
        header.add_widget(lbl_header)
        header.add_widget(btn_nuevo_user)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CONTENIDO DESPLAZABLE
        # ---------------------------------------------------------
        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12), dp(16), dp(24)],
            spacing=dp(12),
            size_hint_y=None
        )
        body.bind(minimum_height=body.setter("height"))

        # --- BANNER DE MARCA (VENTA FÁCIL • TU NEGOCIO, MÁS SIMPLE) ---
        brand_card = MDCard(
            orientation="horizontal",
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(12),
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(88)
        )

        ruta_logo = self._buscar_logo_marca()
        if ruta_logo:
            img_brand = Image(source=ruta_logo, fit_mode="contain")
            img_brand.reload()
            brand_card.add_widget(img_brand)
        else:
            # Emblema izquierdo: Tienda con toldo verde
            store_badge = MDCard(
                size_hint=(None, None),
                size=(dp(60), dp(60)),
                radius=[dp(14)],
                elevation=0,
                md_bg_color=(0.91, 0.97, 0.93, 1),
                pos_hint={"center_y": 0.5}
            )
            store_badge.add_widget(
                MDIconButton(
                    icon="storefront",
                    icon_size="34sp",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.58, 0.28, 1),
                    size_hint=(1, 1),
                    disabled=True
                )
            )

            # Centro: Carrito con check + Título bicolor Venta Fácil + Lema
            brand_center = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5}
            )
            title_row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint_y=None,
                height=dp(30)
            )
            cart_icon = MDIconButton(
                icon="cart-check",
                icon_size="24sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.58, 0.28, 1),
                size_hint=(None, None),
                size=(dp(26), dp(26)),
                pos_hint={"center_y": 0.5},
                disabled=True
            )
            lbl_brand_title = MDLabel(
                text="[b][color=#142D55]Venta[/color] [color=#218C40]Fácil[/color][/b]",
                markup=True,
                font_style="H6",
                pos_hint={"center_y": 0.5}
            )
            title_row.add_widget(cart_icon)
            title_row.add_widget(lbl_brand_title)

            lbl_slogan = MDLabel(
                text="Tu negocio, más simple",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(18)
            )
            brand_center.add_widget(title_row)
            brand_center.add_widget(lbl_slogan)

            brand_card.add_widget(store_badge)
            brand_card.add_widget(brand_center)

        body.add_widget(brand_card)

        # --- ENCABEZADO USUARIOS REGISTRADOS ---
        users_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(22)
        )
        users_header.add_widget(
            MDLabel(
                text="Usuarios Registrados (toca uno)",
                font_style="Caption",
                bold=True,
                size_hint_x=0.62
            )
        )
        users_header.add_widget(
            MDLabel(
                text="Acceso PIN o Correo",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_x=0.38
            )
        )
        body.add_widget(users_header)

        # Lista horizontal de tarjetas de usuarios
        users_scroll = MDScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(78)
        )
        self.users_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_x=None,
            padding=[dp(2), dp(4), dp(2), dp(4)]
        )
        self.users_row.bind(minimum_width=self.users_row.setter("width"))
        users_scroll.add_widget(self.users_row)
        body.add_widget(users_scroll)

        # --- BOTONES DE MODO DE ACCESO (PIN / CORREO) ---
        tabs_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(42)
        )
        self.btn_tab_pin = MDFillRoundFlatButton(
            text="Ingresar con PIN",
            font_size="13sp",
            size_hint_x=0.5,
            height=dp(40),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self.cambiar_modo_login("pin")
        )
        self.btn_tab_correo = MDFillRoundFlatButton(
            text="Correo y Contraseña",
            font_size="13sp",
            size_hint_x=0.5,
            height=dp(40),
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.22, 1),
            on_release=lambda x: self.cambiar_modo_login("correo")
        )
        tabs_row.add_widget(self.btn_tab_pin)
        tabs_row.add_widget(self.btn_tab_correo)
        body.add_widget(tabs_row)

        # --- CONTENEDOR DINÁMICO (TECLADO PIN O FORMULARIO CORREO) ---
        self.auth_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )
        self.auth_container.bind(minimum_height=self.auth_container.setter("height"))
        body.add_widget(self.auth_container)

        self._construir_panel_pin()
        self._construir_panel_correo()

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _buscar_logo_marca(self):
        carpetas = [
            os.path.join(os.path.abspath("."), "assets"),
            mobile_utils.get_subdir("assets"),
        ]
        for carpeta in carpetas:
            for nombre in ("welcome_banner.png", "logo_banner.png", "logo.png", "logo.jpg"):
                ruta = os.path.join(carpeta, nombre)
                if os.path.exists(ruta):
                    return ruta
        return ""

    # ---------------------------------------------------------
    # PANEL DE ACCESO POR PIN DE 4 DÍGITOS
    # ---------------------------------------------------------
    def _construir_panel_pin(self):
        self.panel_pin = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )
        self.panel_pin.bind(minimum_height=self.panel_pin.setter("height"))

        self.lbl_pin_titulo = MDLabel(
            text="Ingresa tu PIN de 4 dígitos",
            font_style="Subtitle1",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(24)
        )
        self.panel_pin.add_widget(self.lbl_pin_titulo)

        self.input_pin = MDTextField(
            hint_text="PIN de 4 dígitos",
            mode="round",
            password=True,
            max_text_length=4,
            input_filter="int",
            halign="center",
            font_size="18sp",
            size_hint_y=None,
            height=dp(48),
            fill_color_normal=(1, 1, 1, 1)
        )
        self.input_pin.bind(text=self.on_pin_text_change)
        self.panel_pin.add_widget(self.input_pin)

        # Teclado numérico táctil 3x4
        keypad = MDGridLayout(
            cols=3,
            spacing=dp(10),
            size_hint=(None, None),
            size=(dp(276), dp(220)),
            pos_hint={"center_x": 0.5}
        )

        teclas = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for t in teclas:
            btn_num = MDRoundFlatButton(
                text=t,
                font_size="18sp",
                size_hint=(None, None),
                size=(dp(84), dp(46)),
                line_color=(0.75, 0.78, 0.82, 1),
                text_color=(0.15, 0.20, 0.25, 1),
                on_release=lambda x, dig=t: self.agregar_digito_pin(dig)
            )
            keypad.add_widget(btn_num)

        btn_limpiar = MDRoundFlatButton(
            text="Limpiar",
            font_size="13sp",
            size_hint=(None, None),
            size=(dp(84), dp(46)),
            line_color=(0.75, 0.78, 0.82, 1),
            text_color=(0.35, 0.40, 0.45, 1),
            on_release=lambda x: setattr(self.input_pin, "text", "")
        )
        btn_cero = MDRoundFlatButton(
            text="0",
            font_size="18sp",
            size_hint=(None, None),
            size=(dp(84), dp(46)),
            line_color=(0.75, 0.78, 0.82, 1),
            text_color=(0.15, 0.20, 0.25, 1),
            on_release=lambda x: self.agregar_digito_pin("0")
        )
        btn_borrar = MDIconButton(
            icon="backspace-outline",
            icon_size="24sp",
            theme_text_color="Custom",
            text_color=(0.85, 0.22, 0.22, 1),
            size_hint=(None, None),
            size=(dp(84), dp(46)),
            on_release=lambda x: self.borrar_ultimo_digito()
        )

        keypad.add_widget(btn_limpiar)
        keypad.add_widget(btn_cero)
        keypad.add_widget(btn_borrar)
        self.panel_pin.add_widget(keypad)

    # ---------------------------------------------------------
    # PANEL DE ACCESO POR CORREO Y CONTRASEÑA
    # ---------------------------------------------------------
    def _construir_panel_correo(self):
        self.panel_correo = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None
        )
        self.panel_correo.bind(minimum_height=self.panel_correo.setter("height"))

        self.input_email = MDTextField(
            hint_text="Correo electrónico o teléfono",
            mode="round",
            icon_left="email-outline",
            size_hint_y=None,
            height=dp(48),
            fill_color_normal=(1, 1, 1, 1)
        )
        self.input_password = MDTextField(
            hint_text="Contraseña",
            mode="round",
            icon_left="lock-outline",
            password=True,
            size_hint_y=None,
            height=dp(48),
            fill_color_normal=(1, 1, 1, 1)
        )
        btn_entrar = MDFillRoundFlatButton(
            text="INICIAR SESIÓN",
            icon="login",
            font_size="14sp",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            on_release=self.autenticar_por_correo
        )

        self.panel_correo.add_widget(self.input_email)
        self.panel_correo.add_widget(self.input_password)
        self.panel_correo.add_widget(btn_entrar)

    # ---------------------------------------------------------
    # GESTIÓN DE USUARIOS Y AUTENTICACIÓN
    # ---------------------------------------------------------
    def on_pre_enter(self, *args):
        self.usuario_seleccionado = None
        self.lbl_pin_titulo.text = "Ingresa tu PIN de 4 dígitos"
        self.input_pin.text = ""
        self.input_password.text = ""
        self.cargar_usuarios_registrados()
        self.cambiar_modo_login("pin")

    def cargar_usuarios_registrados(self):
        self.users_row.clear_widgets()
        usuarios = database.get_usuarios()

        for u in usuarios:
            es_admin = (u.get("rol") != "cajero")
            seleccionado = (self.usuario_seleccionado and self.usuario_seleccionado.get("id") == u["id"])

            card = MDCard(
                orientation="horizontal",
                size_hint=(None, None),
                size=(dp(210), dp(66)),
                padding=[dp(10), dp(6), dp(4), dp(6)],
                spacing=dp(8),
                radius=[dp(14)],
                elevation=1,
                md_bg_color=(0.91, 0.97, 0.93, 1) if seleccionado else (1, 1, 1, 1),
                line_color=(0.13, 0.55, 0.25, 1) if seleccionado else (0.85, 0.87, 0.90, 1),
                on_release=lambda x, usr=u: self.seleccionar_usuario_tarjeta(usr)
            )

            ic_rol = MDIconButton(
                icon="shield-account" if es_admin else "card-account-details-outline",
                icon_size="24sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.55, 0.25, 1) if es_admin else (0.45, 0.50, 0.55, 1),
                size_hint=(None, None),
                size=(dp(30), dp(30)),
                pos_hint={"center_y": 0.5},
                disabled=True
            )

            info = MDBoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
            info.add_widget(
                MDLabel(text=u["nombre"], font_style="Subtitle2", bold=True, shorten=True)
            )
            rol_txt = "Admin" if es_admin else "Cajero"
            info.add_widget(
                MDLabel(
                    text=f"{u['negocio']} • {rol_txt}",
                    font_style="Caption",
                    theme_text_color="Secondary",
                    shorten=True
                )
            )

            btn_del = MDIconButton(
                icon="trash-can-outline",
                icon_size="19sp",
                theme_text_color="Custom",
                text_color=(0.85, 0.22, 0.22, 1),
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, usr=u: self.confirmar_eliminar_usuario(usr)
            )

            card.add_widget(ic_rol)
            card.add_widget(info)
            card.add_widget(btn_del)
            self.users_row.add_widget(card)

    def seleccionar_usuario_tarjeta(self, usuario):
        self.usuario_seleccionado = usuario
        self.lbl_pin_titulo.text = f"PIN de {usuario['nombre']} (4 dígitos)"
        self.input_email.text = usuario.get("email", "")
        self.input_pin.text = ""
        self.cargar_usuarios_registrados()

    def confirmar_eliminar_usuario(self, usuario):
        def ejecutar_eliminacion(inst):
            exito, mensaje = database.delete_usuario(usuario["id"])
            self.confirm_dialog.dismiss()
            if exito:
                if self.usuario_seleccionado and self.usuario_seleccionado.get("id") == usuario["id"]:
                    self.usuario_seleccionado = None
                    self.lbl_pin_titulo.text = "Ingresa tu PIN de 4 dígitos"
                self.cargar_usuarios_registrados()
            else:
                self._mostrar_alerta("No se pudo eliminar", mensaje)

        self.confirm_dialog = MDDialog(
            title="Eliminar Usuario",
            text=f"¿Deseas eliminar a '{usuario['nombre']}' ({usuario.get('rol', 'admin')})?",
            size_hint_x=0.90,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.confirm_dialog.dismiss()),
                MDFillRoundFlatButton(
                    text="ELIMINAR",
                    md_bg_color=(0.85, 0.22, 0.22, 1),
                    on_release=ejecutar_eliminacion
                )
            ]
        )
        self.confirm_dialog.open()

    def cambiar_modo_login(self, modo):
        self.modo_login = modo
        self.auth_container.clear_widgets()

        if modo == "pin":
            self.btn_tab_pin.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_tab_pin.text_color = (1, 1, 1, 1)
            self.btn_tab_correo.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_tab_correo.text_color = (0.20, 0.25, 0.22, 1)
            self.auth_container.add_widget(self.panel_pin)
        else:
            self.btn_tab_correo.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_tab_correo.text_color = (1, 1, 1, 1)
            self.btn_tab_pin.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_tab_pin.text_color = (0.20, 0.25, 0.22, 1)
            self.auth_container.add_widget(self.panel_correo)

    def agregar_digito_pin(self, digito):
        if len(self.input_pin.text) < 4:
            self.input_pin.text += digito

    def borrar_ultimo_digito(self):
        if self.input_pin.text:
            self.input_pin.text = self.input_pin.text[:-1]

    def on_pin_text_change(self, instance, texto):
        if len(texto.strip()) == 4:
            self.autenticar_por_pin()

    def autenticar_por_pin(self):
        pin = self.input_pin.text.strip()
        if len(pin) != 4:
            return

        usuario_valido = database.login_pin(pin)
        self.input_pin.text = ""

        if usuario_valido:
            self.iniciar_sesion_exitosa(usuario_valido)
        else:
            self._mostrar_alerta("PIN Incorrecto", "El PIN ingresado no corresponde a ningún usuario registrado.")

    def autenticar_por_correo(self, *args):
        email = self.input_email.text.strip()
        password = self.input_password.text.strip()

        if not email or not password:
            self._mostrar_alerta("Datos incompletos", "Ingresa tu correo/teléfono y tu contraseña.")
            return

        usuario_valido = database.login_usuario(email, password)
        if usuario_valido:
            self.input_password.text = ""
            self.iniciar_sesion_exitosa(usuario_valido)
        else:
            self._mostrar_alerta("Credenciales inválidas", "El correo o la contraseña son incorrectos.")

    def iniciar_sesion_exitosa(self, usuario):
        app = App.get_running_app()
        if app:
            app.usuario_actual = usuario

        if usuario.get("rol") == "cajero":
            self.ir_a_pantalla("pos")
        else:
            self.ir_a_pantalla("dashboard")

    def _mostrar_alerta(self, titulo, mensaje):
        self.dialog = MDDialog(
            title=titulo,
            text=mensaje,
            size_hint_x=0.90,
            buttons=[
                MDFillRoundFlatButton(
                    text="ENTENDIDO",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def volver_inicio(self):
        if self.manager and "welcome" in self.manager.screen_names:
            self.manager.current = "welcome"

    def ir_a_pantalla(self, nombre):
        if not self.manager:
            return
        equivalencias = {
            "dashboard": ["dashboard"],
            "pos": ["pos"],
            "register": ["register", "register_user", "registro"],
            "welcome": ["welcome"],
        }
        for candidato in equivalencias.get(nombre, [nombre]):
            if candidato in self.manager.screen_names:
                self.manager.current = candidato
                return