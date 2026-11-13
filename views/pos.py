import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


ICONOS_CATEGORIA = {
    "granos": "food-variant",
    "cereal": "food-variant",
    "lácteo": "egg-outline",
    "lacteo": "egg-outline",
    "huevo": "egg-outline",
    "bebida": "bottle-soda-classic-outline",
    "refresco": "bottle-soda-classic-outline",
    "aceite": "bottle-tonic-outline",
    "condimento": "bottle-tonic-outline",
    "enlatado": "package-variant-closed",
    "conserva": "package-variant-closed",
    "panad": "bread-slice-outline",
    "galleta": "cookie-outline",
    "snack": "cookie-outline",
    "golosina": "cookie-outline",
    "postre": "ice-cream",
    "embutido": "food-steak",
    "carne": "food-steak",
    "fruta": "food-apple-outline",
    "verdura": "food-apple-outline",
    "limpieza": "spray-bottle",
    "aseo": "hand-wash-outline",
    "mascota": "paw-outline",
}


class POSScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_products = []
        self.cart = {}
        self.carrito = self.cart
        self.total = 0.0
        self.total_venta = 0.0
        self.dialog = None

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.95, 0.96, 0.98, 1))

        # ---------------------------------------------------------
        # 1. BARRA SUPERIOR COMPACTA PARA CELULAR
        # ---------------------------------------------------------
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            padding=[dp(6), dp(6), dp(8), dp(6)],
            spacing=dp(6),
            md_bg_color=(1, 1, 1, 1)
        )
        self.btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.volver_atras()
        )

        title_box = MDBoxLayout(orientation="vertical", spacing=dp(1))
        title_box.add_widget(
            MDLabel(
                text="Punto de Venta",
                font_style="Subtitle1",
                bold=True,
                shorten=True
            )
        )
        self.lbl_operador = MDLabel(
            text="Operador en turno",
            font_style="Caption",
            theme_text_color="Secondary",
            shorten=True
        )
        title_box.add_widget(self.lbl_operador)

        btn_cierre = MDRoundFlatButton(
            text="Cierre",
            icon="cash-lock",
            font_size="12sp",
            line_color=(0.30, 0.36, 0.42, 1),
            text_color=(0.20, 0.26, 0.32, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.ir_a_cierre_caja()
        )

        btn_clear_order = MDIconButton(
            icon="trash-can-outline",
            theme_text_color="Custom",
            text_color=(0.85, 0.22, 0.22, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.limpiar_carrito()
        )

        header.add_widget(self.btn_back)
        header.add_widget(title_box)
        header.add_widget(btn_cierre)
        header.add_widget(btn_clear_order)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CUERPO RESPONSIVO (VERTICAL EN CELULAR / HORIZONTAL EN TABLET-PC)
        # ---------------------------------------------------------
        self.main_content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(10), dp(8), dp(10), dp(10)],
            spacing=dp(10)
        )

        # --- PANEL CATÁLOGO ---
        self.left_panel = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8)
        )

        self.search_field = MDTextField(
            hint_text="Buscar producto...",
            mode="round",
            icon_left="magnify",
            size_hint_y=None,
            height=dp(44),
            fill_color_normal=(1, 1, 1, 1)
        )
        self.search_field.bind(text=self.filtrar_productos)
        self.left_panel.add_widget(self.search_field)

        catalog_scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        self.products_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            padding=[dp(2), dp(2), dp(2), dp(8)],
            size_hint_y=None
        )
        self.products_grid.bind(minimum_height=self.products_grid.setter("height"))
        catalog_scroll.add_widget(self.products_grid)
        self.left_panel.add_widget(catalog_scroll)

        # --- PANEL ORDEN ACTUAL ---
        self.right_card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(6),
            radius=[dp(18)],
            elevation=2,
            md_bg_color=(1, 1, 1, 1)
        )

        order_top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24))
        order_top.add_widget(
            MDLabel(
                text="Orden Actual",
                font_style="Subtitle1",
                bold=True
            )
        )
        self.lbl_items_count = MDLabel(
            text="0 art.",
            font_style="Caption",
            bold=True,
            halign="right",
            theme_text_color="Secondary"
        )
        order_top.add_widget(self.lbl_items_count)
        self.right_card.add_widget(order_top)

        self.order_scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        self.order_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[0, dp(2), 0, dp(2)]
        )
        self.order_list.bind(minimum_height=self.order_list.setter("height"))
        self.order_scroll.add_widget(self.order_list)
        self.right_card.add_widget(self.order_scroll)

        self.right_card.add_widget(
            MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.90, 0.92, 0.94, 1))
        )

        # Fila inferior con Total + Botón Cobrar lado a lado en celular
        bottom_pay_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(46)
        )
        total_box = MDBoxLayout(orientation="vertical", size_hint_x=0.42)
        total_box.add_widget(
            MDLabel(text="Total:", font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=dp(16))
        )
        self.lbl_total = MDLabel(
            text="$0.00",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint_y=None,
            height=dp(28)
        )
        total_box.add_widget(self.lbl_total)

        btn_cobrar = MDFillRoundFlatButton(
            text="Cobrar Venta",
            icon="cash-register",
            font_size="14sp",
            size_hint=(0.58, None),
            height=dp(44),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            pos_hint={"center_y": 0.5},
            on_release=self.ir_a_cobrar
        )
        bottom_pay_row.add_widget(total_box)
        bottom_pay_row.add_widget(btn_cobrar)
        self.right_card.add_widget(bottom_pay_row)

        self.main_content.add_widget(self.left_panel)
        self.main_content.add_widget(self.right_card)
        root.add_widget(self.main_content)
        self.add_widget(root)

        Window.bind(width=self._adaptar_layout)
        self._adaptar_layout()

    def _adaptar_layout(self, *args):
        if mobile_utils.es_pantalla_movil():
            self.main_content.orientation = "vertical"
            self.left_panel.size_hint = (1, 0.56)
            self.right_card.size_hint = (1, 0.44)
            self.products_grid.cols = 2
        else:
            self.main_content.orientation = "horizontal"
            self.left_panel.size_hint = (0.64, 1)
            self.right_card.size_hint = (0.36, 1)
            self.products_grid.cols = 3

    def on_pre_enter(self, *args):
        self._adaptar_layout()
        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        if usuario:
            rol_etiqueta = "Cajero" if usuario.get("rol") == "cajero" else "Admin"
            self.lbl_operador.text = f"{usuario['nombre']} ({rol_etiqueta})"
            self.btn_back.icon = "logout" if usuario.get("rol") == "cajero" else "arrow-left"
        else:
            self.lbl_operador.text = "Operador: Admin"
            self.btn_back.icon = "arrow-left"

        self.cargar_productos()
        self.actualizar_carrito_ui()

    def cargar_productos(self):
        self.all_products = database.get_productos()
        self.filtrar_productos()

    def filtrar_productos(self, *args):
        query = self.search_field.text.strip().lower()
        if not query:
            self._render_catalogo(self.all_products)
            return

        filtrados = [
            p for p in self.all_products
            if query in p["nombre"].lower() or query in (p.get("categoria") or "").lower()
        ]
        self._render_catalogo(filtrados)

    def _obtener_icono_respaldo(self, categoria):
        cat_low = (categoria or "").lower()
        for clave, icono in ICONOS_CATEGORIA.items():
            if clave in cat_low:
                return icono
        return "package-variant-closed"

    def _render_catalogo(self, productos):
        self.products_grid.clear_widgets()

        if not productos:
            self.products_grid.add_widget(
                MDLabel(
                    text="No se encontraron productos.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(70)
                )
            )
            return

        for prod in productos:
            stock = int(prod.get("stock", 0))
            precio = float(prod.get("precio_venta", prod.get("precio", 0.0)))
            ruta_img = os.path.normpath(prod.get("imagen", "")) if prod.get("imagen") else ""
            tiene_foto = bool(ruta_img and os.path.exists(ruta_img))

            card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(152),
                padding=[dp(8), dp(6), dp(8), dp(8)],
                spacing=dp(2),
                radius=[dp(14)],
                elevation=1,
                md_bg_color=(1, 1, 1, 1) if stock > 0 else (0.95, 0.95, 0.96, 1),
                on_release=lambda x, p=prod: self.agregar_al_carrito(p)
            )

            color_stock = (0.85, 0.22, 0.22, 1) if stock <= 5 else (0.13, 0.55, 0.25, 1)
            card.add_widget(
                MDLabel(
                    text=f"STOCK: {stock}" if stock > 0 else "AGOTADO",
                    font_style="Overline",
                    bold=True,
                    halign="right",
                    theme_text_color="Custom",
                    text_color=color_stock,
                    size_hint_y=None,
                    height=dp(16)
                )
            )

            media_box = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(60), dp(60)),
                pos_hint={"center_x": 0.5}
            )
            if tiene_foto:
                img = Image(source=ruta_img, fit_mode="contain")
                img.reload()
                media_box.add_widget(img)
            else:
                media_box.add_widget(
                    MDIconButton(
                        icon=self._obtener_icono_respaldo(prod.get("categoria")),
                        icon_size="32sp",
                        theme_text_color="Custom",
                        text_color=(0.48, 0.53, 0.58, 1),
                        size_hint=(1, 1),
                        disabled=True
                    )
                )
            card.add_widget(media_box)

            card.add_widget(
                MDLabel(
                    text=prod["nombre"],
                    font_style="Subtitle2",
                    bold=True,
                    halign="center",
                    shorten=True,
                    size_hint_y=None,
                    height=dp(22)
                )
            )

            card.add_widget(
                MDLabel(
                    text=f"${precio:.2f}",
                    font_style="Subtitle1",
                    bold=True,
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.55, 0.25, 1) if stock > 0 else (0.55, 0.58, 0.62, 1),
                    size_hint_y=None,
                    height=dp(22)
                )
            )

            self.products_grid.add_widget(card)

    def agregar_al_carrito(self, prod):
        stock_disp = int(prod.get("stock", 0))
        if stock_disp <= 0:
            self._mostrar_alerta("Sin Stock", f"El producto '{prod['nombre']}' está agotado.")
            return

        pid = prod["id"]
        precio = float(prod.get("precio_venta", prod.get("precio", 0.0)))

        if pid in self.cart:
            if self.cart[pid]["cantidad"] >= stock_disp:
                self._mostrar_alerta(
                    "Stock Máximo",
                    f"Solo hay {stock_disp} unidad(es) disponible(s) de '{prod['nombre']}'."
                )
                return
            self.cart[pid]["cantidad"] += 1
        else:
            self.cart[pid] = {
                "id": pid,
                "nombre": prod["nombre"],
                "precio": precio,
                "precio_venta": precio,
                "cantidad": 1,
                "stock": stock_disp,
                "imagen": prod.get("imagen", "")
            }

        self.actualizar_carrito_ui()

    def cambiar_cantidad(self, pid, delta):
        if pid not in self.cart:
            return
        nueva_cant = self.cart[pid]["cantidad"] + delta
        if nueva_cant <= 0:
            del self.cart[pid]
        elif nueva_cant <= self.cart[pid]["stock"]:
            self.cart[pid]["cantidad"] = nueva_cant
        self.actualizar_carrito_ui()

    def limpiar_carrito(self):
        self.cart.clear()
        self.total = 0.0
        self.total_venta = 0.0
        self.actualizar_carrito_ui()

    def actualizar_carrito_ui(self):
        self.order_list.clear_widgets()

        if not self.cart:
            self.total = 0.0
            self.total_venta = 0.0
            self.lbl_items_count.text = "0 art."
            self.lbl_total.text = "$0.00"
            self.order_list.add_widget(
                MDLabel(
                    text="Toca productos arriba para agregarlos",
                    font_style="Caption",
                    theme_text_color="Hint",
                    halign="center",
                    size_hint_y=None,
                    height=dp(55)
                )
            )
            return

        total_unidades = 0
        suma_total = 0.0

        for pid, item in self.cart.items():
            cant = item["cantidad"]
            precio = item["precio_venta"]
            subtotal = cant * precio
            total_unidades += cant
            suma_total += subtotal

            row = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(50),
                padding=[dp(8), dp(4), dp(4), dp(4)],
                spacing=dp(6),
                radius=[dp(10)],
                elevation=0,
                md_bg_color=(0.96, 0.97, 0.98, 1)
            )

            ruta_img = os.path.normpath(item.get("imagen", "")) if item.get("imagen") else ""
            if ruta_img and os.path.exists(ruta_img):
                thumb = Image(
                    source=ruta_img,
                    size_hint=(None, None),
                    size=(dp(32), dp(32)),
                    pos_hint={"center_y": 0.5},
                    fit_mode="contain"
                )
                thumb.reload()
                row.add_widget(thumb)

            info = MDBoxLayout(orientation="vertical", spacing=dp(1))
            info.add_widget(
                MDLabel(text=item["nombre"], font_style="Subtitle2", bold=True, shorten=True)
            )
            info.add_widget(
                MDLabel(
                    text=f"${precio:.2f}  •  Sub: ${subtotal:.2f}",
                    font_style="Caption",
                    theme_text_color="Secondary",
                    shorten=True
                )
            )

            qty_box = MDBoxLayout(
                orientation="horizontal",
                size_hint_x=None,
                width=dp(88),
                pos_hint={"center_y": 0.5}
            )
            btn_menos = MDIconButton(
                icon="minus-circle-outline",
                icon_size="19sp",
                theme_text_color="Custom",
                text_color=(0.80, 0.25, 0.25, 1),
                size_hint=(None, None),
                size=(dp(30), dp(30)),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, p_id=pid: self.cambiar_cantidad(p_id, -1)
            )
            lbl_cant = MDLabel(
                text=str(cant),
                font_style="Subtitle2",
                bold=True,
                halign="center",
                size_hint_x=None,
                width=dp(24),
                pos_hint={"center_y": 0.5}
            )
            btn_mas = MDIconButton(
                icon="plus-circle-outline",
                icon_size="19sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.55, 0.25, 1),
                size_hint=(None, None),
                size=(dp(30), dp(30)),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, p_id=pid: self.cambiar_cantidad(p_id, 1)
            )
            qty_box.add_widget(btn_menos)
            qty_box.add_widget(lbl_cant)
            qty_box.add_widget(btn_mas)

            row.add_widget(info)
            row.add_widget(qty_box)
            self.order_list.add_widget(row)

        self.total = round(suma_total, 2)
        self.total_venta = self.total
        self.lbl_items_count.text = f"{total_unidades} art."
        self.lbl_total.text = f"${self.total:.2f}"

    def ir_a_cobrar(self, *args):
        if not self.cart or self.total <= 0:
            self._mostrar_alerta("Orden Vacía", "Agrega al menos un producto antes de cobrar.")
            return

        if not self.manager or "checkout" not in self.manager.screen_names:
            return

        checkout_screen = self.manager.get_screen("checkout")
        if hasattr(checkout_screen, "set_order"):
            checkout_screen.set_order(dict(self.cart), self.total)
        self.manager.current = "checkout"

    def ir_a_cierre_caja(self):
        if not self.manager:
            return
        for nombre in ("closure", "cierre"):
            if nombre in self.manager.screen_names:
                self.manager.current = nombre
                return

    def volver_atras(self):
        if not self.manager:
            return
        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        if usuario and usuario.get("rol") == "cajero" and "login" in self.manager.screen_names:
            self.manager.current = "login"
        elif "dashboard" in self.manager.screen_names:
            self.manager.current = "dashboard"

    def _mostrar_alerta(self, titulo, mensaje):
        self.dialog = MDDialog(
            title=titulo,
            text=mensaje,
            buttons=[
                MDFillRoundFlatButton(
                    text="ENTENDIDO",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()