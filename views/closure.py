import os
import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


class ClosureScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ventas_efec = 0.0
        self.ventas_transf = 0.0
        self.total_ventas = 0.0
        self.tickets_hoy = 0

        self.gastos_efec = 0.0
        self.gastos_transf = 0.0
        self.total_gastos = 0.0
        self.gastos_hoy_lista = []

        self.efectivo_esperado = 0.0
        self.transf_esperada = 0.0

        self.reporte_dialog = None
        self.gasto_dialog = None
        self._bloqueando_eventos = False

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.95, 0.96, 0.98, 1))

        # ---------------------------------------------------------
        # 1. ENCABEZADO SUPERIOR
        # ---------------------------------------------------------
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[dp(8), dp(8), dp(12), dp(8)],
            spacing=dp(8),
            md_bg_color=(1, 1, 1, 1),
        )

        btn_back = MDIconButton(
            icon="arrow-left",
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.ir_a_dashboard(),
        )

        title_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        title_box.add_widget(
            MDLabel(
                text="Cierre y Arqueo de Caja",
                font_style="Subtitle1",
                bold=True,
                shorten=True,
                theme_text_color="Custom",
                text_color=(0.10, 0.14, 0.20, 1),
            )
        )
        self.lbl_subtitulo = MDLabel(
            text="Administrador • VentaFácil",
            font_style="Caption",
            shorten=True,
            theme_text_color="Secondary",
        )
        title_box.add_widget(self.lbl_subtitulo)

        btn_auto_cuadrar = MDRoundFlatButton(
            text="Cuadre Perfecto",
            icon="check-decagram",
            font_size="12sp",
            line_color=(0.13, 0.60, 0.30, 1),
            text_color=(0.13, 0.60, 0.30, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.aplicar_cuadre_perfecto(),
        )

        btn_refresh = MDIconButton(
            icon="refresh",
            pos_hint={"center_y": 0.5},
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            on_release=lambda x: self.cargar_datos_dia(auto_cuadrar=True),
        )

        header.add_widget(btn_back)
        header.add_widget(title_box)
        header.add_widget(btn_auto_cuadrar)
        header.add_widget(btn_refresh)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CONTENIDO PRINCIPAL DESPLAZABLE
        # ---------------------------------------------------------
        scroll = MDScrollView()
        self.body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(14), dp(14), dp(28)],
            spacing=dp(12),
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))

        # --- TARJETAS KPI SUPERIORES ---
        self.kpi_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(216),
        )

        _, self.lbl_kpi_efec, self.lbl_kpi_efec_sub = self._crear_kpi_card(
            "Ventas Efectivo", "$0.00", "0 ticket(s) hoy", "cash", (0.13, 0.65, 0.34, 1)
        )
        _, self.lbl_kpi_transf, self.lbl_kpi_transf_sub = self._crear_kpi_card(
            "Transferencias", "$0.00", "Pagos bancarios", "bank-transfer", (0.13, 0.52, 0.89, 1)
        )
        _, self.lbl_kpi_gastos, self.lbl_kpi_gastos_sub = self._crear_kpi_card(
            "Gastos Hoy", "$0.00", "Efec: $0.00 • Transf: $0.00", "receipt-text-minus-outline", (0.90, 0.51, 0.12, 1)
        )
        _, self.lbl_kpi_total, self.lbl_kpi_total_sub = self._crear_kpi_card(
            "Total Vendido", "$0.00", "Efectivo + Transf.", "cash-register", (0.15, 0.42, 0.50, 1)
        )

        self.kpi_grid.add_widget(self.lbl_kpi_efec.parent)
        self.kpi_grid.add_widget(self.lbl_kpi_transf.parent)
        self.kpi_grid.add_widget(self.lbl_kpi_gastos.parent)
        self.kpi_grid.add_widget(self.lbl_kpi_total.parent)
        self.body.add_widget(self.kpi_grid)

        # ---------------------------------------------------------
        # 3. TARJETA DE FUSIÓN: INGRESOS + BASE - GASTOS DEL DÍA
        # ---------------------------------------------------------
        fusion_card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(12)],
            spacing=dp(8),
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None,
        )
        fusion_card.bind(minimum_height=fusion_card.setter("height"))

        fusion_top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        fusion_top.add_widget(
            MDLabel(
                text="Fusión de Caja y Gastos del Turno",
                font_style="Subtitle1",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.12, 0.16, 0.22, 1),
            )
        )
        btn_add_gasto = MDRoundFlatButton(
            text="+ Gasto Rápido",
            font_size="12sp",
            line_color=(0.90, 0.51, 0.12, 1),
            text_color=(0.85, 0.42, 0.08, 1),
            pos_hint={"center_y": 0.5},
            on_release=self.abrir_dialogo_gasto_rapido,
        )
        fusion_top.add_widget(btn_add_gasto)
        fusion_card.add_widget(fusion_top)

        # Desglose matemático paso a paso en pantalla
        ecuacion_box = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            radius=[dp(12)],
            elevation=0,
            md_bg_color=(0.96, 0.98, 0.97, 1),
            size_hint_y=None,
        )
        ecuacion_box.bind(minimum_height=ecuacion_box.setter("height"))

        self.lbl_formula_efec = MDLabel(
            text="Efectivo en cajón: Base ($10.00) + Ventas ($0.00) - Gastos ($0.00) = $10.00",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.13, 0.52, 0.26, 1),
            size_hint_y=None,
            height=dp(20),
        )
        self.lbl_formula_transf = MDLabel(
            text="Banco / Transf.: Ventas ($0.00) - Gastos ($0.00) = $0.00",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.13, 0.48, 0.82, 1),
            size_hint_y=None,
            height=dp(20),
        )
        self.lbl_utilidad_neta = MDLabel(
            text="Utilidad Neta del Día (Ventas Totales - Gastos Totales): $0.00",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.20, 0.25, 0.32, 1),
            size_hint_y=None,
            height=dp(20),
        )
        ecuacion_box.add_widget(self.lbl_formula_efec)
        ecuacion_box.add_widget(self.lbl_formula_transf)
        ecuacion_box.add_widget(self.lbl_utilidad_neta)
        fusion_card.add_widget(ecuacion_box)

        # Lista visible de gastos descontados en este cierre
        self.gastos_lista_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
        )
        self.gastos_lista_box.bind(minimum_height=self.gastos_lista_box.setter("height"))
        fusion_card.add_widget(self.gastos_lista_box)

        self.body.add_widget(fusion_card)

        # ---------------------------------------------------------
        # 4. FORMULARIO DE CONTEO Y CUADRE PERFECTO
        # ---------------------------------------------------------
        arqueo_card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(14), dp(14), dp(14)],
            spacing=dp(10),
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None,
        )
        arqueo_card.bind(minimum_height=arqueo_card.setter("height"))

        # --- SECCIÓN 1: EFECTIVO ---
        arqueo_card.add_widget(
            MDLabel(
                text="1. Conteo Físico de Efectivo en Cajón",
                font_style="Subtitle2",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.13, 0.58, 0.28, 1),
                size_hint_y=None,
                height=dp(22),
            )
        )

        self.efec_inputs_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(54),
        )

        self.txt_base = MDTextField(
            hint_text="Base inicial ($)",
            text="10.00",
            icon_left="cash-register",
            mode="round",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
        )
        self.txt_base.bind(text=self.on_cambio_valores)

        efec_contado_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(50))
        self.txt_efectivo = MDTextField(
            hint_text="Efectivo contado ($)",
            text="0.00",
            icon_left="cash",
            mode="round",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
        )
        self.txt_efectivo.bind(text=self.on_cambio_valores)

        self.btn_exacto_efec = MDRoundFlatButton(
            text="Exacto",
            font_size="12sp",
            line_color=(0.13, 0.60, 0.30, 1),
            text_color=(0.13, 0.60, 0.30, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.cuadrar_efectivo_exacto(),
        )
        efec_contado_row.add_widget(self.txt_efectivo)
        efec_contado_row.add_widget(self.btn_exacto_efec)

        self.efec_inputs_grid.add_widget(self.txt_base)
        self.efec_inputs_grid.add_widget(efec_contado_row)
        arqueo_card.add_widget(self.efec_inputs_grid)

        # Panel resultado efectivo
        res_efec_box = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.94, 0.98, 0.95, 1),
            size_hint_y=None,
            height=dp(54),
        )
        row_ef1 = MDBoxLayout(orientation="horizontal")
        row_ef1.add_widget(
            MDLabel(
                text="Efectivo esperado (Base + Ventas - Gastos):",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        self.lbl_efec_esperado = MDLabel(
            text="$0.00",
            font_style="Caption",
            bold=True,
            halign="right",
        )
        row_ef1.add_widget(self.lbl_efec_esperado)

        row_ef2 = MDBoxLayout(orientation="horizontal")
        row_ef2.add_widget(
            MDLabel(
                text="Diferencia Efectivo:",
                font_style="Subtitle2",
                bold=True,
            )
        )
        self.lbl_dif_efec = MDLabel(
            text="Cuadrado ($0.00)",
            font_style="Subtitle2",
            bold=True,
            halign="right",
            theme_text_color="Custom",
            text_color=(0.13, 0.58, 0.28, 1),
        )
        row_ef2.add_widget(self.lbl_dif_efec)

        res_efec_box.add_widget(row_ef1)
        res_efec_box.add_widget(row_ef2)
        arqueo_card.add_widget(res_efec_box)

        # --- SECCIÓN 2: TRANSFERENCIAS ---
        arqueo_card.add_widget(
            MDLabel(
                text="2. Arqueo de Transferencias Bancarias",
                font_style="Subtitle2",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.13, 0.52, 0.89, 1),
                size_hint_y=None,
                height=dp(24),
            )
        )

        transf_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50))
        self.txt_transferencia = MDTextField(
            hint_text="Transferencias verificadas ($)",
            text="0.00",
            icon_left="bank-check",
            mode="round",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
        )
        self.txt_transferencia.bind(text=self.on_cambio_valores)

        self.btn_exacto_transf = MDRoundFlatButton(
            text="Exacto",
            font_size="12sp",
            line_color=(0.13, 0.52, 0.89, 1),
            text_color=(0.13, 0.52, 0.89, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.cuadrar_transferencia_exacta(),
        )
        transf_row.add_widget(self.txt_transferencia)
        transf_row.add_widget(self.btn_exacto_transf)
        arqueo_card.add_widget(transf_row)

        res_transf_box = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.94, 0.97, 1.0, 1),
            size_hint_y=None,
            height=dp(54),
        )
        row_tr1 = MDBoxLayout(orientation="horizontal")
        row_tr1.add_widget(
            MDLabel(
                text="Transferencias esperadas (Ventas - Gastos):",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        self.lbl_transf_esperada = MDLabel(
            text="$0.00",
            font_style="Caption",
            bold=True,
            halign="right",
        )
        row_tr1.add_widget(self.lbl_transf_esperada)

        row_tr2 = MDBoxLayout(orientation="horizontal")
        row_tr2.add_widget(
            MDLabel(
                text="Diferencia Transferencias:",
                font_style="Subtitle2",
                bold=True,
            )
        )
        self.lbl_dif_transf = MDLabel(
            text="Cuadrado ($0.00)",
            font_style="Subtitle2",
            bold=True,
            halign="right",
            theme_text_color="Custom",
            text_color=(0.13, 0.58, 0.28, 1),
        )
        row_tr2.add_widget(self.lbl_dif_transf)

        res_transf_box.add_widget(row_tr1)
        res_transf_box.add_widget(row_tr2)
        arqueo_card.add_widget(res_transf_box)

        # --- BALANCE GENERAL DEL ARQUEO ---
        self.balance_card = MDCard(
            orientation="horizontal",
            padding=[dp(14), dp(10), dp(14), dp(10)],
            radius=[dp(12)],
            elevation=0,
            md_bg_color=(0.90, 0.98, 0.93, 1),
            size_hint_y=None,
            height=dp(48),
        )
        self.lbl_total_fisico_vs_esp = MDLabel(
            text="Balance General del Arqueo ($0.00 / $0.00):",
            font_style="Subtitle2",
            bold=True,
            size_hint_x=0.58,
            shorten=True,
        )
        self.lbl_balance_general = MDLabel(
            text="CUADRE PERFECTO ($0.00)",
            font_style="Subtitle2",
            bold=True,
            halign="right",
            size_hint_x=0.42,
            theme_text_color="Custom",
            text_color=(0.10, 0.55, 0.25, 1),
        )
        self.balance_card.add_widget(self.lbl_total_fisico_vs_esp)
        self.balance_card.add_widget(self.lbl_balance_general)
        arqueo_card.add_widget(self.balance_card)

        # Observaciones
        self.txt_observaciones = MDTextField(
            hint_text="Observaciones del cierre (opcional, ej. Cuadre perfecto con gastos incluidos)",
            icon_left="note-text-outline",
            mode="round",
            size_hint_y=None,
            height=dp(48),
        )
        arqueo_card.add_widget(self.txt_observaciones)
        self.body.add_widget(arqueo_card)

        # --- BOTÓN PRINCIPAL REALIZAR CIERRE ---
        btn_cerrar_caja = MDFillRoundFlatButton(
            text="REALIZAR CIERRE DE CAJA Y VER REPORTE EN PANTALLA",
            icon="check-circle",
            font_size="14sp",
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=(0.13, 0.58, 0.28, 1),
            text_color=(1, 1, 1, 1),
            on_release=self.realizar_cierre_y_mostrar,
        )
        self.body.add_widget(btn_cerrar_caja)

        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

        Window.bind(width=self._adaptar_layout)
        self._adaptar_layout()

    def _crear_kpi_card(self, titulo, valor, subtitulo, icono, bg_color):
        card = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(2),
            radius=[dp(16)],
            elevation=2,
            md_bg_color=bg_color,
        )
        top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        top.add_widget(
            MDIconButton(
                icon=icono,
                icon_size="19sp",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.95),
                size_hint=(None, None),
                size=(dp(22), dp(22)),
                disabled=True,
            )
        )
        top.add_widget(
            MDLabel(
                text=titulo,
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.92),
                padding=[dp(4), 0, 0, 0],
            )
        )
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
        card.add_widget(top)
        card.add_widget(lbl_val)
        card.add_widget(lbl_sub)
        return card, lbl_val, lbl_sub

    def _adaptar_layout(self, *args):
        if mobile_utils.es_pantalla_movil():
            self.kpi_grid.cols = 2
            self.kpi_grid.height = dp(216)
            self.efec_inputs_grid.cols = 1
            self.efec_inputs_grid.height = dp(112)
        else:
            self.kpi_grid.cols = 4
            self.kpi_grid.height = dp(116)
            self.efec_inputs_grid.cols = 2
            self.efec_inputs_grid.height = dp(54)

    def _float_seguro(self, texto):
        try:
            val = float((texto or "").strip())
            return val if val >= 0 else 0.0
        except ValueError:
            return 0.0

    # ---------------------------------------------------------
    # CARGA Y FUSIÓN DE VENTAS + GASTOS DEL DÍA
    # ---------------------------------------------------------
    def on_pre_enter(self, *args):
        self._adaptar_layout()
        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
        if usuario:
            rol = "Cajero" if usuario.get("rol") == "cajero" else "Administrador"
            self.lbl_subtitulo.text = f"{usuario['nombre']} ({rol}) • {usuario['negocio']} • {fecha_hoy}"
        else:
            self.lbl_subtitulo.text = f"Administrador • VentaFácil • {fecha_hoy}"

        self.cargar_datos_dia(auto_cuadrar=True)

    def cargar_datos_dia(self, auto_cuadrar=True):
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")

        # 1. Ventas de hoy separadas por método
        ventas = database.get_ventas()
        self.ventas_efec = 0.0
        self.ventas_transf = 0.0
        self.tickets_hoy = 0

        for v in ventas:
            f = v.get("fecha")
            if isinstance(f, datetime.datetime) and f.strftime("%Y-%m-%d") == hoy_str:
                self.tickets_hoy += 1
                monto = float(v.get("total", 0.0))
                if "transf" in (v.get("metodo_pago") or "").lower():
                    self.ventas_transf += monto
                else:
                    self.ventas_efec += monto

        self.total_ventas = round(self.ventas_efec + self.ventas_transf, 2)

        # 2. Gastos de hoy separados por método
        self.gastos_hoy_lista = database.get_gastos_hoy()
        self.gastos_efec = 0.0
        self.gastos_transf = 0.0

        for g in self.gastos_hoy_lista:
            monto = float(g.get("monto", 0.0))
            if "transf" in (g.get("metodo_pago") or "").lower():
                self.gastos_transf += monto
            else:
                self.gastos_efec += monto

        self.total_gastos = round(self.gastos_efec + self.gastos_transf, 2)

        # Actualizar KPIs
        self.lbl_kpi_efec.text = f"${self.ventas_efec:.2f}"
        self.lbl_kpi_efec_sub.text = f"{self.tickets_hoy} ticket(s) hoy"

        self.lbl_kpi_transf.text = f"${self.ventas_transf:.2f}"
        self.lbl_kpi_gastos.text = f"${self.total_gastos:.2f}"
        self.lbl_kpi_gastos_sub.text = f"Efec: ${self.gastos_efec:.2f} • Transf: ${self.gastos_transf:.2f}"
        self.lbl_kpi_total.text = f"${self.total_ventas:.2f}"

        # Renderizar listado de gastos fusionados
        self._renderizar_lista_gastos()

        if auto_cuadrar:
            self.aplicar_cuadre_perfecto()
        else:
            self.recalcular_cuadre()

    def _renderizar_lista_gastos(self):
        self.gastos_lista_box.clear_widgets()
        if not self.gastos_hoy_lista:
            self.gastos_lista_box.add_widget(
                MDLabel(
                    text="No hay egresos registrados hoy ($0.00 descontados).",
                    font_style="Caption",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(24),
                )
            )
            return

        self.gastos_lista_box.add_widget(
            MDLabel(
                text=f"Detalle de gastos descontados ({len(self.gastos_hoy_lista)}):",
                font_style="Caption",
                bold=True,
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(20),
            )
        )

        for g in self.gastos_hoy_lista:
            desc = g.get("descripcion", "Gasto")
            cat = g.get("categoria", "General")
            metodo = g.get("metodo_pago", "Efectivo")
            monto = float(g.get("monto", 0.0))

            fila = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(36),
                padding=[dp(10), 0, dp(10), 0],
                radius=[dp(8)],
                elevation=0,
                md_bg_color=(0.99, 0.96, 0.93, 1),
            )
            fila.add_widget(
                MDLabel(
                    text=f"• {desc} ({cat} • {metodo})",
                    font_style="Caption",
                    shorten=True,
                    size_hint_x=0.75,
                )
            )
            fila.add_widget(
                MDLabel(
                    text=f"-${monto:.2f}",
                    font_style="Caption",
                    bold=True,
                    halign="right",
                    size_hint_x=0.25,
                    theme_text_color="Custom",
                    text_color=(0.85, 0.25, 0.18, 1),
                )
            )
            self.gastos_lista_box.add_widget(fila)

    # ---------------------------------------------------------
    # LÓGICA DE CUADRE PERFECTO EN TIEMPO REAL
    # ---------------------------------------------------------
    def on_cambio_valores(self, *args):
        if self._bloqueando_eventos:
            return
        self.recalcular_cuadre()

    def recalcular_cuadre(self):
        base = self._float_seguro(self.txt_base.text)
        efectivo_contado = self._float_seguro(self.txt_efectivo.text)
        transf_verificada = self._float_seguro(self.txt_transferencia.text)

        self.efectivo_esperado = round(base + self.ventas_efec - self.gastos_efec, 2)
        self.transf_esperada = round(self.ventas_transf - self.gastos_transf, 2)
        utilidad_neta = round(self.total_ventas - self.total_gastos, 2)

        # Actualizar ecuación visual fusionada
        self.lbl_formula_efec.text = (
            f"Efectivo cajón: Base (${base:.2f}) + Ventas (${self.ventas_efec:.2f}) "
            f"- Gastos (${self.gastos_efec:.2f}) = ${self.efectivo_esperado:.2f}"
        )
        self.lbl_formula_transf.text = (
            f"Banco / Transf.: Ventas (${self.ventas_transf:.2f}) "
            f"- Gastos (${self.gastos_transf:.2f}) = ${self.transf_esperada:.2f}"
        )
        self.lbl_utilidad_neta.text = (
            f"Flujo Neto del Día (Ventas ${self.total_ventas:.2f} - Gastos ${self.total_gastos:.2f}): ${utilidad_neta:.2f}"
        )

        # Actualizar textos de botones rápidos
        self.btn_exacto_efec.text = f"Exacto (${self.efectivo_esperado:.2f})"
        self.btn_exacto_transf.text = f"Exacto (${self.transf_esperada:.2f})"

        self.lbl_efec_esperado.text = f"${self.efectivo_esperado:.2f}"
        self.lbl_transf_esperada.text = f"${self.transf_esperada:.2f}"

        dif_efec = round(efectivo_contado - self.efectivo_esperado, 2)
        dif_transf = round(transf_verificada - self.transf_esperada, 2)
        dif_total = round(dif_efec + dif_transf, 2)

        self._formatear_diferencia(self.lbl_dif_efec, dif_efec)
        self._formatear_diferencia(self.lbl_dif_transf, dif_transf)

        total_declarado = round(efectivo_contado + transf_verificada, 2)
        total_esperado = round(self.efectivo_esperado + self.transf_esperada, 2)
        self.lbl_total_fisico_vs_esp.text = f"Arqueo Total (${total_declarado:.2f} / ${total_esperado:.2f}):"

        if abs(dif_total) < 0.009:
            self.lbl_balance_general.text = "CUADRE PERFECTO ($0.00)"
            self.lbl_balance_general.text_color = (0.10, 0.55, 0.25, 1)
            self.balance_card.md_bg_color = (0.90, 0.98, 0.93, 1)
        elif dif_total > 0:
            self.lbl_balance_general.text = f"Sobrante: +${dif_total:.2f}"
            self.lbl_balance_general.text_color = (0.13, 0.52, 0.89, 1)
            self.balance_card.md_bg_color = (0.93, 0.96, 1.0, 1)
        else:
            self.lbl_balance_general.text = f"Faltante: -${abs(dif_total):.2f}"
            self.lbl_balance_general.text_color = (0.85, 0.20, 0.20, 1)
            self.balance_card.md_bg_color = (1.0, 0.94, 0.94, 1)

    def _formatear_diferencia(self, label, diferencia):
        if abs(diferencia) < 0.009:
            label.text = "Cuadrado ($0.00)"
            label.text_color = (0.13, 0.58, 0.28, 1)
        elif diferencia > 0:
            label.text = f"Sobrante: +${diferencia:.2f}"
            label.text_color = (0.13, 0.52, 0.89, 1)
        else:
            label.text = f"Faltante: -${abs(diferencia):.2f}"
            label.text_color = (0.85, 0.20, 0.20, 1)

    def cuadrar_efectivo_exacto(self):
        base = self._float_seguro(self.txt_base.text)
        self.efectivo_esperado = round(base + self.ventas_efec - self.gastos_efec, 2)
        self._bloqueando_eventos = True
        self.txt_efectivo.text = f"{self.efectivo_esperado:.2f}"
        self._bloqueando_eventos = False
        self.recalcular_cuadre()

    def cuadrar_transferencia_exacta(self):
        self.transf_esperada = round(self.ventas_transf - self.gastos_transf, 2)
        self._bloqueando_eventos = True
        self.txt_transferencia.text = f"{self.transf_esperada:.2f}"
        self._bloqueando_eventos = False
        self.recalcular_cuadre()

    def aplicar_cuadre_perfecto(self):
        base = self._float_seguro(self.txt_base.text)
        self.efectivo_esperado = round(base + self.ventas_efec - self.gastos_efec, 2)
        self.transf_esperada = round(self.ventas_transf - self.gastos_transf, 2)
        self._bloqueando_eventos = True
        self.txt_efectivo.text = f"{self.efectivo_esperado:.2f}"
        self.txt_transferencia.text = f"{self.transf_esperada:.2f}"
        self._bloqueando_eventos = False
        self.recalcular_cuadre()

    # ---------------------------------------------------------
    # REGISTRO DE GASTO RÁPIDO DIRECTAMENTE EN EL CIERRE
    # ---------------------------------------------------------
    def abrir_dialogo_gasto_rapido(self, *args):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(170),
            padding=[0, dp(6), 0, 0],
        )
        txt_desc = MDTextField(
            hint_text="Concepto del gasto (ej. Pago proveedor pan)",
            mode="round",
            size_hint_y=None,
            height=dp(48),
        )
        txt_monto = MDTextField(
            hint_text="Monto ($)",
            mode="round",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
        )

        self.metodo_gasto_sel = "Efectivo"
        row_met = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
        btn_ef = MDFillRoundFlatButton(
            text="Efectivo",
            md_bg_color=(0.13, 0.58, 0.28, 1),
            size_hint_x=0.5,
        )
        btn_tr = MDRoundFlatButton(
            text="Transferencia",
            line_color=(0.13, 0.52, 0.89, 1),
            text_color=(0.13, 0.52, 0.89, 1),
            size_hint_x=0.5,
        )

        def sel_ef(inst):
            self.metodo_gasto_sel = "Efectivo"
            btn_ef.md_bg_color = (0.13, 0.58, 0.28, 1)
            btn_tr.line_color = (0.13, 0.52, 0.89, 1)

        def sel_tr(inst):
            self.metodo_gasto_sel = "Transferencia"
            btn_ef.md_bg_color = (0.65, 0.70, 0.75, 1)
            btn_tr.line_color = (0.13, 0.58, 0.28, 1)

        btn_ef.bind(on_release=sel_ef)
        btn_tr.bind(on_release=sel_tr)
        row_met.add_widget(btn_ef)
        row_met.add_widget(btn_tr)

        content.add_widget(txt_desc)
        content.add_widget(txt_monto)
        content.add_widget(row_met)

        def guardar_gasto_rapido(inst):
            desc = (txt_desc.text or "").strip() or "Gasto de caja"
            monto = self._float_seguro(txt_monto.text)
            if monto <= 0:
                return
            database.insert_gasto(desc, monto, "Operativo", self.metodo_gasto_sel)
            self.gasto_dialog.dismiss()
            self.cargar_datos_dia(auto_cuadrar=True)

        self.gasto_dialog = MDDialog(
            title="Registrar Gasto en Cierre",
            type="custom",
            size_hint_x=0.90,
            content_cls=content,
            buttons=[
                MDRoundFlatButton(
                    text="CANCELAR",
                    on_release=lambda x: self.gasto_dialog.dismiss(),
                ),
                MDFillRoundFlatButton(
                    text="AGREGAR Y CUADRAR",
                    md_bg_color=(0.90, 0.51, 0.12, 1),
                    on_release=guardar_gasto_rapido,
                ),
            ],
        )
        self.gasto_dialog.open()

    # ---------------------------------------------------------
    # GENERAR REPORTE Y MOSTRAR CUADRE EN PANTALLA
    # ---------------------------------------------------------
    def realizar_cierre_y_mostrar(self, *args):
        self.recalcular_cuadre()

        base = self._float_seguro(self.txt_base.text)
        efectivo_contado = self._float_seguro(self.txt_efectivo.text)
        transf_verificada = self._float_seguro(self.txt_transferencia.text)
        dif_efec = round(efectivo_contado - self.efectivo_esperado, 2)
        dif_transf = round(transf_verificada - self.transf_esperada, 2)
        dif_total = round(dif_efec + dif_transf, 2)
        utilidad_neta = round(self.total_ventas - self.total_gastos, 2)
        obs = (self.txt_observaciones.text or "").strip() or "Sin novedades en turno"

        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        nombre_resp = usuario["nombre"] if usuario else "Administrador"
        nombre_negocio = usuario["negocio"] if usuario else "VentaFácil"

        ahora = datetime.datetime.now()
        estado_texto = "CUADRE PERFECTO ($0.00)" if abs(dif_total) < 0.009 else self.lbl_balance_general.text

        # Guardar reporte en carpeta cierres_caja
        cierres_dir = mobile_utils.get_subdir("cierres_caja")
        nombre_archivo = f"Cierre_{ahora.strftime('%Y%m%d_%H%M%S')}.txt"
        ruta_archivo = os.path.join(cierres_dir, nombre_archivo)

        lineas = [
            "================================================",
            f"   REPORTE DE CIERRE Y ARQUEO DE CAJA",
            f"   {nombre_negocio}",
            "================================================",
            f"Fecha y Hora : {ahora.strftime('%d/%m/%Y %I:%M %p')}",
            f"Responsable  : {nombre_resp}",
            f"Tickets Hoy  : {self.tickets_hoy}",
            "------------------------------------------------",
            "1. FUSIÓN DE INGRESOS Y GASTOS",
            f"   Base Inicial Caja      : ${base:.2f}",
            f"   (+) Ventas Efectivo    : ${self.ventas_efec:.2f}",
            f"   (-) Gastos Efectivo    : -${self.gastos_efec:.2f}",
            f"   (=) Efectivo Esperado  : ${self.efectivo_esperado:.2f}",
            f"   Efectivo Contado       : ${efectivo_contado:.2f}",
            f"   Diferencia Efectivo    : ${dif_efec:+.2f}",
            "------------------------------------------------",
            "2. ARQUEO DE TRANSFERENCIAS BANCARIAS",
            f"   (+) Ventas Transf.     : ${self.ventas_transf:.2f}",
            f"   (-) Gastos Transf.     : -${self.gastos_transf:.2f}",
            f"   (=) Transf. Esperadas  : ${self.transf_esperada:.2f}",
            f"   Transf. Verificadas    : ${transf_verificada:.2f}",
            f"   Diferencia Transf.     : ${dif_transf:+.2f}",
            "------------------------------------------------",
            "3. RESUMEN CONSOLIDADO",
            f"   Total Vendido          : ${self.total_ventas:.2f}",
            f"   Total Gastos           : -${self.total_gastos:.2f}",
            f"   Utilidad Neta Turno    : ${utilidad_neta:.2f}",
            f"   ESTADO DEL ARQUEO      : {estado_texto}",
            f"   Observaciones          : {obs}",
            "================================================",
        ]
        try:
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas))
        except Exception:
            pass

        # Mostrar comprobante visual completo en pantalla
        self._mostrar_modal_cierre_en_pantalla(
            ahora=ahora,
            responsable=nombre_resp,
            negocio=nombre_negocio,
            base=base,
            efectivo_contado=efectivo_contado,
            transf_verificada=transf_verificada,
            dif_total=dif_total,
            utilidad_neta=utilidad_neta,
            estado_texto=estado_texto,
            obs=obs,
        )

    def _mostrar_modal_cierre_en_pantalla(
        self,
        ahora,
        responsable,
        negocio,
        base,
        efectivo_contado,
        transf_verificada,
        dif_total,
        utilidad_neta,
        estado_texto,
        obs,
    ):
        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(370),
            spacing=dp(8),
            padding=[0, dp(4), 0, 0],
        )

        # Sello superior de estado
        es_perfecto = abs(dif_total) < 0.009
        banner = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(42),
            padding=[dp(12), 0, dp(12), 0],
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.13, 0.60, 0.30, 1) if es_perfecto else (0.13, 0.52, 0.89, 1),
        )
        banner.add_widget(
            MDLabel(
                text=f"✓ {estado_texto}",
                font_style="Subtitle2",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        wrapper.add_widget(banner)

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        detalle = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(4), dp(2), dp(6), dp(8)],
        )
        detalle.bind(minimum_height=detalle.setter("height"))

        filas_datos = [
            ("Negocio / Turno:", f"{negocio} • {ahora.strftime('%d/%m/%Y %I:%M %p')}"),
            ("Responsable:", f"{responsable} ({self.tickets_hoy} tickets)"),
            ("Base Inicial en Caja:", f"${base:.2f}"),
            ("(+) Ventas en Efectivo:", f"+${self.ventas_efec:.2f}"),
            ("(-) Gastos en Efectivo:", f"-${self.gastos_efec:.2f}"),
            ("(=) Efectivo en Cajón (Contado / Esp.):", f"${efectivo_contado:.2f} / ${self.efectivo_esperado:.2f}"),
            ("(+) Ventas Transferencia:", f"+${self.ventas_transf:.2f}"),
            ("(-) Gastos Transferencia:", f"-${self.gastos_transf:.2f}"),
            ("(=) Banco / Transf. (Verif. / Esp.):", f"${transf_verificada:.2f} / ${self.transf_esperada:.2f}"),
            ("Total Ventas - Total Gastos:", f"${self.total_ventas:.2f} - ${self.total_gastos:.2f} = ${utilidad_neta:.2f}"),
            ("Observaciones:", obs),
        ]

        for etiqueta, valor in filas_datos:
            row = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(34),
                padding=[dp(10), 0, dp(10), 0],
                radius=[dp(8)],
                elevation=0,
                md_bg_color=(0.96, 0.97, 0.99, 1),
            )
            row.add_widget(
                MDLabel(
                    text=etiqueta,
                    font_style="Caption",
                    theme_text_color="Secondary",
                    size_hint_x=0.55,
                    shorten=True,
                )
            )
            row.add_widget(
                MDLabel(
                    text=valor,
                    font_style="Caption",
                    bold=True,
                    halign="right",
                    size_hint_x=0.45,
                    shorten=True,
                )
            )
            detalle.add_widget(row)

        scroll.add_widget(detalle)
        wrapper.add_widget(scroll)

        def cerrar_y_volver(inst):
            self.reporte_dialog.dismiss()
            self.ir_a_dashboard()

        self.reporte_dialog = MDDialog(
            title="Comprobante de Cierre Guardado",
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=[
                MDRoundFlatButton(
                    text="SEGUIR AQUÍ",
                    on_release=lambda x: self.reporte_dialog.dismiss(),
                ),
                MDFillRoundFlatButton(
                    text="VOLVER AL INICIO",
                    md_bg_color=(0.13, 0.58, 0.28, 1),
                    on_release=cerrar_y_volver,
                ),
            ],
        )
        self.reporte_dialog.open()

    def ir_a_dashboard(self):
        if self.manager and "dashboard" in self.manager.screen_names:
            self.manager.current = "dashboard"


CierreScreen = ClosureScreen