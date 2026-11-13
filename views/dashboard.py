import os
import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comprobante_dialog = None
        self.detalle_dialog = None
        self.notif_dialog = None
        self.alertas_activas = []
        self._ultimo_hash_ventas = None

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.95, 0.96, 0.98, 1))

        # ---------------------------------------------------------
        # 1. ENCABEZADO SUPERIOR CON LOGO, CAMPANITA Y ACCESOS
        # ---------------------------------------------------------
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(68),
            padding=[dp(10), dp(8), dp(8), dp(8)],
            spacing=dp(6),
            md_bg_color=(1, 1, 1, 1),
        )

        logo_card = MDCard(
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            radius=[dp(12)],
            elevation=1,
            md_bg_color=(0.13, 0.58, 0.28, 1),
            pos_hint={"center_y": 0.5},
        )
        ruta_logo = self._buscar_logo()
        if ruta_logo:
            logo_card.md_bg_color = (1, 1, 1, 1)
            logo_card.add_widget(Image(source=ruta_logo, fit_mode="contain"))
        else:
            logo_center = AnchorLayout(anchor_x="center", anchor_y="center")
            logo_center.add_widget(
                MDIcon(
                    icon="storefront",
                    font_size="22sp",
                    size_hint=(None, None),
                    size=(dp(24), dp(24)),
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                )
            )
            logo_card.add_widget(logo_center)

        title_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        self.lbl_greeting = MDLabel(
            text="¡Hola, Admin!",
            font_style="Subtitle1",
            bold=True,
            shorten=True,
            theme_text_color="Custom",
            text_color=(0.10, 0.14, 0.20, 1),
        )
        self.lbl_subtitle = MDLabel(
            text="Administrador • VentaFácil",
            font_style="Caption",
            shorten=True,
            theme_text_color="Secondary",
        )
        title_box.add_widget(self.lbl_greeting)
        title_box.add_widget(self.lbl_subtitle)

        btn_reports = MDRoundFlatButton(
            text="Reportes",
            icon="chart-bar",
            font_size="12sp",
            line_color=(0.13, 0.52, 0.89, 1),
            text_color=(0.13, 0.52, 0.89, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.ir_a_pantalla("reports"),
        )

        bell_wrapper = RelativeLayout(
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            pos_hint={"center_y": 0.5},
        )
        self.btn_notificaciones = MDIconButton(
            icon="bell-outline",
            icon_size="22sp",
            size_hint=(None, None),
            size=(dp(38), dp(38)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            theme_text_color="Custom",
            text_color=(0.35, 0.40, 0.45, 1),
            on_release=self.abrir_centro_notificaciones,
        )
        self.badge_card = MDCard(
            size_hint=(None, None),
            size=(dp(18), dp(18)),
            radius=[dp(9)],
            elevation=0,
            md_bg_color=(0.88, 0.22, 0.22, 1),
            pos_hint={"right": 0.98, "top": 0.96},
            opacity=0,
        )
        self.lbl_badge_count = MDLabel(
            text="0",
            font_size="10sp",
            bold=True,
            halign="center",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        self.badge_card.add_widget(self.lbl_badge_count)
        bell_wrapper.add_widget(self.btn_notificaciones)
        bell_wrapper.add_widget(self.badge_card)

        btn_refresh = MDIconButton(
            icon="refresh",
            icon_size="22sp",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            pos_hint={"center_y": 0.5},
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            on_release=lambda x: self.actualizar_dashboard(forzar=True),
        )
        btn_logout = MDIconButton(
            icon="logout",
            icon_size="22sp",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            pos_hint={"center_y": 0.5},
            theme_text_color="Custom",
            text_color=(0.35, 0.40, 0.45, 1),
            on_release=lambda x: self.ir_a_pantalla("login"),
        )

        header.add_widget(logo_card)
        header.add_widget(title_box)
        header.add_widget(btn_reports)
        header.add_widget(bell_wrapper)
        header.add_widget(btn_refresh)
        header.add_widget(btn_logout)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CONTENIDO PRINCIPAL DESPLAZABLE
        # ---------------------------------------------------------
        scroll_main = MDScrollView()
        self.body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(14), dp(14), dp(24)],
            spacing=dp(14),
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))

        self.banner_alerta_card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=[dp(12), dp(6), dp(8), dp(6)],
            spacing=dp(8),
            radius=[dp(12)],
            elevation=0,
            md_bg_color=(1.0, 0.93, 0.92, 1),
            line_color=(0.88, 0.25, 0.20, 0.8),
            on_release=self.abrir_centro_notificaciones,
        )
        self.banner_alerta_card.add_widget(
            MDIcon(
                icon="bell-alert-outline",
                font_size="20sp",
                theme_text_color="Custom",
                text_color=(0.85, 0.20, 0.18, 1),
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5},
            )
        )
        self.lbl_banner_alerta = MDLabel(
            text="",
            font_style="Caption",
            bold=True,
            shorten=True,
            theme_text_color="Custom",
            text_color=(0.75, 0.16, 0.14, 1),
            pos_hint={"center_y": 0.5},
        )
        btn_cerrar_banner = MDIconButton(
            icon="close",
            icon_size="18sp",
            theme_text_color="Custom",
            text_color=(0.65, 0.20, 0.18, 1),
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self._ocultar_banner_alerta(),
        )
        self.banner_alerta_card.add_widget(self.lbl_banner_alerta)
        self.banner_alerta_card.add_widget(btn_cerrar_banner)
        self.body.add_widget(self.banner_alerta_card)

        # --- TARJETAS KPI INTERACTIVAS ---
        self.kpi_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(224),
        )

        card_ventas, self.lbl_ventas_val, self.lbl_ventas_sub = self._crear_kpi_card(
            titulo="Ventas Hoy",
            valor="$0.00",
            subtitulo="0 venta(s) hoy",
            icono="cash-register",
            bg_color=(0.13, 0.65, 0.34, 1),
            on_click=self.ver_detalle_ventas_hoy,
        )
        card_gastos, self.lbl_gastos_val, self.lbl_gastos_sub = self._crear_kpi_card(
            titulo="Gastos Hoy",
            valor="$0.00",
            subtitulo="Egresos del día",
            icono="receipt-text-minus-outline",
            bg_color=(0.90, 0.51, 0.12, 1),
            on_click=self.ver_detalle_gastos_hoy,
        )
        card_prods, self.lbl_prods_val, self.lbl_prods_sub = self._crear_kpi_card(
            titulo="Productos",
            valor="0",
            subtitulo="En catálogo",
            icono="package-variant-closed",
            bg_color=(0.13, 0.52, 0.89, 1),
            on_click=self.ver_detalle_productos,
        )
        card_stock, self.lbl_stock_val, self.lbl_stock_sub = self._crear_kpi_card(
            titulo="Stock Bajo",
            valor="0",
            subtitulo="≤ 5 unidades",
            icono="alert-circle-outline",
            bg_color=(0.88, 0.30, 0.25, 1),
            on_click=self.ver_detalle_stock_bajo,
        )

        self.kpi_grid.add_widget(card_ventas)
        self.kpi_grid.add_widget(card_gastos)
        self.kpi_grid.add_widget(card_prods)
        self.kpi_grid.add_widget(card_stock)
        self.body.add_widget(self.kpi_grid)

        # --- ACCIONES RÁPIDAS ---
        self.body.add_widget(
            MDLabel(
                text="Acciones Rápidas",
                font_style="Subtitle1",
                bold=True,
                size_hint_y=None,
                height=dp(24),
                theme_text_color="Custom",
                text_color=(0.12, 0.16, 0.22, 1),
            )
        )

        self.actions_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(186),
        )

        card_pos = self._crear_accion_interactiva(
            titulo="Nueva Venta",
            icono="cart-plus",
            destino="pos",
            destacado=True,
            color_principal=(0.13, 0.58, 0.28, 1),
            color_badge=(1.0, 1.0, 1.0, 0.20),
        )
        card_inv = self._crear_accion_interactiva(
            titulo="Inventario",
            icono="package-variant-closed",
            destino="inventory",
            destacado=False,
            color_principal=(0.13, 0.52, 0.89, 1),
            color_badge=(0.90, 0.95, 1.0, 1),
        )
        card_gastos_act = self._crear_accion_interactiva(
            titulo="Gastos",
            icono="receipt-text-minus-outline",
            destino="expenses",
            destacado=False,
            color_principal=(0.88, 0.35, 0.25, 1),
            color_badge=(1.0, 0.93, 0.91, 1),
        )
        card_cierre = self._crear_accion_interactiva(
            titulo="Cierre Caja",
            icono="cash-lock",
            destino="closure",
            destacado=False,
            color_principal=(0.24, 0.32, 0.42, 1),
            color_badge=(0.92, 0.94, 0.97, 1),
        )

        self.actions_grid.add_widget(card_pos)
        self.actions_grid.add_widget(card_inv)
        self.actions_grid.add_widget(card_gastos_act)
        self.actions_grid.add_widget(card_cierre)
        self.body.add_widget(self.actions_grid)

        # --- ÚLTIMAS VENTAS REALIZADAS ---
        sales_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            padding=[0, dp(2), 0, 0],
        )
        sales_header.add_widget(
            MDLabel(
                text="Últimas Ventas",
                font_style="Subtitle1",
                bold=True,
                size_hint_x=0.45,
            )
        )
        self.lbl_balance_hoy = MDLabel(
            text="Balance Hoy: $0.00",
            font_style="Caption",
            bold=True,
            halign="right",
            size_hint_x=0.55,
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
        )
        sales_header.add_widget(self.lbl_balance_hoy)
        self.body.add_widget(sales_header)

        sales_card = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            radius=[dp(16)],
            elevation=0,
            line_color=(0.88, 0.90, 0.93, 1),
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None,
        )
        sales_card.bind(minimum_height=sales_card.setter("height"))

        self.sales_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
        )
        self.sales_list.bind(minimum_height=self.sales_list.setter("height"))
        sales_card.add_widget(self.sales_list)
        self.body.add_widget(sales_card)

        scroll_main.add_widget(self.body)
        root.add_widget(scroll_main)
        self.add_widget(root)

        Window.bind(width=self._adaptar_layout)
        self._adaptar_layout()

    def _crear_accion_interactiva(
        self,
        titulo,
        icono,
        destino,
        destacado=False,
        color_principal=(0.13, 0.58, 0.28, 1),
        color_badge=(0.90, 0.96, 0.92, 1),
    ):
        bg_card = color_principal if destacado else (1, 1, 1, 1)
        fg_titulo = (1, 1, 1, 1) if destacado else (0.12, 0.16, 0.22, 1)
        fg_icono = (1, 1, 1, 1) if destacado else color_principal
        borde = (0, 0, 0, 0) if destacado else (0.86, 0.89, 0.93, 1)

        card = MDCard(
            orientation="vertical",
            padding=[dp(8), dp(10), dp(8), dp(8)],
            spacing=dp(6),
            radius=[dp(18)],
            elevation=1 if destacado else 0,
            ripple_behavior=True,
            md_bg_color=bg_card,
            line_color=borde,
            size_hint_y=None,
            height=dp(88),
        )

        top_anchor = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint_y=None,
            height=dp(44),
        )
        icon_badge = MDCard(
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            radius=[dp(14)],
            elevation=0,
            md_bg_color=color_badge,
        )
        icon_center = AnchorLayout(anchor_x="center", anchor_y="center")
        icon_center.add_widget(
            MDIcon(
                icon=icono,
                font_size="23sp",
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                theme_text_color="Custom",
                text_color=fg_icono,
            )
        )
        icon_badge.add_widget(icon_center)
        top_anchor.add_widget(icon_badge)

        lbl_titulo = MDLabel(
            text=titulo,
            font_style="Subtitle2",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=fg_titulo,
        )

        card.add_widget(top_anchor)
        card.add_widget(lbl_titulo)
        card.bind(on_release=lambda inst: self.ir_a_pantalla(destino))
        return card

    def _buscar_logo(self):
        carpetas = [
            os.path.join(os.path.abspath("."), "assets"),
            mobile_utils.get_subdir("assets"),
        ]
        for carpeta in carpetas:
            for nombre in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp"):
                ruta = os.path.join(carpeta, nombre)
                if os.path.exists(ruta):
                    return ruta
        return ""

    def _adaptar_layout(self, *args):
        if mobile_utils.es_pantalla_movil():
            self.kpi_grid.cols = 2
            self.kpi_grid.height = dp(224)
            self.actions_grid.cols = 2
            self.actions_grid.height = dp(186)
            self.body.padding = [dp(14), dp(14), dp(14), dp(24)]
        else:
            self.kpi_grid.cols = 4
            self.kpi_grid.height = dp(122)
            self.actions_grid.cols = 4
            self.actions_grid.height = dp(88)
            self.body.padding = [dp(24), dp(18), dp(24), dp(24)]

    def _crear_kpi_card(self, titulo, valor, subtitulo, icono, bg_color, on_click=None):
        card = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(10), dp(10), dp(10)],
            spacing=dp(2),
            radius=[dp(16)],
            elevation=1,
            ripple_behavior=True,
            md_bg_color=bg_color,
            on_release=on_click if on_click else (lambda x: None),
        )

        top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24))
        icon_w = MDIcon(
            icon=icono,
            font_size="20sp",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.95),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
        )
        lbl_title = MDLabel(
            text=titulo,
            font_style="Caption",
            bold=True,
            shorten=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.92),
            padding=[dp(4), 0, 0, 0],
        )
        chevron_w = MDIcon(
            icon="chevron-right",
            font_size="18sp",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.80),
            size_hint=(None, None),
            size=(dp(22), dp(22)),
        )
        top_row.add_widget(icon_w)
        top_row.add_widget(lbl_title)
        top_row.add_widget(chevron_w)

        lbl_val = MDLabel(
            text=valor,
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )

        lbl_sub = MDLabel(
            text=subtitulo,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.85),
            size_hint_y=None,
            height=dp(16),
        )

        card.add_widget(top_row)
        card.add_widget(lbl_val)
        card.add_widget(lbl_sub)
        return card, lbl_val, lbl_sub

    # ---------------------------------------------------------
    # CENTRO DE NOTIFICACIONES
    # ---------------------------------------------------------
    def _aplicar_alertas_ui(self, alertas):
        self.alertas_activas = alertas
        cantidad = len(alertas)

        if cantidad > 0:
            self.badge_card.opacity = 1
            self.lbl_badge_count.text = str(cantidad) if cantidad < 100 else "99+"
            self.btn_notificaciones.icon = "bell-ring-outline"
            self.btn_notificaciones.text_color = (0.88, 0.25, 0.20, 1)
        else:
            self.badge_card.opacity = 0
            self.lbl_badge_count.text = "0"
            self.btn_notificaciones.icon = "bell-outline"
            self.btn_notificaciones.text_color = (0.35, 0.40, 0.45, 1)

        alerta_reciente = getattr(database, "ULTIMA_ALERTA_STOCK", "")
        if alerta_reciente:
            database.ULTIMA_ALERTA_STOCK = ""
            self.lbl_banner_alerta.text = f"Aviso: {alerta_reciente}"
            self.banner_alerta_card.height = dp(42)
            self.banner_alerta_card.opacity = 1

    def _ocultar_banner_alerta(self):
        self.banner_alerta_card.height = 0
        self.banner_alerta_card.opacity = 0

    def abrir_centro_notificaciones(self, *args):
        self._aplicar_alertas_ui(database.get_notificaciones_activas())
        self._ocultar_banner_alerta()

        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(320),
            spacing=dp(8),
            padding=[0, dp(4), 0, 0],
        )

        cantidad = len(self.alertas_activas)
        resumen_txt = (
            f"Tienes {cantidad} alerta(s) activa(s) • Toca una para gestionar"
            if cantidad > 0
            else "Sin alertas pendientes • Todo en orden"
        )
        color_res = (0.85, 0.22, 0.22, 1) if cantidad > 0 else (0.13, 0.55, 0.25, 1)

        resumen_card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            padding=[dp(10), 0, dp(10), 0],
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.95, 0.96, 0.98, 1),
        )
        resumen_card.add_widget(
            MDLabel(
                text=resumen_txt,
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=color_res,
                shorten=True,
            )
        )
        wrapper.add_widget(resumen_card)

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        lista = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(2), dp(2), dp(4), dp(6)],
        )
        lista.bind(minimum_height=lista.setter("height"))

        if not self.alertas_activas:
            lista.add_widget(
                MDLabel(
                    text="¡Todo al día! No hay productos agotados ni con stock bajo.",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.55, 0.25, 1),
                    size_hint_y=None,
                    height=dp(110),
                )
            )
        else:
            for alerta in self.alertas_activas:
                destino = alerta.get("destino", "inventory")

                def ir_alerta(inst, dest=destino):
                    self.notif_dialog.dismiss()
                    self.ir_a_pantalla(dest)

                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(56),
                    padding=[dp(8), dp(4), dp(6), dp(4)],
                    spacing=dp(8),
                    radius=[dp(12)],
                    elevation=0,
                    md_bg_color=alerta.get("bg", (0.97, 0.98, 0.99, 1)),
                    on_release=ir_alerta,
                )
                ic = MDIcon(
                    icon=alerta.get("icono", "bell-outline"),
                    font_size="22sp",
                    theme_text_color="Custom",
                    text_color=alerta.get("color", (0.85, 0.22, 0.22, 1)),
                    size_hint=(None, None),
                    size=(dp(28), dp(28)),
                    pos_hint={"center_y": 0.5},
                )
                info = MDBoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
                info.add_widget(
                    MDLabel(
                        text=alerta.get("titulo", "Alerta"),
                        font_style="Subtitle2",
                        bold=True,
                        shorten=True,
                    )
                )
                info.add_widget(
                    MDLabel(
                        text=alerta.get("detalle", ""),
                        font_style="Caption",
                        theme_text_color="Secondary",
                        shorten=True,
                    )
                )
                arrow = MDIcon(
                    icon="chevron-right",
                    font_size="20sp",
                    theme_text_color="Secondary",
                    size_hint=(None, None),
                    size=(dp(24), dp(24)),
                    pos_hint={"center_y": 0.5},
                )
                card.add_widget(ic)
                card.add_widget(info)
                card.add_widget(arrow)
                lista.add_widget(card)

        scroll.add_widget(lista)
        wrapper.add_widget(scroll)

        botones = []
        if cantidad > 0:
            def ir_inv(inst):
                self.notif_dialog.dismiss()
                self.ir_a_pantalla("inventory")

            botones.append(
                MDRoundFlatButton(
                    text="IR A INVENTARIO",
                    line_color=(0.13, 0.52, 0.89, 1),
                    text_color=(0.13, 0.52, 0.89, 1),
                    on_release=ir_inv,
                )
            )

        botones.append(
            MDFillRoundFlatButton(
                text="CERRAR",
                md_bg_color=(0.13, 0.55, 0.25, 1),
                on_release=lambda x: self.notif_dialog.dismiss(),
            )
        )

        self.notif_dialog = MDDialog(
            title="Centro de Notificaciones",
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=botones,
        )
        self.notif_dialog.open()

    # ---------------------------------------------------------
    # MODALES DE VISUALIZACIÓN AL TOCAR CADA TARJETA KPI
    # ---------------------------------------------------------
    def _abrir_modal_lista(self, titulo, resumen_texto, color_resumen, filas_widgets, texto_accion=None, pantalla_destino=None):
        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(320),
            spacing=dp(8),
            padding=[0, dp(4), 0, 0],
        )

        resumen_card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(38),
            padding=[dp(10), 0, dp(10), 0],
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.95, 0.96, 0.98, 1),
        )
        resumen_card.add_widget(
            MDLabel(
                text=resumen_texto,
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=color_resumen,
                shorten=True,
            )
        )
        wrapper.add_widget(resumen_card)

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        lista = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(2), dp(2), dp(4), dp(6)],
        )
        lista.bind(minimum_height=lista.setter("height"))

        for w in filas_widgets:
            lista.add_widget(w)

        scroll.add_widget(lista)
        wrapper.add_widget(scroll)

        botones = []
        if texto_accion and pantalla_destino:
            def ir_destino(inst):
                self.detalle_dialog.dismiss()
                self.ir_a_pantalla(pantalla_destino)

            botones.append(
                MDRoundFlatButton(
                    text=texto_accion,
                    line_color=(0.13, 0.52, 0.89, 1),
                    text_color=(0.13, 0.52, 0.89, 1),
                    on_release=ir_destino,
                )
            )

        botones.append(
            MDFillRoundFlatButton(
                text="CERRAR",
                md_bg_color=(0.13, 0.55, 0.25, 1),
                on_release=lambda x: self.detalle_dialog.dismiss(),
            )
        )

        self.detalle_dialog = MDDialog(
            title=titulo,
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=botones,
        )
        self.detalle_dialog.open()

    def ver_detalle_ventas_hoy(self, *args):
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        ventas = database.get_ventas()
        ventas_hoy = []
        total_efec = 0.0
        total_transf = 0.0

        for v in ventas:
            f = v.get("fecha")
            if isinstance(f, datetime.datetime) and f.strftime("%Y-%m-%d") == hoy_str:
                ventas_hoy.append(v)
                monto = float(v.get("total", 0.0))
                if "transf" in (v.get("metodo_pago") or "").lower():
                    total_transf += monto
                else:
                    total_efec += monto

        filas = []
        if not ventas_hoy:
            filas.append(
                MDLabel(
                    text="No hay ventas registradas el día de hoy.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(90),
                )
            )
        else:
            for v in ventas_hoy:
                vid = v.get("id", 0)
                total = float(v.get("total", 0.0))
                metodo = v.get("metodo_pago", "Efectivo")
                comp = v.get("comprobante", "")
                comp_img = v.get("comprobante_img", "")
                hora = v["fecha"].strftime("%I:%M %p") if isinstance(v.get("fecha"), datetime.datetime) else ""

                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(52),
                    padding=[dp(10), dp(4), dp(8), dp(4)],
                    spacing=dp(6),
                    radius=[dp(10)],
                    elevation=0,
                    md_bg_color=(0.97, 0.98, 0.99, 1),
                )
                info = MDBoxLayout(orientation="vertical", size_hint_x=0.65)
                titulo_v = f"Ticket #{vid:04d} • {metodo}" + (f" ({comp})" if comp else "")
                info.add_widget(MDLabel(text=titulo_v, font_style="Subtitle2", bold=True, shorten=True))
                info.add_widget(MDLabel(text=f"Hora: {hora}", font_style="Caption", theme_text_color="Secondary"))
                card.add_widget(info)

                if comp_img and os.path.exists(comp_img):
                    def abrir_foto(inst, venta_ref=v):
                        self.detalle_dialog.dismiss()
                        self.ver_comprobante_dialog(venta_ref)

                    card.add_widget(
                        MDIconButton(
                            icon="receipt-text-outline",
                            icon_size="19sp",
                            theme_text_color="Custom",
                            text_color=(0.13, 0.52, 0.89, 1),
                            size_hint=(None, None),
                            size=(dp(30), dp(30)),
                            pos_hint={"center_y": 0.5},
                            on_release=abrir_foto,
                        )
                    )

                card.add_widget(
                    MDLabel(
                        text=f"+${total:.2f}",
                        font_style="Subtitle2",
                        bold=True,
                        halign="right",
                        size_hint_x=0.35,
                        theme_text_color="Custom",
                        text_color=(0.13, 0.58, 0.28, 1),
                    )
                )
                filas.append(card)

        resumen = f"Efec: ${total_efec:.2f}  •  Transf: ${total_transf:.2f}  •  ({len(ventas_hoy)} tickets)"
        self._abrir_modal_lista(
            titulo="Ventas Realizadas Hoy",
            resumen_texto=resumen,
            color_resumen=(0.13, 0.55, 0.25, 1),
            filas_widgets=filas,
            texto_accion="REPORTES",
            pantalla_destino="reports",
        )

    def ver_detalle_gastos_hoy(self, *args):
        gastos_hoy = database.get_gastos_hoy()
        total_efec = 0.0
        total_transf = 0.0

        for g in gastos_hoy:
            monto = float(g.get("monto", 0.0))
            if "transf" in (g.get("metodo_pago") or "").lower():
                total_transf += monto
            else:
                total_efec += monto

        filas = []
        if not gastos_hoy:
            filas.append(
                MDLabel(
                    text="No se han registrado gastos el día de hoy.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(90),
                )
            )
        else:
            for g in gastos_hoy:
                desc = g.get("descripcion", "Gasto")
                cat = g.get("categoria", "General")
                metodo = g.get("metodo_pago", "Efectivo")
                monto = float(g.get("monto", 0.0))

                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(52),
                    padding=[dp(10), dp(4), dp(10), dp(4)],
                    spacing=dp(6),
                    radius=[dp(10)],
                    elevation=0,
                    md_bg_color=(0.99, 0.97, 0.95, 1),
                )
                info = MDBoxLayout(orientation="vertical", size_hint_x=0.68)
                info.add_widget(MDLabel(text=desc, font_style="Subtitle2", bold=True, shorten=True))
                info.add_widget(
                    MDLabel(
                        text=f"{cat} • {metodo}",
                        font_style="Caption",
                        theme_text_color="Secondary",
                        shorten=True,
                    )
                )
                card.add_widget(info)
                card.add_widget(
                    MDLabel(
                        text=f"-${monto:.2f}",
                        font_style="Subtitle2",
                        bold=True,
                        halign="right",
                        size_hint_x=0.32,
                        theme_text_color="Custom",
                        text_color=(0.85, 0.22, 0.22, 1),
                    )
                )
                filas.append(card)

        resumen = f"Efec: ${total_efec:.2f}  •  Transf: ${total_transf:.2f}  •  Total: ${total_efec + total_transf:.2f}"
        self._abrir_modal_lista(
            titulo="Gastos de Hoy",
            resumen_texto=resumen,
            color_resumen=(0.85, 0.42, 0.08, 1),
            filas_widgets=filas,
            texto_accion="IR A GASTOS",
            pantalla_destino="expenses",
        )

    def ver_detalle_productos(self, *args):
        productos = database.get_productos()
        unidades_totales = sum(int(p.get("stock", 0)) for p in productos)

        filas = []
        if not productos:
            filas.append(
                MDLabel(
                    text="El catálogo está vacío. Agrega productos en Inventario.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(90),
                )
            )
        else:
            for p in productos:
                nombre = p.get("nombre", "Producto")
                cat = p.get("categoria", "General")
                precio = float(p.get("precio_venta", p.get("precio", 0.0)))
                stock = int(p.get("stock", 0))

                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(52),
                    padding=[dp(10), dp(4), dp(10), dp(4)],
                    spacing=dp(6),
                    radius=[dp(10)],
                    elevation=0,
                    md_bg_color=(0.95, 0.97, 1.0, 1),
                )
                info = MDBoxLayout(orientation="vertical", size_hint_x=0.66)
                info.add_widget(MDLabel(text=nombre, font_style="Subtitle2", bold=True, shorten=True))
                info.add_widget(
                    MDLabel(
                        text=f"{cat} • Stock: {stock} uds",
                        font_style="Caption",
                        theme_text_color="Secondary",
                        shorten=True,
                    )
                )
                card.add_widget(info)
                card.add_widget(
                    MDLabel(
                        text=f"${precio:.2f}",
                        font_style="Subtitle2",
                        bold=True,
                        halign="right",
                        size_hint_x=0.34,
                        theme_text_color="Custom",
                        text_color=(0.13, 0.52, 0.89, 1),
                    )
                )
                filas.append(card)

        resumen = f"{len(productos)} producto(s) registrados  •  {unidades_totales} unidades en total"
        self._abrir_modal_lista(
            titulo="Catálogo de Productos",
            resumen_texto=resumen,
            color_resumen=(0.13, 0.52, 0.89, 1),
            filas_widgets=filas,
            texto_accion="INVENTARIO",
            pantalla_destino="inventory",
        )

    def ver_detalle_stock_bajo(self, *args):
        productos = database.get_productos()
        bajos = sorted(
            [p for p in productos if int(p.get("stock", 0)) <= 5],
            key=lambda x: int(x.get("stock", 0)),
        )

        filas = []
        if not bajos:
            filas.append(
                MDLabel(
                    text="¡Excelente! Ningún producto tiene stock bajo (≤ 5 uds).",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.55, 0.25, 1),
                    size_hint_y=None,
                    height=dp(90),
                )
            )
        else:
            for p in bajos:
                nombre = p.get("nombre", "Producto")
                cat = p.get("categoria", "General")
                stock = int(p.get("stock", 0))
                etiqueta_stock = "AGOTADO (0)" if stock == 0 else f"Quedan {stock} uds"
                color_alerta = (0.85, 0.15, 0.15, 1) if stock == 0 else (0.90, 0.45, 0.10, 1)

                card = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(52),
                    padding=[dp(10), dp(4), dp(10), dp(4)],
                    spacing=dp(6),
                    radius=[dp(10)],
                    elevation=0,
                    md_bg_color=(1.0, 0.95, 0.95, 1),
                )
                info = MDBoxLayout(orientation="vertical", size_hint_x=0.62)
                info.add_widget(MDLabel(text=nombre, font_style="Subtitle2", bold=True, shorten=True))
                info.add_widget(MDLabel(text=cat, font_style="Caption", theme_text_color="Secondary", shorten=True))
                card.add_widget(info)
                card.add_widget(
                    MDLabel(
                        text=etiqueta_stock,
                        font_style="Caption",
                        bold=True,
                        halign="right",
                        size_hint_x=0.38,
                        theme_text_color="Custom",
                        text_color=color_alerta,
                    )
                )
                filas.append(card)

        resumen = f"{len(bajos)} producto(s) requieren reabastecimiento urgente"
        self._abrir_modal_lista(
            titulo="Alerta de Stock Bajo (≤ 5)",
            resumen_texto=resumen,
            color_resumen=(0.85, 0.22, 0.22, 1),
            filas_widgets=filas,
            texto_accion="REABASTECER",
            pantalla_destino="inventory",
        )

    # ---------------------------------------------------------
    # ACTUALIZACIÓN DIFERIDA PARA TRANSICIONES INSTANTÁNEAS
    # ---------------------------------------------------------
    def on_pre_enter(self, *args):
        self._adaptar_layout()
        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        if usuario:
            rol_etiqueta = "Cajero" if usuario.get("rol") == "cajero" else "Administrador"
            self.lbl_greeting.text = f"¡Hola, {usuario['nombre']}!"
            self.lbl_subtitle.text = f"{rol_etiqueta} • {usuario['negocio']}"
        else:
            self.lbl_greeting.text = "¡Hola, Admin!"
            self.lbl_subtitle.text = "Administrador • VentaFácil"

    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self.actualizar_dashboard(), 0.02)

    def actualizar_dashboard(self, forzar=False):
        resumen = database.get_dashboard_resumen()
        self._aplicar_alertas_ui(resumen["alertas"])

        ventas_hoy = resumen["ventas_hoy"]
        tickets_hoy = resumen["tickets_hoy"]
        gastos_hoy = resumen["gastos_hoy"]
        balance_neto = resumen["balance_neto"]
        total_prods = resumen["total_prods"]
        stock_bajo = resumen["stock_bajo"]

        self.lbl_ventas_val.text = f"${ventas_hoy:.2f}"
        self.lbl_ventas_sub.text = f"{tickets_hoy} venta(s) hoy"
        self.lbl_gastos_val.text = f"${gastos_hoy:.2f}"
        self.lbl_prods_val.text = str(total_prods)
        self.lbl_stock_val.text = str(stock_bajo)

        self.lbl_balance_hoy.text = f"Balance Hoy: ${balance_neto:.2f}"
        self.lbl_balance_hoy.text_color = (0.13, 0.55, 0.25, 1) if balance_neto >= 0 else (0.85, 0.2, 0.2, 1)

        ultimas = resumen["ultimas_ventas"]
        firma_ventas = tuple((v["id"], v["total"], v["comprobante"]) for v in ultimas)
        if not forzar and firma_ventas == self._ultimo_hash_ventas:
            return
        self._ultimo_hash_ventas = firma_ventas

        self.sales_list.clear_widgets()
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")

        if not ultimas:
            self.sales_list.add_widget(
                MDLabel(
                    text="Aún no hay ventas. Toca 'Nueva Venta' para iniciar.",
                    font_style="Body2",
                    theme_text_color="Hint",
                    halign="center",
                    size_hint_y=None,
                    height=dp(65),
                )
            )
            return

        for idx, venta in enumerate(ultimas):
            vid = venta.get("id", 0)
            total = venta.get("total", 0.0)
            metodo = venta.get("metodo_pago", "Efectivo")
            comprobante = venta.get("comprobante", "")
            comprobante_img = venta.get("comprobante_img", "")
            fecha_obj = venta.get("fecha")

            titulo_ticket = f"#{vid:04d} • {metodo}"
            if comprobante:
                titulo_ticket += f" ({comprobante})"

            if isinstance(fecha_obj, datetime.datetime):
                if fecha_obj.strftime("%Y-%m-%d") == hoy_str:
                    fecha_texto = f"Hoy, {fecha_obj.strftime('%I:%M %p')}"
                else:
                    fecha_texto = fecha_obj.strftime("%d/%m/%Y • %I:%M %p")
            else:
                fecha_texto = str(fecha_obj)

            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(54),
                padding=[dp(2), dp(4), dp(4), dp(4)],
                spacing=dp(6),
            )

            icon_status = MDIcon(
                icon="check-circle-outline",
                font_size="20sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.65, 0.34, 1),
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5},
            )

            info_box = MDBoxLayout(orientation="vertical", size_hint_x=0.62, spacing=dp(2))
            info_box.add_widget(
                MDLabel(
                    text=titulo_ticket,
                    font_style="Subtitle2",
                    bold=True,
                    shorten=True,
                    theme_text_color="Custom",
                    text_color=(0.12, 0.16, 0.22, 1),
                )
            )
            info_box.add_widget(
                MDLabel(
                    text=fecha_texto,
                    font_style="Caption",
                    theme_text_color="Secondary",
                )
            )

            row.add_widget(icon_status)
            row.add_widget(info_box)

            if comprobante_img and os.path.exists(comprobante_img):
                btn_ver_comp = MDIconButton(
                    icon="receipt-text-outline",
                    icon_size="20sp",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.52, 0.89, 1),
                    size_hint=(None, None),
                    size=(dp(32), dp(32)),
                    pos_hint={"center_y": 0.5},
                    on_release=lambda x, v=venta: self.ver_comprobante_dialog(v),
                )
                row.add_widget(btn_ver_comp)

            lbl_monto = MDLabel(
                text=f"+${total:.2f}",
                font_style="Subtitle1",
                bold=True,
                halign="right",
                size_hint_x=0.38,
                theme_text_color="Custom",
                text_color=(0.13, 0.58, 0.28, 1),
            )
            row.add_widget(lbl_monto)
            self.sales_list.add_widget(row)

            if idx < len(ultimas) - 1:
                self.sales_list.add_widget(
                    MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.92, 0.93, 0.95, 1))
                )

    def ver_comprobante_dialog(self, venta):
        ruta_img = venta.get("comprobante_img", "")
        if not ruta_img or not os.path.exists(ruta_img):
            return

        content = MDBoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, height=dp(290))
        content.add_widget(
            MDLabel(
                text=f"Ref: {venta.get('comprobante', 'N/A')} • ${venta.get('total', 0.0):.2f}",
                font_style="Subtitle2",
                bold=True,
                size_hint_y=None,
                height=dp(24),
            )
        )
        img = Image(source=ruta_img, fit_mode="contain")
        content.add_widget(img)

        self.comprobante_dialog = MDDialog(
            title=f"Comprobante #{venta.get('id', 0):04d}",
            type="custom",
            size_hint_x=0.92,
            content_cls=content,
            buttons=[
                MDFillRoundFlatButton(
                    text="CERRAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.comprobante_dialog.dismiss(),
                )
            ],
        )
        self.comprobante_dialog.open()

    def ir_a_pantalla(self, nombre_pantalla):
        if not self.manager:
            return
        equivalencias = {
            "inventory": ["inventory", "inventario"],
            "expenses": ["expenses", "gastos"],
            "closure": ["closure", "cierre"],
            "pos": ["pos"],
            "login": ["login", "welcome"],
            "reports": ["reports", "reportes"],
        }
        for nombre in equivalencias.get(nombre_pantalla, [nombre_pantalla]):
            if nombre in self.manager.screen_names:
                self.manager.current = nombre
                return