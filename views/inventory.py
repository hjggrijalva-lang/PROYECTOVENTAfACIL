import os
import shutil
import time
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.metrics import dp
import database
import mobile_utils


CATEGORIAS_ABARROTES = [
    ("Granos y Cereales", "food-variant"),
    ("Lácteos y Huevos", "egg-outline"),
    ("Bebidas y Refrescos", "bottle-soda-classic-outline"),
    ("Aceites y Condimentos", "bottle-tonic-outline"),
    ("Enlatados y Conservas", "package-variant-closed"),
    ("Panadería y Galletas", "bread-slice-outline"),
    ("Snacks y Golosinas", "cookie-outline"),
    ("Embutidos y Carnes", "food-steak"),
    ("Frutas y Verduras", "food-apple-outline"),
    ("Limpieza del Hogar", "spray-bottle"),
    ("Aseo Personal", "hand-wash-outline"),
    ("Alimento para Mascotas", "paw-outline"),
    ("General / Otros", "store-outline"),
]


class InventoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_products = []
        self.categoria_filtro = "Todas"
        self.categoria_seleccionada = "Granos y Cereales"
        self.dialog = None
        self.cat_dialog = None
        self.confirm_dialog = None
        self.file_dialog = None
        self.imagen_seleccionada = ""

        # Carpeta segura para almacenar las fotos de productos (Android y PC)
        self.assets_dir = mobile_utils.get_subdir("assets", "productos")

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.96, 0.97, 0.98, 1))

        # ---------------------------------------------------------
        # 1. BARRA SUPERIOR (Header)
        # ---------------------------------------------------------
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            padding=[dp(8), dp(6), dp(12), dp(6)],
            spacing=dp(8),
            md_bg_color=(1, 1, 1, 1)
        )
        btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: setattr(self.manager, "current", "dashboard")
        )
        lbl_title = MDLabel(
            text="Inventario y Precios",
            font_style="H6",
            bold=True,
            shorten=True,
            pos_hint={"center_y": 0.5}
        )
        btn_add = MDFillRoundFlatButton(
            text="+ Nuevo",
            font_size="13sp",
            md_bg_color=(0.13, 0.55, 0.25, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.abrir_formulario_producto(None)
        )

        header.add_widget(btn_back)
        header.add_widget(lbl_title)
        header.add_widget(btn_add)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. BUSCADOR, FILTRO POR CATEGORÍA Y LISTA DE PRODUCTOS
        # ---------------------------------------------------------
        body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(10), dp(12), dp(14)],
            spacing=dp(10)
        )

        self.search_field = MDTextField(
            hint_text="Buscar producto o categoría...",
            mode="round",
            icon_left="magnify",
            size_hint_y=None,
            height=dp(46),
            fill_color_normal=(1, 1, 1, 1)
        )
        self.search_field.bind(text=self.filtrar_productos)
        body.add_widget(self.search_field)

        # Barra horizontal de filtros rápidos por categoría de abarrotes
        cat_scroll = MDScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(40)
        )
        self.cat_filter_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_x=None,
            padding=[dp(2), dp(2), dp(2), dp(2)]
        )
        self.cat_filter_row.bind(minimum_width=self.cat_filter_row.setter("width"))
        cat_scroll.add_widget(self.cat_filter_row)
        body.add_widget(cat_scroll)

        self._render_filtros_categoria()

        scroll = MDScrollView()
        self.product_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            padding=[dp(2), dp(4), dp(2), dp(16)]
        )
        self.product_list.bind(minimum_height=self.product_list.setter("height"))
        scroll.add_widget(self.product_list)
        body.add_widget(scroll)

        root.add_widget(body)
        self.add_widget(root)

    # ---------------------------------------------------------
    # FILTROS POR CATEGORÍA Y BÚSQUEDA
    # ---------------------------------------------------------
    def _render_filtros_categoria(self):
        self.cat_filter_row.clear_widgets()
        opciones = ["Todas"] + [c[0] for c in CATEGORIAS_ABARROTES]

        for cat in opciones:
            activa = (cat == self.categoria_filtro)
            if activa:
                btn = MDFillRoundFlatButton(
                    text=cat,
                    font_size="12sp",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x, c=cat: self.seleccionar_filtro_categoria(c)
                )
            else:
                btn = MDRoundFlatButton(
                    text=cat,
                    font_size="12sp",
                    line_color=(0.75, 0.78, 0.82, 1),
                    text_color=(0.25, 0.30, 0.35, 1),
                    on_release=lambda x, c=cat: self.seleccionar_filtro_categoria(c)
                )
            self.cat_filter_row.add_widget(btn)

    def seleccionar_filtro_categoria(self, categoria):
        self.categoria_filtro = categoria
        self._render_filtros_categoria()
        self.filtrar_productos()

    def on_pre_enter(self, *args):
        self.cargar_productos()

    def cargar_productos(self):
        self.all_products = database.get_productos()
        self.filtrar_productos()

    def filtrar_productos(self, *args):
        query = self.search_field.text.strip().lower()
        filtrados = self.all_products

        if self.categoria_filtro != "Todas":
            filtrados = [
                p for p in filtrados
                if (p.get("categoria") or "General").strip().lower() == self.categoria_filtro.lower()
            ]

        if query:
            filtrados = [
                p for p in filtrados
                if query in p["nombre"].lower() or query in (p.get("categoria") or "").lower()
            ]

        self.render_lista(filtrados)

    def render_lista(self, productos):
        self.product_list.clear_widgets()

        if not productos:
            self.product_list.add_widget(
                MDLabel(
                    text="No hay productos en esta categoría. Presiona '+ Nuevo' para registrar uno.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(80)
                )
            )
            return

        for prod in productos:
            precio_venta = prod.get("precio_venta", prod.get("precio", 0.0))
            precio_costo = prod.get("precio_costo", 0.0)
            stock = prod.get("stock", 0)
            ruta_img = prod.get("imagen", "")

            card = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(80),
                padding=[dp(10), dp(8), dp(6), dp(8)],
                spacing=dp(8),
                radius=[dp(14)],
                elevation=1,
                md_bg_color=(1, 1, 1, 1)
            )

            # 1. Miniatura de Foto o Placeholder
            thumb_box = MDCard(
                size_hint=(None, None),
                size=(dp(54), dp(54)),
                radius=[dp(10)],
                elevation=0,
                md_bg_color=(0.93, 0.95, 0.96, 1),
                pos_hint={"center_y": 0.5}
            )
            if ruta_img and os.path.exists(ruta_img):
                img_widget = Image(
                    source=ruta_img,
                    fit_mode="contain"
                )
                img_widget.reload()
                thumb_box.add_widget(img_widget)
            else:
                thumb_box.add_widget(
                    MDIconButton(
                        icon="image-outline",
                        icon_size="24sp",
                        theme_text_color="Custom",
                        text_color=(0.55, 0.60, 0.65, 1),
                        size_hint=(1, 1),
                        disabled=True
                    )
                )

            # 2. Nombre, Categoría y Stock
            info_col = MDBoxLayout(orientation="vertical", size_hint_x=0.46, spacing=dp(2))
            info_col.add_widget(
                MDLabel(text=prod["nombre"], font_style="Subtitle2", bold=True, shorten=True)
            )
            info_col.add_widget(
                MDLabel(
                    text=f"{prod.get('categoria', 'General')} • {stock} uds",
                    font_style="Caption",
                    theme_text_color="Secondary",
                    shorten=True
                )
            )

            # 3. Precio Venta y Costo
            price_col = MDBoxLayout(orientation="vertical", size_hint_x=0.26, spacing=dp(2))
            price_col.add_widget(
                MDLabel(
                    text=f"${precio_venta:.2f}",
                    font_style="Subtitle1",
                    bold=True,
                    halign="right",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.55, 0.25, 1)
                )
            )
            price_col.add_widget(
                MDLabel(
                    text=f"C: ${precio_costo:.2f}",
                    font_style="Caption",
                    halign="right",
                    theme_text_color="Hint"
                )
            )

            # 4. Botones Editar y Eliminar
            actions_col = MDBoxLayout(
                orientation="horizontal",
                size_hint_x=None,
                width=dp(76),
                spacing=dp(0),
                pos_hint={"center_y": 0.5}
            )
            btn_edit = MDIconButton(
                icon="pencil-outline",
                icon_size="20sp",
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                theme_text_color="Custom",
                text_color=(0.14, 0.48, 0.82, 1),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, p=prod: self.abrir_formulario_producto(p)
            )
            btn_delete = MDIconButton(
                icon="trash-can-outline",
                icon_size="20sp",
                size_hint=(None, None),
                size=(dp(36), dp(36)),
                theme_text_color="Custom",
                text_color=(0.85, 0.22, 0.22, 1),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, p=prod: self.confirmar_eliminacion(p)
            )

            actions_col.add_widget(btn_edit)
            actions_col.add_widget(btn_delete)

            card.add_widget(thumb_box)
            card.add_widget(info_col)
            card.add_widget(price_col)
            card.add_widget(actions_col)
            self.product_list.add_widget(card)

    # ---------------------------------------------------------
    # ELIMINACIÓN DE PRODUCTOS CON CONFIRMACIÓN
    # ---------------------------------------------------------
    def confirmar_eliminacion(self, prod):
        def ejecutar_borrado(inst):
            ruta_img = prod.get("imagen", "")
            if ruta_img and ruta_img.startswith(self.assets_dir) and os.path.exists(ruta_img):
                try:
                    os.remove(ruta_img)
                except OSError:
                    pass

            database.delete_producto(prod["id"])
            self.confirm_dialog.dismiss()
            self.cargar_productos()

        self.confirm_dialog = MDDialog(
            title="Eliminar Producto",
            text=f"¿Estás seguro de que deseas eliminar '{prod['nombre']}' del inventario?",
            size_hint_x=0.90,
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    on_release=lambda x: self.confirm_dialog.dismiss()
                ),
                MDFillRoundFlatButton(
                    text="ELIMINAR",
                    md_bg_color=(0.85, 0.22, 0.22, 1),
                    on_release=ejecutar_borrado
                )
            ]
        )
        self.confirm_dialog.open()

    # ---------------------------------------------------------
    # DIÁLOGO MODAL PARA AGREGAR / EDITAR PRODUCTO
    # ---------------------------------------------------------
    def abrir_formulario_producto(self, prod=None):
        es_edicion = prod is not None
        self.imagen_seleccionada = prod.get("imagen", "") if es_edicion else ""

        cat_inicial = prod.get("categoria", "Granos y Cereales") if es_edicion else (
            self.categoria_filtro if self.categoria_filtro != "Todas" else "Granos y Cereales"
        )
        self.categoria_seleccionada = cat_inicial or "Granos y Cereales"

        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(335),
            padding=[0, dp(8), 0, 0]
        )

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=[dp(2), dp(4), dp(6), dp(8)]
        )
        content.bind(minimum_height=content.setter("height"))

        # --- 1. Vista previa y botones de Foto ---
        photo_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(72),
            spacing=dp(10)
        )

        self.preview_card = MDCard(
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            radius=[dp(12)],
            elevation=1,
            md_bg_color=(0.93, 0.95, 0.96, 1)
        )
        self.actualizar_preview_foto()

        photo_controls = MDBoxLayout(orientation="vertical", spacing=dp(4), pos_hint={"center_y": 0.5})
        self.lbl_foto_estado = MDLabel(
            text=os.path.basename(self.imagen_seleccionada) if self.imagen_seleccionada else "Sin foto asignada",
            font_style="Caption",
            theme_text_color="Secondary",
            shorten=True,
            size_hint_y=None,
            height=dp(20)
        )

        photo_btns = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(38))
        btn_cargar_foto = MDRoundFlatButton(
            text="Foto",
            icon="image-plus",
            line_color=(0.13, 0.55, 0.25, 1),
            text_color=(0.13, 0.55, 0.25, 1),
            on_release=self.seleccionar_foto
        )
        btn_quitar_foto = MDFlatButton(
            text="Quitar",
            theme_text_color="Custom",
            text_color=(0.80, 0.25, 0.25, 1),
            on_release=self.quitar_foto
        )
        photo_btns.add_widget(btn_cargar_foto)
        photo_btns.add_widget(btn_quitar_foto)

        photo_controls.add_widget(self.lbl_foto_estado)
        photo_controls.add_widget(photo_btns)

        photo_row.add_widget(self.preview_card)
        photo_row.add_widget(photo_controls)
        content.add_widget(photo_row)

        # --- 2. Nombre del producto ---
        self.field_nombre = MDTextField(
            hint_text="Nombre (ej. Arroz Blanco 1kg)",
            text=prod["nombre"] if es_edicion else "",
            size_hint_y=None,
            height=dp(52)
        )
        content.add_widget(self.field_nombre)

        # --- 3. Selector Desplegable de Categoría de Abarrotes ---
        cat_section = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(68)
        )
        cat_section.add_widget(
            MDLabel(
                text="Categoría de Abarrotes",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(18)
            )
        )

        cat_selector_card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46),
            padding=[dp(10), 0, dp(6), 0],
            spacing=dp(8),
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.95, 0.97, 0.96, 1),
            line_color=(0.13, 0.55, 0.25, 0.75),
            on_release=self.abrir_selector_categoria
        )
        cat_icon = MDIconButton(
            icon="tag-outline",
            icon_size="20sp",
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            pos_hint={"center_y": 0.5},
            disabled=True
        )
        self.lbl_categoria_seleccionada = MDLabel(
            text=self.categoria_seleccionada,
            font_style="Subtitle2",
            bold=True,
            shorten=True,
            theme_text_color="Custom",
            text_color=(0.10, 0.16, 0.22, 1),
            pos_hint={"center_y": 0.5}
        )
        arrow_icon = MDIconButton(
            icon="chevron-down",
            icon_size="22sp",
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos_hint={"center_y": 0.5},
            on_release=self.abrir_selector_categoria
        )
        cat_selector_card.add_widget(cat_icon)
        cat_selector_card.add_widget(self.lbl_categoria_seleccionada)
        cat_selector_card.add_widget(arrow_icon)
        cat_section.add_widget(cat_selector_card)
        content.add_widget(cat_section)

        # --- 4. Fila de Precios (Venta y Costo lado a lado) ---
        prices_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(54)
        )
        self.field_precio_venta = MDTextField(
            hint_text="P. Venta ($)",
            text=f"{prod.get('precio_venta', 0.0):.2f}" if es_edicion else "",
            input_filter="float",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(52)
        )
        self.field_precio_costo = MDTextField(
            hint_text="P. Costo ($)",
            text=f"{prod.get('precio_costo', 0.0):.2f}" if es_edicion else "0.00",
            input_filter="float",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(52)
        )
        prices_row.add_widget(self.field_precio_venta)
        prices_row.add_widget(self.field_precio_costo)
        content.add_widget(prices_row)

        # --- 5. Stock disponible ---
        self.field_stock = MDTextField(
            hint_text="Stock disponible (unidades)",
            text=str(prod.get("stock", 0)) if es_edicion else "10",
            input_filter="int",
            size_hint_y=None,
            height=dp(52)
        )
        content.add_widget(self.field_stock)

        scroll.add_widget(content)
        wrapper.add_widget(scroll)

        botones = [
            MDFlatButton(
                text="CANCELAR",
                on_release=lambda x: self.dialog.dismiss()
            ),
            MDFillRoundFlatButton(
                text="GUARDAR",
                md_bg_color=(0.13, 0.55, 0.25, 1),
                on_release=lambda x: self.guardar_producto(prod["id"] if es_edicion else None)
            )
        ]

        self.dialog = MDDialog(
            title="Editar Producto" if es_edicion else "Nuevo Producto",
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=botones
        )
        self.dialog.open()

    # ---------------------------------------------------------
    # SELECTOR DE CATEGORÍAS DE ABARROTES
    # ---------------------------------------------------------
    def abrir_selector_categoria(self, *args):
        box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(300),
            padding=[0, dp(6), 0, 0]
        )
        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        lista = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(2), dp(2), dp(6), dp(4)]
        )
        lista.bind(minimum_height=lista.setter("height"))

        for nombre_cat, icono_cat in CATEGORIAS_ABARROTES:
            es_actual = (nombre_cat == self.categoria_seleccionada)
            item_card = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(44),
                padding=[dp(10), 0, dp(10), 0],
                spacing=dp(10),
                radius=[dp(10)],
                elevation=0,
                md_bg_color=(0.88, 0.96, 0.90, 1) if es_actual else (0.96, 0.97, 0.98, 1),
                line_color=(0.13, 0.55, 0.25, 1) if es_actual else (0.88, 0.90, 0.92, 1),
                on_release=lambda x, c=nombre_cat: self._confirmar_categoria(c)
            )
            ic_left = MDIconButton(
                icon=icono_cat,
                icon_size="20sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.55, 0.25, 1) if es_actual else (0.35, 0.42, 0.48, 1),
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5},
                disabled=True
            )
            lbl = MDLabel(
                text=nombre_cat,
                font_style="Subtitle2",
                bold=es_actual,
                shorten=True,
                theme_text_color="Custom",
                text_color=(0.10, 0.35, 0.18, 1) if es_actual else (0.15, 0.20, 0.25, 1),
                pos_hint={"center_y": 0.5}
            )
            item_card.add_widget(ic_left)
            item_card.add_widget(lbl)

            if es_actual:
                ic_check = MDIconButton(
                    icon="check-circle",
                    icon_size="20sp",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.55, 0.25, 1),
                    size_hint=(None, None),
                    size=(dp(28), dp(28)),
                    pos_hint={"center_y": 0.5},
                    disabled=True
                )
                item_card.add_widget(ic_check)

            lista.add_widget(item_card)

        scroll.add_widget(lista)
        box.add_widget(scroll)

        self.cat_dialog = MDDialog(
            title="Categoría de Abarrotes",
            type="custom",
            size_hint_x=0.92,
            content_cls=box,
            buttons=[
                MDFlatButton(
                    text="CERRAR",
                    on_release=lambda x: self.cat_dialog.dismiss()
                )
            ]
        )
        self.cat_dialog.open()

    def _confirmar_categoria(self, categoria):
        self.categoria_seleccionada = categoria
        self.lbl_categoria_seleccionada.text = categoria
        if self.cat_dialog:
            self.cat_dialog.dismiss()

    # ---------------------------------------------------------
    # MANEJO DE FOTOGRAFÍA DEL PRODUCTO (GALERÍA MÓVIL / PC)
    # ---------------------------------------------------------
    def actualizar_preview_foto(self):
        self.preview_card.clear_widgets()
        if self.imagen_seleccionada and os.path.exists(self.imagen_seleccionada):
            img = Image(
                source=self.imagen_seleccionada,
                fit_mode="contain"
            )
            img.reload()
            self.preview_card.add_widget(img)
        else:
            self.preview_card.add_widget(
                MDIconButton(
                    icon="camera-outline",
                    icon_size="26sp",
                    theme_text_color="Custom",
                    text_color=(0.50, 0.55, 0.60, 1),
                    size_hint=(1, 1),
                    disabled=True
                )
            )

    def quitar_foto(self, *args):
        self.imagen_seleccionada = ""
        self.lbl_foto_estado.text = "Sin foto asignada"
        self.actualizar_preview_foto()

    def seleccionar_foto(self, *args):
        mobile_utils.seleccionar_imagen_dispositivo(
            self._procesar_archivo_imagen,
            fallback_kivy_fn=self._abrir_selector_kivy
        )

    def _abrir_selector_kivy(self):
        chooser = FileChooserIconView(
            filters=["*.png", "*.jpg", "*.jpeg", "*.webp"],
            size_hint_y=None,
            height=dp(280)
        )

        def confirmar_seleccion(inst):
            if chooser.selection:
                self._procesar_archivo_imagen(chooser.selection[0])
            self.file_dialog.dismiss()

        self.file_dialog = MDDialog(
            title="Seleccionar Imagen",
            type="custom",
            size_hint_x=0.92,
            content_cls=chooser,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.file_dialog.dismiss()),
                MDFillRoundFlatButton(
                    text="SELECCIONAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=confirmar_seleccion
                )
            ]
        )
        self.file_dialog.open()

    def _procesar_archivo_imagen(self, ruta_origen):
        if not ruta_origen or not os.path.exists(ruta_origen):
            return

        ext = os.path.splitext(ruta_origen)[1].lower() or ".png"
        nombre_archivo = f"prod_{int(time.time() * 1000)}{ext}"
        ruta_destino = os.path.join(self.assets_dir, nombre_archivo)

        shutil.copy2(ruta_origen, ruta_destino)
        self.imagen_seleccionada = ruta_destino
        self.lbl_foto_estado.text = os.path.basename(ruta_origen)
        self.actualizar_preview_foto()

    def guardar_producto(self, prod_id=None):
        nombre = self.field_nombre.text.strip()
        if not nombre:
            return

        categoria = self.categoria_seleccionada or "Granos y Cereales"
        try:
            precio_venta = float(self.field_precio_venta.text.strip().replace(",", ".") or 0.0)
        except ValueError:
            precio_venta = 0.0

        try:
            precio_costo = float(self.field_precio_costo.text.strip().replace(",", ".") or 0.0)
        except ValueError:
            precio_costo = 0.0

        try:
            stock = int(self.field_stock.text.strip() or 0)
        except ValueError:
            stock = 0

        if prod_id is not None:
            database.update_producto(
                prod_id, nombre, categoria, precio_costo, precio_venta, stock, self.imagen_seleccionada
            )
        else:
            sku_auto = f"SKU-{int(time.time()) % 100000}"
            database.insert_producto(
                nombre, sku_auto, categoria, precio_costo, precio_venta, stock, self.imagen_seleccionada
            )

        self.dialog.dismiss()
        self.cargar_productos()