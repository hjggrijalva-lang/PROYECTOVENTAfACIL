import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import database


CATEGORIAS_GASTO = [
    "Mercadería",
    "Insumos",
    "Servicios",
    "Transporte",
    "Mantenimiento",
    "General",
]


class ExpensesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categoria_seleccionada = "General"
        self.metodo_pago = "Efectivo"
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
            padding=[dp(8), dp(6), dp(14), dp(6)],
            spacing=dp(8),
            md_bg_color=(1, 1, 1, 1)
        )
        btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.volver_atras()
        )
        lbl_title = MDLabel(
            text="Registro de Gastos",
            font_style="H6",
            bold=True,
            pos_hint={"center_y": 0.5}
        )
        header.add_widget(btn_back)
        header.add_widget(lbl_title)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CONTENIDO DESPLAZABLE PARA CELULAR
        # ---------------------------------------------------------
        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(24)],
            spacing=dp(12),
            size_hint_y=None
        )
        body.bind(minimum_height=body.setter("height"))

        # --- TARJETA RESUMEN DE GASTOS DEL DÍA ---
        summary_card = MDCard(
            orientation="vertical",
            padding=[dp(18), dp(14), dp(18), dp(14)],
            spacing=dp(2),
            radius=[dp(16)],
            elevation=2,
            md_bg_color=(0.90, 0.51, 0.12, 1),
            size_hint_y=None,
            height=dp(110)
        )
        summary_card.add_widget(
            MDLabel(
                text="Total Gastos de Hoy",
                font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.92),
                size_hint_y=None,
                height=dp(20)
            )
        )
        self.lbl_total_hoy = MDLabel(
            text="$0.00",
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(42)
        )
        self.lbl_desglose_hoy = MDLabel(
            text="Efectivo: $0.00  •  Transferencia: $0.00",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.90),
            size_hint_y=None,
            height=dp(18)
        )
        summary_card.add_widget(self.lbl_total_hoy)
        summary_card.add_widget(self.lbl_desglose_hoy)
        body.add_widget(summary_card)

        # --- TARJETA FORMULARIO DE NUEVO GASTO ---
        form_card = MDCard(
            orientation="vertical",
            padding=[dp(16), dp(14), dp(16), dp(14)],
            spacing=dp(10),
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None
        )
        form_card.bind(minimum_height=form_card.setter("height"))

        form_card.add_widget(
            MDLabel(
                text="Nuevo Egreso / Salida",
                font_style="Subtitle1",
                bold=True,
                size_hint_y=None,
                height=dp(24)
            )
        )

        self.input_descripcion = MDTextField(
            hint_text="Descripción (ej. Compra de fundas, hielo, luz)",
            mode="round",
            icon_left="text-box-outline",
            size_hint_y=None,
            height=dp(48),
            fill_color_normal=(0.97, 0.98, 0.99, 1)
        )
        form_card.add_widget(self.input_descripcion)

        self.input_monto = MDTextField(
            hint_text="Monto del gasto ($)",
            mode="round",
            icon_left="currency-usd",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
            fill_color_normal=(0.97, 0.98, 0.99, 1)
        )
        form_card.add_widget(self.input_monto)

        # Selector horizontal de categorías
        form_card.add_widget(
            MDLabel(
                text="Categoría",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(18)
            )
        )
        cat_scroll = MDScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(38)
        )
        self.cat_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_x=None
        )
        self.cat_row.bind(minimum_width=self.cat_row.setter("width"))
        cat_scroll.add_widget(self.cat_row)
        form_card.add_widget(cat_scroll)
        self._render_categorias()

        # Selector de Origen de Pago (Efectivo / Transferencia)
        form_card.add_widget(
            MDLabel(
                text="Pagado con",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(18)
            )
        )
        pay_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(42)
        )
        self.btn_efec = MDFillRoundFlatButton(
            text="Efectivo",
            icon="cash",
            size_hint_x=0.48,
            height=dp(40),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self.seleccionar_metodo("Efectivo")
        )
        self.btn_transf = MDFillRoundFlatButton(
            text="Transferencia",
            icon="bank-transfer",
            size_hint_x=0.52,
            height=dp(40),
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.22, 1),
            on_release=lambda x: self.seleccionar_metodo("Transferencia")
        )
        pay_row.add_widget(self.btn_efec)
        pay_row.add_widget(self.btn_transf)
        form_card.add_widget(pay_row)

        btn_guardar = MDFillRoundFlatButton(
            text="REGISTRAR GASTO",
            icon="plus-circle-outline",
            font_size="14sp",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=(0.88, 0.35, 0.25, 1),
            on_release=self.guardar_gasto
        )
        form_card.add_widget(btn_guardar)
        body.add_widget(form_card)

        # --- HISTORIAL DE GASTOS RECIENTES ---
        body.add_widget(
            MDLabel(
                text="Historial de Gastos",
                font_style="Subtitle1",
                bold=True,
                size_hint_y=None,
                height=dp(26)
            )
        )

        list_card = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(8), dp(8)],
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None
        )
        list_card.bind(minimum_height=list_card.setter("height"))

        self.expenses_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None
        )
        self.expenses_list.bind(minimum_height=self.expenses_list.setter("height"))
        list_card.add_widget(self.expenses_list)
        body.add_widget(list_card)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    # ---------------------------------------------------------
    # CONTROLES DE CATEGORÍA Y MÉTODO DE PAGO
    # ---------------------------------------------------------
    def _render_categorias(self):
        self.cat_row.clear_widgets()
        for cat in CATEGORIAS_GASTO:
            activa = (cat == self.categoria_seleccionada)
            if activa:
                btn = MDFillRoundFlatButton(
                    text=cat,
                    font_size="12sp",
                    md_bg_color=(0.90, 0.51, 0.12, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x, c=cat: self.seleccionar_categoria(c)
                )
            else:
                btn = MDRoundFlatButton(
                    text=cat,
                    font_size="12sp",
                    line_color=(0.75, 0.78, 0.82, 1),
                    text_color=(0.25, 0.30, 0.35, 1),
                    on_release=lambda x, c=cat: self.seleccionar_categoria(c)
                )
            self.cat_row.add_widget(btn)

    def seleccionar_categoria(self, cat):
        self.categoria_seleccionada = cat
        self._render_categorias()

    def seleccionar_metodo(self, metodo):
        self.metodo_pago = metodo
        if metodo == "Efectivo":
            self.btn_efec.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_efec.text_color = (1, 1, 1, 1)
            self.btn_transf.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_transf.text_color = (0.20, 0.25, 0.22, 1)
        else:
            self.btn_transf.md_bg_color = (0.13, 0.52, 0.89, 1)
            self.btn_transf.text_color = (1, 1, 1, 1)
            self.btn_efec.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_efec.text_color = (0.20, 0.25, 0.22, 1)

    # ---------------------------------------------------------
    # CARGA, REGISTRO Y ELIMINACIÓN DE GASTOS
    # ---------------------------------------------------------
    def on_pre_enter(self, *args):
        self.refresh_expenses()

    def refresh_expenses(self):
        gastos = database.get_gastos()
        hoy = datetime.date.today()

        total_hoy = 0.0
        efec_hoy = 0.0
        transf_hoy = 0.0

        for g in gastos:
            f = g.get("fecha")
            fecha_gasto = f.date() if isinstance(f, datetime.datetime) else f
            if fecha_gasto == hoy:
                monto = float(g.get("monto", 0.0))
                metodo = (g.get("metodo_pago") or "Efectivo").lower()
                total_hoy += monto
                if "transf" in metodo:
                    transf_hoy += monto
                else:
                    efec_hoy += monto

        self.lbl_total_hoy.text = f"${total_hoy:.2f}"
        self.lbl_desglose_hoy.text = f"Efectivo: ${efec_hoy:.2f}  •  Transferencia: ${transf_hoy:.2f}"

        self.expenses_list.clear_widgets()
        recientes = gastos[:25]

        if not recientes:
            self.expenses_list.add_widget(
                MDLabel(
                    text="No hay gastos registrados aún.",
                    font_style="Body2",
                    theme_text_color="Hint",
                    halign="center",
                    size_hint_y=None,
                    height=dp(65)
                )
            )
            return

        hoy_str = hoy.strftime("%Y-%m-%d")
        for idx, g in enumerate(recientes):
            desc = g.get("descripcion", g.get("desc", "Gasto"))
            cat = g.get("categoria", "General")
            monto = float(g.get("monto", 0.0))
            metodo = g.get("metodo_pago", "Efectivo")
            fecha_obj = g.get("fecha")

            if isinstance(fecha_obj, datetime.datetime):
                if fecha_obj.strftime("%Y-%m-%d") == hoy_str:
                    fecha_txt = f"Hoy, {fecha_obj.strftime('%I:%M %p')}"
                else:
                    fecha_txt = fecha_obj.strftime("%d/%m/%Y • %I:%M %p")
            else:
                fecha_txt = str(fecha_obj)

            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(58),
                padding=[dp(4), dp(4), dp(2), dp(4)],
                spacing=dp(6)
            )

            info_box = MDBoxLayout(orientation="vertical", size_hint_x=0.62, spacing=dp(2))
            info_box.add_widget(
                MDLabel(
                    text=desc,
                    font_style="Subtitle2",
                    bold=True,
                    shorten=True
                )
            )
            info_box.add_widget(
                MDLabel(
                    text=f"{cat} • {metodo} • {fecha_txt}",
                    font_style="Caption",
                    theme_text_color="Secondary",
                    shorten=True
                )
            )

            lbl_monto = MDLabel(
                text=f"-${monto:.2f}",
                font_style="Subtitle1",
                bold=True,
                halign="right",
                size_hint_x=0.28,
                theme_text_color="Custom",
                text_color=(0.85, 0.22, 0.22, 1)
            )

            btn_del = MDIconButton(
                icon="trash-can-outline",
                icon_size="20sp",
                size_hint=(None, None),
                size=(dp(34), dp(34)),
                theme_text_color="Custom",
                text_color=(0.60, 0.64, 0.68, 1),
                pos_hint={"center_y": 0.5},
                on_release=lambda x, item=g: self.confirmar_eliminar(item)
            )

            row.add_widget(info_box)
            row.add_widget(lbl_monto)
            row.add_widget(btn_del)
            self.expenses_list.add_widget(row)

            if idx < len(recientes) - 1:
                self.expenses_list.add_widget(
                    MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.92, 0.93, 0.95, 1))
                )

    def guardar_gasto(self, *args):
        desc = self.input_descripcion.text.strip()
        monto_txt = self.input_monto.text.strip().replace(",", ".")

        if not desc:
            self._mostrar_alerta("Falta descripción", "Ingresa el motivo o descripción del gasto.")
            return

        try:
            monto = float(monto_txt) if monto_txt else 0.0
        except ValueError:
            monto = 0.0

        if monto <= 0:
            self._mostrar_alerta("Monto inválido", "Ingresa un monto mayor a $0.00.")
            return

        database.insert_gasto(
            desc,
            monto,
            categoria=self.categoria_seleccionada,
            metodo_pago=self.metodo_pago
        )

        self.input_descripcion.text = ""
        self.input_monto.text = ""
        self.refresh_expenses()

    def confirmar_eliminar(self, item):
        desc = item.get("descripcion", item.get("desc", "este gasto"))

        def borrar(inst):
            database.delete_gasto(item["id"])
            self.confirm_dialog.dismiss()
            self.refresh_expenses()

        self.confirm_dialog = MDDialog(
            title="Eliminar Gasto",
            text=f"¿Deseas eliminar '{desc}' (${item.get('monto', 0.0):.2f})?",
            size_hint_x=0.90,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.confirm_dialog.dismiss()),
                MDFillRoundFlatButton(
                    text="ELIMINAR",
                    md_bg_color=(0.85, 0.22, 0.22, 1),
                    on_release=borrar
                )
            ]
        )
        self.confirm_dialog.open()

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

    def volver_atras(self):
        if self.manager and "dashboard" in self.manager.screen_names:
            self.manager.current = "dashboard"


GastosScreen = ExpensesScreen