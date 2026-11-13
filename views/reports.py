import os
import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


class ReportsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.periodo_actual = "diario"
        self.datos_reporte = {}
        self.dialog = None

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.95, 0.96, 0.98, 1))

        # ---------------------------------------------------------
        # 1. BARRA SUPERIOR (Header)
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
            on_release=lambda x: self.volver_atras(),
        )

        title_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        title_box.add_widget(
            MDLabel(
                text="Reportes de Ventas",
                font_style="H6",
                bold=True,
                shorten=True,
                theme_text_color="Custom",
                text_color=(0.10, 0.14, 0.20, 1),
            )
        )
        self.lbl_subtitulo = MDLabel(
            text="Ventas del día • Hoy",
            font_style="Caption",
            shorten=True,
            theme_text_color="Secondary",
        )
        title_box.add_widget(self.lbl_subtitulo)

        btn_exportar = MDFillRoundFlatButton(
            text="Exportar Excel",
            icon="microsoft-excel",
            font_size="12sp",
            md_bg_color=(0.13, 0.58, 0.28, 1),
            text_color=(1, 1, 1, 1),
            pos_hint={"center_y": 0.5},
            on_release=self.exportar_reporte_excel,
        )

        header.add_widget(btn_back)
        header.add_widget(title_box)
        header.add_widget(btn_exportar)
        root.add_widget(header)

        # ---------------------------------------------------------
        # 2. CONTENIDO PRINCIPAL DESPLAZABLE
        # ---------------------------------------------------------
        scroll = MDScrollView()
        self.body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(24)],
            spacing=dp(12),
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))

        # --- SELECTOR DE PERIODO (DIARIO / SEMANAL / MENSUAL) ---
        tabs_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(40),
        )

        self.btn_diario = MDFillRoundFlatButton(
            text="Diario (Hoy)",
            font_size="12sp",
            md_bg_color=(0.13, 0.58, 0.28, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self.cambiar_periodo("diario"),
        )
        self.btn_semanal = MDFillRoundFlatButton(
            text="Semanal",
            font_size="12sp",
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.28, 1),
            on_release=lambda x: self.cambiar_periodo("semanal"),
        )
        self.btn_mensual = MDFillRoundFlatButton(
            text="Mensual",
            font_size="12sp",
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.28, 1),
            on_release=lambda x: self.cambiar_periodo("mensual"),
        )

        tabs_row.add_widget(self.btn_diario)
        tabs_row.add_widget(self.btn_semanal)
        tabs_row.add_widget(self.btn_mensual)
        self.body.add_widget(tabs_row)

        # --- TARJETAS KPI DEL PERIODO ---
        self.kpi_grid = MDGridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(216),
        )

        c1, self.lbl_total_ventas, self.lbl_cant_ventas = self._crear_kpi_card(
            "Total Ventas", "$0.00", "0 venta(s)", "cash-register", (0.13, 0.65, 0.34, 1)
        )
        c2, self.lbl_efec_val, self.lbl_transf_val = self._crear_kpi_card(
            "Efectivo / Transf.", "Efec: $0.00", "Transf: $0.00", "bank-transfer", (0.13, 0.52, 0.89, 1)
        )
        c3, self.lbl_gastos_val, _ = self._crear_kpi_card(
            "Gastos Periodo", "$0.00", "Egresos registrados", "receipt-text-minus-outline", (0.90, 0.51, 0.12, 1)
        )
        c4, self.lbl_balance_val, _ = self._crear_kpi_card(
            "Balance Neto", "$0.00", "Ventas - Gastos", "chart-line", (0.15, 0.42, 0.50, 1)
        )

        self.kpi_grid.add_widget(c1)
        self.kpi_grid.add_widget(c2)
        self.kpi_grid.add_widget(c3)
        self.kpi_grid.add_widget(c4)
        self.body.add_widget(self.kpi_grid)

        # --- ENCABEZADO DE LISTADO DE TICKETS ---
        list_header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        self.lbl_titulo_lista = MDLabel(
            text="Ventas Registradas Hoy",
            font_style="Subtitle1",
            bold=True,
            size_hint_x=0.60,
        )
        list_header.add_widget(self.lbl_titulo_lista)
        list_header.add_widget(
            MDLabel(
                text="Toca un ticket para ver productos",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_x=0.40,
            )
        )
        self.body.add_widget(list_header)

        tickets_card = MDCard(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            radius=[dp(16)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None,
        )
        tickets_card.bind(minimum_height=tickets_card.setter("height"))

        self.tickets_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
        )
        self.tickets_list.bind(minimum_height=self.tickets_list.setter("height"))
        tickets_card.add_widget(self.tickets_list)
        self.body.add_widget(tickets_card)

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
            text_color=(1, 1, 1, 0.88),
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
            self.body.padding = [dp(14), dp(12), dp(14), dp(24)]
        else:
            self.kpi_grid.cols = 4
            self.kpi_grid.height = dp(116)
            self.body.padding = [dp(22), dp(16), dp(22), dp(24)]

    # ---------------------------------------------------------
    # CAMBIO DE PERIODO Y CARGA DE DATOS
    # ---------------------------------------------------------
    def on_pre_enter(self, *args):
        self._adaptar_layout()
        self.cambiar_periodo(self.periodo_actual)

    def cambiar_periodo(self, periodo):
        self.periodo_actual = periodo
        botones = {
            "diario": self.btn_diario,
            "semanal": self.btn_semanal,
            "mensual": self.btn_mensual,
        }
        for clave, btn in botones.items():
            if clave == periodo:
                btn.md_bg_color = (0.13, 0.58, 0.28, 1)
                btn.text_color = (1, 1, 1, 1)
            else:
                btn.md_bg_color = (0.88, 0.90, 0.92, 1)
                btn.text_color = (0.20, 0.25, 0.28, 1)

        hoy = datetime.date.today()
        if periodo == "diario":
            self.lbl_subtitulo.text = f"Ventas del día • {hoy.strftime('%d/%m/%Y')}"
            self.lbl_titulo_lista.text = "Ventas Registradas Hoy"
        elif periodo == "semanal":
            self.lbl_subtitulo.text = f"Últimos 7 días • Hasta {hoy.strftime('%d/%m/%Y')}"
            self.lbl_titulo_lista.text = "Ventas de la Semana"
        else:
            self.lbl_subtitulo.text = f"Reporte Mensual • {hoy.strftime('%m/%Y')}"
            self.lbl_titulo_lista.text = "Ventas del Mes"

        self.cargar_reporte()

    def cargar_reporte(self):
        self.datos_reporte = database.get_reporte_periodo(self.periodo_actual)

        total_v = self.datos_reporte["total_ventas"]
        cant_v = self.datos_reporte["cantidad_ventas"]
        efec = self.datos_reporte["total_efectivo"]
        transf = self.datos_reporte["total_transferencia"]
        gastos = self.datos_reporte["total_gastos"]
        balance = self.datos_reporte["balance_neto"]

        self.lbl_total_ventas.text = f"${total_v:.2f}"
        self.lbl_cant_ventas.text = f"{cant_v} venta(s)"
        self.lbl_efec_val.text = f"Efec: ${efec:.2f}"
        self.lbl_transf_val.text = f"Transf: ${transf:.2f}"
        self.lbl_gastos_val.text = f"${gastos:.2f}"
        self.lbl_balance_val.text = f"${balance:.2f}"

        self.tickets_list.clear_widgets()
        ventas = self.datos_reporte.get("ventas", [])

        if not ventas:
            self.tickets_list.add_widget(
                MDLabel(
                    text="No hay ventas registradas en este periodo.",
                    font_style="Body2",
                    theme_text_color="Hint",
                    halign="center",
                    size_hint_y=None,
                    height=dp(70),
                )
            )
            return

        for idx, v in enumerate(ventas):
            vid = v["id"]
            total = v["total"]
            metodo = v["metodo_pago"]
            comp = v.get("comprobante", "")
            fecha_obj = v["fecha"]
            items = v.get("items", [])

            titulo = f"Ticket #{vid:04d} • {metodo}" + (f" ({comp})" if comp else "")
            if items:
                resumen_prods = ", ".join(f"{it['cantidad']}x {it['nombre_producto']}" for it in items[:2])
                if len(items) > 2:
                    resumen_prods += f" (+{len(items) - 2} más)"
                subtitulo = f"{fecha_obj.strftime('%d/%m/%Y • %I:%M %p')}  |  {resumen_prods}"
            else:
                subtitulo = fecha_obj.strftime("%d/%m/%Y • %I:%M %p")

            row = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(60),
                padding=[dp(4), dp(6), dp(4), dp(6)],
                spacing=dp(8),
                elevation=0,
                md_bg_color=(1, 1, 1, 1),
                on_release=lambda x, venta_sel=v: self.ver_detalle_ticket(venta_sel),
            )

            ic = MDIconButton(
                icon="bank-transfer" if "transf" in metodo.lower() else "cash",
                icon_size="22sp",
                theme_text_color="Custom",
                text_color=(0.13, 0.52, 0.89, 1) if "transf" in metodo.lower() else (0.45, 0.50, 0.55, 1),
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={"center_y": 0.5},
                disabled=True,
            )

            info = MDBoxLayout(orientation="vertical", size_hint_x=0.68, spacing=dp(2))
            info.add_widget(
                MDLabel(
                    text=titulo,
                    font_style="Subtitle2",
                    bold=True,
                    shorten=True,
                )
            )
            info.add_widget(
                MDLabel(
                    text=subtitulo,
                    font_style="Caption",
                    theme_text_color="Secondary",
                    shorten=True,
                )
            )

            lbl_monto = MDLabel(
                text=f"+ ${total:.2f}",
                font_style="Subtitle1",
                bold=True,
                halign="right",
                size_hint_x=0.32,
                theme_text_color="Custom",
                text_color=(0.13, 0.58, 0.28, 1),
            )

            row.add_widget(ic)
            row.add_widget(info)
            row.add_widget(lbl_monto)
            self.tickets_list.add_widget(row)

            if idx < len(ventas) - 1:
                self.tickets_list.add_widget(
                    MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.92, 0.93, 0.95, 1))
                )

    def ver_detalle_ticket(self, venta):
        items = venta.get("items") or database.get_detalle_venta(venta["id"])
        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(300),
            spacing=dp(8),
            padding=[0, dp(4), 0, 0],
        )

        f_txt = venta["fecha"].strftime("%d/%m/%Y %I:%M %p")
        info_card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(10), dp(4), dp(10), dp(4)],
            radius=[dp(10)],
            elevation=0,
            md_bg_color=(0.95, 0.96, 0.98, 1),
        )
        info_card.add_widget(
            MDLabel(
                text=f"Fecha: {f_txt} • Pago: {venta['metodo_pago']}",
                font_style="Caption",
                bold=True,
            )
        )
        info_card.add_widget(
            MDLabel(
                text=f"Total: ${venta['total']:.2f}  •  Recibido: ${venta.get('recibido', 0.0):.2f}  •  Cambio: ${venta.get('cambio', 0.0):.2f}",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        wrapper.add_widget(info_card)

        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        lista = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(2), dp(2), dp(4), dp(6)],
        )
        lista.bind(minimum_height=lista.setter("height"))

        if not items:
            lista.add_widget(
                MDLabel(
                    text="Ticket registrado antes de activar el desglose individual por producto.",
                    halign="center",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(80),
                )
            )
        else:
            for it in items:
                row = MDCard(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(46),
                    padding=[dp(10), dp(4), dp(10), dp(4)],
                    radius=[dp(8)],
                    elevation=0,
                    md_bg_color=(0.96, 0.98, 0.97, 1),
                )
                left = MDBoxLayout(orientation="vertical", size_hint_x=0.70)
                left.add_widget(
                    MDLabel(
                        text=f"{it['cantidad']}x {it['nombre_producto']}",
                        font_style="Subtitle2",
                        bold=True,
                        shorten=True,
                    )
                )
                left.add_widget(
                    MDLabel(
                        text=f"Cantidad: {it['cantidad']} • P. Venta: ${it['precio_unitario']:.2f}",
                        font_style="Caption",
                        theme_text_color="Secondary",
                        shorten=True,
                    )
                )
                row.add_widget(left)
                row.add_widget(
                    MDLabel(
                        text=f"${it['subtotal']:.2f}",
                        font_style="Subtitle2",
                        bold=True,
                        halign="right",
                        size_hint_x=0.30,
                        theme_text_color="Custom",
                        text_color=(0.13, 0.58, 0.28, 1),
                    )
                )
                lista.add_widget(row)

        comp_img = venta.get("comprobante_img", "")
        if comp_img and os.path.exists(comp_img):
            img = Image(source=comp_img, size_hint_y=None, height=dp(160), fit_mode="contain")
            img.reload()
            lista.add_widget(img)

        scroll.add_widget(lista)
        wrapper.add_widget(scroll)

        self.dialog = MDDialog(
            title=f"Detalle Ticket #{venta['id']:04d}",
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=[
                MDFillRoundFlatButton(
                    text="CERRAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    # ---------------------------------------------------------
    # EXPORTACIÓN EXACTA A EXCEL (.XLSX) CON 4 HOJAS
    # ---------------------------------------------------------
    def exportar_reporte_excel(self, *args):
        datos = database.get_reporte_periodo(self.periodo_actual)
        productos_inv = database.get_productos()

        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        negocio = usuario["negocio"] if usuario else "VentaFácil"
        responsable = usuario["nombre"] if usuario else "Administrador"

        ahora = datetime.datetime.now()
        nombres_periodo = {"diario": "Diario", "semanal": "Semanal", "mensual": "Mensual"}
        etiq_periodo = nombres_periodo.get(self.periodo_actual, "Diario")

        reportes_dir = mobile_utils.get_subdir("reportes_excel")
        nombre_archivo = f"Reporte_{etiq_periodo}_{ahora.strftime('%Y%m%d_%H%M%S')}.xlsx"
        ruta_completa = os.path.join(reportes_dir, nombre_archivo)

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            self._mostrar_aviso_instalar_openpyxl()
            return

        wb = openpyxl.Workbook()

        # Estilos profesionales para Excel
        font_titulo = Font(name="Calibri", size=14, bold=True, color="142D55")
        font_sub = Font(name="Calibri", size=10, italic=True, color="4A5568")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_total = Font(name="Calibri", size=11, bold=True, color="0F3D1E")
        font_data = Font(name="Calibri", size=10, color="1A202C")

        fill_header_verde = PatternFill(start_color="1F8B40", end_color="1F8B40", fill_type="solid")
        fill_header_azul = PatternFill(start_color="1A65B8", end_color="1A65B8", fill_type="solid")
        fill_header_naranja = PatternFill(start_color="D97718", end_color="D97718", fill_type="solid")
        fill_total = PatternFill(start_color="E6F4EA", end_color="E6F4EA", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        borde_fino = Side(border_style="thin", color="CBD5E0")
        border_celda = Border(left=borde_fino, right=borde_fino, top=borde_fino, bottom=borde_fino)
        formato_moneda = "$#,##0.00"

        def autoajustar_columnas(ws):
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val_str = str(cell.value or "")
                    if not val_str.startswith("="):
                        max_len = max(max_len, len(val_str))
                ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 42)

        # =========================================================
        # HOJA 1: DETALLE DE PRODUCTOS VENDIDOS (SIN CÓDIGO / SKU)
        # =========================================================
        ws_prod = wb.active
        ws_prod.title = "Detalle Productos"

        ws_prod["A1"] = f"{negocio} — Productos Vendidos ({etiq_periodo})"
        ws_prod["A1"].font = font_titulo
        ws_prod["A2"] = f"Generado el {ahora.strftime('%d/%m/%Y %I:%M %p')}  |  Responsable: {responsable}"
        ws_prod["A2"].font = font_sub

        headers_prod = [
            "N° Ticket",
            "Fecha",
            "Hora",
            "Producto",
            "Cantidad",
            "Precio Venta ($)",
            "Método de Pago",
            "Ref. Comprobante",
        ]
        fila_enc = 4
        for col_idx, titulo in enumerate(headers_prod, start=1):
            c = ws_prod.cell(row=fila_enc, column=col_idx, value=titulo)
            c.font = font_header
            c.fill = fill_header_verde
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = border_celda
        ws_prod.row_dimensions[fila_enc].height = 24

        filas_p = datos.get("filas_productos", [])
        fila_inicio_datos = 5
        fila_actual = fila_inicio_datos

        for idx, item in enumerate(filas_p):
            nombre_prod = item["producto"]
            if "sin desglose previo" in nombre_prod.lower():
                nombre_prod = f"Venta en mostrador (Ticket #{item['ticket_id']:04d})"

            valores = [
                f"#{item['ticket_id']:04d}",
                item["fecha"],
                item["hora"],
                nombre_prod,
                item["cantidad"],
                item["precio_unitario"],
                item["metodo_pago"],
                item["comprobante"],
            ]
            for col_idx, val in enumerate(valores, start=1):
                c = ws_prod.cell(row=fila_actual, column=col_idx, value=val)
                c.font = font_data
                c.border = border_celda
                if idx % 2 == 1:
                    c.fill = fill_zebra
                if col_idx in (1, 2, 3, 5, 7):
                    c.alignment = Alignment(horizontal="center")
                if col_idx == 6:
                    c.number_format = formato_moneda
                    c.alignment = Alignment(horizontal="right")
            fila_actual += 1

        if filas_p:
            fila_fin_datos = fila_actual - 1
            ws_prod.cell(row=fila_actual, column=4, value="TOTALES DEL PERIODO").font = font_total

            celda_cant = ws_prod.cell(
                row=fila_actual,
                column=5,
                value=f"=SUM(E{fila_inicio_datos}:E{fila_fin_datos})",
            )
            celda_cant.alignment = Alignment(horizontal="center")

            celda_tot = ws_prod.cell(
                row=fila_actual,
                column=6,
                value=f"=SUMPRODUCT(E{fila_inicio_datos}:E{fila_fin_datos},F{fila_inicio_datos}:F{fila_fin_datos})",
            )
            celda_tot.number_format = formato_moneda
            celda_tot.alignment = Alignment(horizontal="right")

            for col_idx in range(1, len(headers_prod) + 1):
                c = ws_prod.cell(row=fila_actual, column=col_idx)
                c.font = font_total
                c.fill = fill_total
                c.border = border_celda

        ws_prod.freeze_panes = "A5"
        autoajustar_columnas(ws_prod)

        # =========================================================
        # HOJA 2: RESUMEN FINANCIERO Y LISTADO DE TICKETS
        # =========================================================
        ws_tickets = wb.create_sheet(title="Tickets y Resumen")
        ws_tickets["A1"] = f"Resumen Financiero Consolidado — {etiq_periodo}"
        ws_tickets["A1"].font = font_titulo

        resumen_kpis = [
            ("Total Ventas:", datos["total_ventas"], True),
            ("Ventas en Efectivo:", datos["total_efectivo"], True),
            ("Ventas por Transferencia:", datos["total_transferencia"], True),
            ("Cantidad de Tickets:", datos["cantidad_ventas"], False),
            ("Total Gastos del Periodo:", datos["total_gastos"], True),
            ("Balance Neto (Ventas - Gastos):", datos["balance_neto"], True),
        ]
        for idx_k, (etiq, val_k, es_moneda) in enumerate(resumen_kpis, start=3):
            c1 = ws_tickets.cell(row=idx_k, column=1, value=etiq)
            c1.font = font_total if "Balance" in etiq or "Total Ventas" in etiq else font_data
            c1.border = border_celda
            c2 = ws_tickets.cell(row=idx_k, column=2, value=val_k)
            c2.font = font_total if "Balance" in etiq or "Total Ventas" in etiq else font_data
            c2.border = border_celda
            if es_moneda:
                c2.number_format = formato_moneda

        fila_t_enc = 10
        headers_tickets = [
            "N° Ticket",
            "Fecha",
            "Hora",
            "Productos Incluidos",
            "Método de Pago",
            "Total Venta ($)",
            "Recibido ($)",
            "Cambio ($)",
            "Ref. Comprobante",
        ]
        for col_idx, titulo in enumerate(headers_tickets, start=1):
            c = ws_tickets.cell(row=fila_t_enc, column=col_idx, value=titulo)
            c.font = font_header
            c.fill = fill_header_azul
            c.alignment = Alignment(horizontal="center")
            c.border = border_celda

        fila_t = fila_t_enc + 1
        for idx, v in enumerate(datos.get("ventas", [])):
            items_v = v.get("items", [])
            desc_items = (
                ", ".join(f"{it['cantidad']}x {it['nombre_producto']}" for it in items_v)
                if items_v
                else f"Venta en mostrador (Ticket #{v['id']:04d})"
            )
            vals_t = [
                f"#{v['id']:04d}",
                v["fecha"].strftime("%d/%m/%Y"),
                v["fecha"].strftime("%I:%M %p"),
                desc_items,
                v["metodo_pago"],
                v["total"],
                v.get("recibido", 0.0),
                v.get("cambio", 0.0),
                v.get("comprobante") or "-",
            ]
            for col_idx, val in enumerate(vals_t, start=1):
                c = ws_tickets.cell(row=fila_t, column=col_idx, value=val)
                c.font = font_data
                c.border = border_celda
                if idx % 2 == 1:
                    c.fill = fill_zebra
                if col_idx in (6, 7, 8):
                    c.number_format = formato_moneda
            fila_t += 1

        if datos.get("ventas"):
            ws_tickets.cell(row=fila_t, column=4, value="TOTAL TICKETS").font = font_total
            for col_s in (6, 7, 8):
                letra = get_column_letter(col_s)
                ct = ws_tickets.cell(row=fila_t, column=col_s, value=f"=SUM({letra}11:{letra}{fila_t - 1})")
                ct.number_format = formato_moneda
            for col_idx in range(1, len(headers_tickets) + 1):
                c = ws_tickets.cell(row=fila_t, column=col_idx)
                c.font = font_total
                c.fill = fill_total
                c.border = border_celda

        autoajustar_columnas(ws_tickets)

        # =========================================================
        # HOJA 3: GASTOS DEL PERIODO
        # =========================================================
        ws_gastos = wb.create_sheet(title="Gastos Periodo")
        ws_gastos["A1"] = f"Egresos y Gastos Registrados — {etiq_periodo}"
        ws_gastos["A1"].font = font_titulo

        headers_gastos = ["ID", "Fecha", "Hora", "Descripción", "Categoría", "Método de Pago", "Monto ($)"]
        for col_idx, titulo in enumerate(headers_gastos, start=1):
            c = ws_gastos.cell(row=3, column=col_idx, value=titulo)
            c.font = font_header
            c.fill = fill_header_naranja
            c.alignment = Alignment(horizontal="center")
            c.border = border_celda

        fila_g = 4
        for idx, g in enumerate(datos.get("gastos", [])):
            vals_g = [
                g["id"],
                g["fecha"].strftime("%d/%m/%Y"),
                g["fecha"].strftime("%I:%M %p"),
                g["descripcion"],
                g["categoria"],
                g["metodo_pago"],
                g["monto"],
            ]
            for col_idx, val in enumerate(vals_g, start=1):
                c = ws_gastos.cell(row=fila_g, column=col_idx, value=val)
                c.font = font_data
                c.border = border_celda
                if idx % 2 == 1:
                    c.fill = fill_zebra
                if col_idx == 7:
                    c.number_format = formato_moneda
            fila_g += 1

        if datos.get("gastos"):
            ws_gastos.cell(row=fila_g, column=4, value="TOTAL GASTOS").font = font_total
            cg = ws_gastos.cell(row=fila_g, column=7, value=f"=SUM(G4:G{fila_g - 1})")
            cg.number_format = formato_moneda
            for col_idx in range(1, len(headers_gastos) + 1):
                c = ws_gastos.cell(row=fila_g, column=col_idx)
                c.font = font_total
                c.fill = fill_total
                c.border = border_celda

        autoajustar_columnas(ws_gastos)

        # =========================================================
        # HOJA 4: ESTADO ACTUAL DE INVENTARIO
        # =========================================================
        ws_inv = wb.create_sheet(title="Inventario Actual")
        ws_inv["A1"] = f"Valoración de Inventario al {ahora.strftime('%d/%m/%Y %I:%M %p')}"
        ws_inv["A1"].font = font_titulo

        headers_inv = [
            "ID",
            "Producto",
            "Categoría",
            "Stock Actual",
            "Costo Unit. ($)",
            "Precio Venta ($)",
            "Valor Costo Total ($)",
            "Valor Venta Total ($)",
            "Estado",
        ]
        for col_idx, titulo in enumerate(headers_inv, start=1):
            c = ws_inv.cell(row=3, column=col_idx, value=titulo)
            c.font = font_header
            c.fill = fill_header_verde
            c.alignment = Alignment(horizontal="center")
            c.border = border_celda

        fila_i = 4
        for idx, p in enumerate(productos_inv):
            stk = int(p.get("stock", 0))
            estado_stk = "AGOTADO" if stk == 0 else ("STOCK BAJO" if stk <= 5 else "DISPONIBLE")
            vals_i = [
                p["id"],
                p["nombre"],
                p.get("categoria", "General"),
                stk,
                p.get("precio_costo", 0.0),
                p.get("precio_venta", 0.0),
                f"=D{fila_i}*E{fila_i}",
                f"=D{fila_i}*F{fila_i}",
                estado_stk,
            ]
            for col_idx, val in enumerate(vals_i, start=1):
                c = ws_inv.cell(row=fila_i, column=col_idx, value=val)
                c.font = font_data
                c.border = border_celda
                if idx % 2 == 1:
                    c.fill = fill_zebra
                if col_idx in (5, 6, 7, 8):
                    c.number_format = formato_moneda
            fila_i += 1

        if productos_inv:
            ws_inv.cell(row=fila_i, column=2, value="TOTAL INVENTARIO").font = font_total
            ws_inv.cell(row=fila_i, column=4, value=f"=SUM(D4:D{fila_i - 1})")
            for col_si in (7, 8):
                letra = get_column_letter(col_si)
                ci = ws_inv.cell(row=fila_i, column=col_si, value=f"=SUM({letra}4:{letra}{fila_i - 1})")
                ci.number_format = formato_moneda
            for col_idx in range(1, len(headers_inv) + 1):
                c = ws_inv.cell(row=fila_i, column=col_idx)
                c.font = font_total
                c.fill = fill_total
                c.border = border_celda

        autoajustar_columnas(ws_inv)

        wb.save(ruta_completa)

        resumen_msg = (
            f"Archivo Excel generado con éxito:\n"
            f"• {nombre_archivo}\n\n"
            f"Contenido incluido (4 hojas):\n"
            f"• Detalle Productos: {len(filas_p)} registro(s)\n"
            f"• Tickets y Resumen: {datos['cantidad_ventas']} ticket(s) (${datos['total_ventas']:.2f})\n"
            f"• Gastos Periodo: {len(datos.get('gastos', []))} egreso(s) (${datos['total_gastos']:.2f})\n"
            f"• Inventario Actual: {len(productos_inv)} producto(s)"
        )

        def abrir_excel(inst):
            mobile_utils.compartir_o_abrir_archivo(ruta_completa, titulo="Reporte Excel VentaFácil")

        self.dialog = MDDialog(
            title="Reporte Excel Exportado",
            text=resumen_msg,
            size_hint_x=0.92,
            buttons=[
                MDRoundFlatButton(
                    text="ABRIR / COMPARTIR",
                    icon="microsoft-excel",
                    line_color=(0.13, 0.58, 0.28, 1),
                    text_color=(0.13, 0.58, 0.28, 1),
                    on_release=abrir_excel,
                ),
                MDFillRoundFlatButton(
                    text="CERRAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                ),
            ],
        )
        self.dialog.open()

    def _mostrar_aviso_instalar_openpyxl(self):
        self.dialog = MDDialog(
            title="Librería Excel Requerida",
            text="Para generar archivos .xlsx instala openpyxl ejecutando en tu terminal:\n\npip install openpyxl",
            size_hint_x=0.90,
            buttons=[
                MDFillRoundFlatButton(
                    text="ENTENDIDO",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    def volver_atras(self):
        if self.manager and "dashboard" in self.manager.screen_names:
            self.manager.current = "dashboard"


ReportesScreen = ReportsScreen