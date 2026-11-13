import os
import html
import shutil
import time
import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserIconView
from kivy.app import App
from kivy.metrics import dp
import database
import mobile_utils


class CheckoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_cobrar = 0.0
        self.cantidad_items = 0
        self.carrito = []
        self.metodo_pago = "Efectivo"
        self.comprobante_img_path = ""
        self.ultimo_ticket_path = ""
        self.dialog = None
        self.file_dialog = None

        root = MDBoxLayout(orientation="vertical", md_bg_color=(0.96, 0.97, 0.98, 1))

        # 1. BARRA SUPERIOR
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
            on_release=lambda x: self.volver_a_pos()
        )
        lbl_title = MDLabel(
            text="Procesar Pago",
            font_style="H6",
            bold=True,
            pos_hint={"center_y": 0.5}
        )
        header.add_widget(btn_back)
        header.add_widget(lbl_title)
        root.add_widget(header)

        # 2. CONTENIDO DESPLAZABLE
        scroll = MDScrollView()
        body = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(14), dp(16), dp(24)],
            spacing=dp(14),
            size_hint_y=None
        )
        body.bind(minimum_height=body.setter("height"))

        # Tarjeta Total a Cobrar
        total_card = MDCard(
            orientation="vertical",
            padding=[dp(18), dp(14), dp(18), dp(14)],
            spacing=dp(2),
            radius=[dp(16)],
            elevation=2,
            md_bg_color=(0.13, 0.65, 0.34, 1),
            size_hint_y=None,
            height=dp(120)
        )
        total_card.add_widget(
            MDLabel(
                text="Total a Cobrar",
                font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.92),
                size_hint_y=None,
                height=dp(22)
            )
        )
        self.lbl_total_cobrar = MDLabel(
            text="$0.00",
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(44)
        )
        self.lbl_items_count = MDLabel(
            text="0 artículo(s) en la orden",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.88),
            size_hint_y=None,
            height=dp(18)
        )
        total_card.add_widget(self.lbl_total_cobrar)
        total_card.add_widget(self.lbl_items_count)
        body.add_widget(total_card)

        # Selector Método de Pago
        body.add_widget(
            MDLabel(
                text="Método de Pago",
                font_style="Subtitle2",
                bold=True,
                size_hint_y=None,
                height=dp(22)
            )
        )

        methods_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(44)
        )
        self.btn_efectivo = MDFillRoundFlatButton(
            text="Efectivo",
            icon="cash",
            size_hint_x=0.48,
            height=dp(44),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            text_color=(1, 1, 1, 1),
            on_release=lambda x: self.seleccionar_metodo("Efectivo")
        )
        self.btn_transferencia = MDFillRoundFlatButton(
            text="Transferencia",
            icon="bank-transfer",
            size_hint_x=0.52,
            height=dp(44),
            md_bg_color=(0.88, 0.90, 0.92, 1),
            text_color=(0.20, 0.25, 0.22, 1),
            on_release=lambda x: self.seleccionar_metodo("Transferencia")
        )
        methods_row.add_widget(self.btn_efectivo)
        methods_row.add_widget(self.btn_transferencia)
        body.add_widget(methods_row)

        # Contenedor dinámico
        self.dynamic_payment_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None
        )
        self.dynamic_payment_box.bind(minimum_height=self.dynamic_payment_box.setter("height"))
        body.add_widget(self.dynamic_payment_box)

        self._construir_panel_efectivo()
        self._construir_panel_transferencia()

        btn_confirmar = MDFillRoundFlatButton(
            text="CONFIRMAR Y FINALIZAR VENTA",
            font_size="14sp",
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=(0.13, 0.55, 0.25, 1),
            on_release=self.finalizar_venta
        )
        body.add_widget(btn_confirmar)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _construir_panel_efectivo(self):
        self.panel_efectivo = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )
        self.panel_efectivo.bind(minimum_height=self.panel_efectivo.setter("height"))

        self.input_recibido = MDTextField(
            hint_text="Monto recibido en efectivo ($)",
            mode="round",
            icon_left="currency-usd",
            input_filter="float",
            font_size="18sp",
            size_hint_y=None,
            height=dp(50),
            fill_color_normal=(1, 1, 1, 1)
        )
        self.input_recibido.bind(text=self.calcular_cambio)
        self.panel_efectivo.add_widget(self.input_recibido)

        # Cuadrícula de billetes rápidos adaptable a pantalla de celular
        quick_grid = MDGridLayout(
            cols=3,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(84)
        )
        btn_exacto = MDRoundFlatButton(
            text="Exacto",
            size_hint_x=1,
            line_color=(0.13, 0.55, 0.25, 1),
            text_color=(0.13, 0.55, 0.25, 1),
            on_release=lambda x: setattr(self.input_recibido, "text", f"{self.total_cobrar:.2f}")
        )
        quick_grid.add_widget(btn_exacto)

        for billete in (1, 5, 10, 20, 50):
            btn_b = MDRoundFlatButton(
                text=f"${billete}",
                size_hint_x=1,
                line_color=(0.65, 0.68, 0.72, 1),
                text_color=(0.25, 0.30, 0.35, 1),
                on_release=lambda x, b=billete: setattr(self.input_recibido, "text", f"{b:.2f}")
            )
            quick_grid.add_widget(btn_b)
        self.panel_efectivo.add_widget(quick_grid)

        self.lbl_cambio = MDLabel(
            text="Cambio: $0.00",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint_y=None,
            height=dp(30)
        )
        self.panel_efectivo.add_widget(self.lbl_cambio)

    def _construir_panel_transferencia(self):
        self.panel_transferencia = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )
        self.panel_transferencia.bind(minimum_height=self.panel_transferencia.setter("height"))

        info_card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(12)],
            spacing=dp(10),
            radius=[dp(14)],
            elevation=1,
            md_bg_color=(1, 1, 1, 1),
            size_hint_y=None
        )
        info_card.bind(minimum_height=info_card.setter("height"))

        self.lbl_monto_transferencia = MDLabel(
            text="Monto exacto: $0.00",
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.13, 0.55, 0.25, 1),
            size_hint_y=None,
            height=dp(22)
        )
        info_card.add_widget(self.lbl_monto_transferencia)

        self.input_comprobante = MDTextField(
            hint_text="N° Comprobante / Referencia",
            mode="round",
            icon_left="receipt-text-check-outline",
            size_hint_y=None,
            height=dp(50),
            fill_color_normal=(0.97, 0.98, 0.99, 1)
        )
        info_card.add_widget(self.input_comprobante)

        btn_adjuntar = MDRoundFlatButton(
            text="Adjuntar Captura de Galería",
            icon="image-plus",
            size_hint_x=1,
            line_color=(0.13, 0.52, 0.89, 1),
            text_color=(0.13, 0.52, 0.89, 1),
            on_release=self.seleccionar_imagen_comprobante
        )
        self.lbl_archivo_comprobante = MDLabel(
            text="Opcional: sin captura adjunta",
            font_style="Caption",
            theme_text_color="Secondary",
            shorten=True,
            size_hint_y=None,
            height=dp(18)
        )
        info_card.add_widget(btn_adjuntar)
        info_card.add_widget(self.lbl_archivo_comprobante)

        self.panel_transferencia.add_widget(info_card)

    def set_order(self, cart, total=None):
        self.carrito = cart if cart else []
        try:
            self.total_cobrar = float(total) if total is not None else 0.0
        except (TypeError, ValueError):
            self.total_cobrar = 0.0
        self._actualizar_resumen_ui()

    def set_datos_venta(self, carrito, total=None):
        self.set_order(carrito, total)

    def cargar_venta(self, carrito, total=None):
        self.set_order(carrito, total)

    def on_pre_enter(self, *args):
        if self.manager and "pos" in self.manager.screen_names:
            pos_screen = self.manager.get_screen("pos")
            if not self.carrito:
                self.carrito = getattr(pos_screen, "cart", getattr(pos_screen, "carrito", []))
            if self.total_cobrar <= 0:
                self.total_cobrar = float(getattr(pos_screen, "total", 0.0))

        self.comprobante_img_path = ""
        self.input_recibido.text = ""
        self.input_comprobante.text = ""
        self.lbl_archivo_comprobante.text = "Opcional: sin captura adjunta"
        self._actualizar_resumen_ui()
        self.seleccionar_metodo("Efectivo")

    def _extraer_items_normalizados(self):
        if not self.carrito:
            return []

        productos_db = database.get_productos()
        prod_por_id = {p["id"]: p for p in productos_db}
        prod_por_nombre = {p["nombre"].strip().lower(): p for p in productos_db}
        items_norm = []

        if isinstance(self.carrito, dict):
            for key, item in self.carrito.items():
                if isinstance(item, dict):
                    cant = int(item.get("cantidad", item.get("qty", 1)))
                    nombre = item.get("nombre")
                    precio = item.get("precio_venta", item.get("precio", None))
                    if nombre is None or precio is None:
                        pid = item.get("id", key)
                        ref = prod_por_id.get(pid) or prod_por_nombre.get(str(nombre or key).strip().lower(), {})
                        nombre = nombre or ref.get("nombre", f"Producto #{pid}")
                        if precio is None:
                            precio = ref.get("precio_venta", ref.get("precio", 0.0))
                    precio_f = float(precio)
                    items_norm.append({
                        "nombre": str(nombre),
                        "cantidad": cant,
                        "precio": precio_f,
                        "subtotal": round(precio_f * cant, 2)
                    })
        elif isinstance(self.carrito, list):
            for item in self.carrito:
                if isinstance(item, dict):
                    cant = int(item.get("cantidad", item.get("qty", 1)))
                    nombre = item.get("nombre", "Artículo")
                    precio_f = float(item.get("precio_venta", item.get("precio", 0.0)))
                    items_norm.append({
                        "nombre": str(nombre),
                        "cantidad": cant,
                        "precio": precio_f,
                        "subtotal": round(precio_f * cant, 2)
                    })
        return items_norm

    def _actualizar_resumen_ui(self):
        items = self._extraer_items_normalizados()
        self.cantidad_items = sum(i["cantidad"] for i in items)
        suma_calculada = round(sum(i["subtotal"] for i in items), 2)

        if suma_calculada > 0:
            self.total_cobrar = suma_calculada

        self.lbl_total_cobrar.text = f"${self.total_cobrar:.2f}"
        self.lbl_items_count.text = f"{self.cantidad_items} artículo(s) en la orden"
        self.lbl_monto_transferencia.text = f"Monto exacto por transferencia: ${self.total_cobrar:.2f}"
        self.calcular_cambio(self.input_recibido, self.input_recibido.text)

    def seleccionar_metodo(self, metodo):
        self.metodo_pago = metodo
        self.dynamic_payment_box.clear_widgets()

        if metodo == "Efectivo":
            self.btn_efectivo.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_efectivo.text_color = (1, 1, 1, 1)
            self.btn_transferencia.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_transferencia.text_color = (0.20, 0.25, 0.22, 1)
            self.dynamic_payment_box.add_widget(self.panel_efectivo)
            self.calcular_cambio(self.input_recibido, self.input_recibido.text)
        else:
            self.btn_transferencia.md_bg_color = (0.13, 0.55, 0.25, 1)
            self.btn_transferencia.text_color = (1, 1, 1, 1)
            self.btn_efectivo.md_bg_color = (0.88, 0.90, 0.92, 1)
            self.btn_efectivo.text_color = (0.20, 0.25, 0.22, 1)
            self.lbl_monto_transferencia.text = f"Monto exacto por transferencia: ${self.total_cobrar:.2f}"
            self.dynamic_payment_box.add_widget(self.panel_transferencia)

    def calcular_cambio(self, instance, texto):
        limpio = texto.strip().replace(",", ".")
        try:
            recibido = float(limpio) if limpio else 0.0
        except ValueError:
            recibido = 0.0

        if recibido + 1e-6 >= self.total_cobrar and self.total_cobrar > 0:
            cambio = max(0.0, recibido - self.total_cobrar)
            self.lbl_cambio.text = f"Cambio: ${cambio:.2f}"
            self.lbl_cambio.text_color = (0.13, 0.55, 0.25, 1)
        else:
            faltante = max(0.0, self.total_cobrar - recibido)
            self.lbl_cambio.text = f"Cambio: $0.00 (Falta: ${faltante:.2f})"
            self.lbl_cambio.text_color = (0.85, 0.25, 0.25, 1)

    def seleccionar_imagen_comprobante(self, *args):
        mobile_utils.seleccionar_imagen_dispositivo(
            self._guardar_archivo_comprobante,
            fallback_kivy_fn=self._abrir_selector_kivy
        )

    def _abrir_selector_kivy(self):
        chooser = FileChooserIconView(
            filters=["*.png", "*.jpg", "*.jpeg", "*.webp"],
            size_hint_y=None,
            height=dp(260)
        )

        def confirmar(inst):
            if chooser.selection:
                self._guardar_archivo_comprobante(chooser.selection[0])
            self.file_dialog.dismiss()

        self.file_dialog = MDDialog(
            title="Seleccionar Comprobante",
            type="custom",
            size_hint_x=0.92,
            content_cls=chooser,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda x: self.file_dialog.dismiss()),
                MDFillRoundFlatButton(
                    text="ADJUNTAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=confirmar
                )
            ]
        )
        self.file_dialog.open()

    def _guardar_archivo_comprobante(self, ruta_origen):
        if not ruta_origen or not os.path.exists(ruta_origen):
            return
        carpeta = mobile_utils.get_subdir("assets", "comprobantes")
        ext = os.path.splitext(ruta_origen)[1].lower() or ".png"
        nombre_archivo = f"comp_{int(time.time() * 1000)}{ext}"
        ruta_destino = os.path.join(carpeta, nombre_archivo)
        shutil.copy2(ruta_origen, ruta_destino)
        self.comprobante_img_path = ruta_destino
        self.lbl_archivo_comprobante.text = f"Adjunto: {os.path.basename(ruta_origen)}"

    def _generar_comprobante_venta(self, venta_id, items_vendidos, total, recibido, cambio, metodo, comprobante_ref):
        app = App.get_running_app()
        usuario = getattr(app, "usuario_actual", None) if app else None
        nombre_negocio = html.escape(usuario.get("negocio", "Abarrotes VentaFácil") if usuario else "Abarrotes VentaFácil")
        nombre_cajero = html.escape(usuario.get("nombre", "Administrador") if usuario else "Administrador")
        fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")

        filas_html = ""
        for item in items_vendidos:
            nom = html.escape(item["nombre"])
            cant = item["cantidad"]
            pu = item["precio"]
            sub = item["subtotal"]
            filas_html += f"""
            <tr>
                <td><strong>{cant}</strong></td>
                <td>{nom}<br><small>${pu:.2f} c/u</small></td>
                <td style="text-align:right;">${sub:.2f}</td>
            </tr>
            """

        if metodo == "Transferencia":
            pago_html = f"""
            <div class="row"><span>Método:</span><strong>Transferencia</strong></div>
            <div class="row"><span>N° Comprobante:</span><strong>{html.escape(comprobante_ref)}</strong></div>
            """
        else:
            pago_html = f"""
            <div class="row"><span>Método:</span><strong>Efectivo</strong></div>
            <div class="row"><span>Recibido:</span><strong>${recibido:.2f}</strong></div>
            <div class="row"><span>Cambio:</span><strong>${cambio:.2f}</strong></div>
            """

        html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ticket #{venta_id:04d}</title>
<style>
    body {{ font-family: sans-serif; background: #f0f2f5; padding: 16px; display: flex; flex-direction: column; align-items: center; }}
    .ticket {{ background: #fff; width: 100%; max-width: 340px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
    .center {{ text-align: center; }}
    h2 {{ margin: 0 0 4px 0; color: #1f8b40; }}
    .divider {{ border-top: 1px dashed #cbd5e0; margin: 12px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    td {{ padding: 6px 0; border-bottom: 1px dotted #edf2f7; }}
    .total {{ display: flex; justify-content: space-between; font-size: 18px; font-weight: bold; color: #1f8b40; }}
    .row {{ display: flex; justify-content: space-between; font-size: 13px; margin: 4px 0; }}
    .btn {{ margin-top: 16px; background: #1f8b40; color: #fff; border: none; padding: 12px 20px; border-radius: 24px; font-weight: bold; }}
    @media print {{ .btn {{ display: none; }} body {{ background: #fff; padding: 0; }} .ticket {{ box-shadow: none; }} }}
</style>
</head>
<body>
    <div class="ticket">
        <div class="center">
            <h2>{nombre_negocio}</h2>
            <small>Ticket #{venta_id:04d} • {fecha_hora}<br>Atendió: {nombre_cajero}</small>
        </div>
        <div class="divider"></div>
        <table><tbody>{filas_html}</tbody></table>
        <div class="divider"></div>
        <div class="total"><span>TOTAL:</span><span>${total:.2f}</span></div>
        {pago_html}
        <div class="divider"></div>
        <div class="center"><small>¡Gracias por su compra!</small></div>
    </div>
    <button class="btn" onclick="window.print()">Imprimir / Guardar PDF</button>
</body>
</html>
"""
        carpeta_tickets = mobile_utils.get_subdir("comprobantes_emitidos")
        ruta_completa = os.path.join(carpeta_tickets, f"Ticket_{venta_id:04d}.html")
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(html_doc)
        return ruta_completa

    def finalizar_venta(self, *args):
        if self.total_cobrar <= 0:
            self.mostrar_dialogo("Orden vacía", "No hay productos con monto válido para cobrar.")
            return

        comprobante_num = ""
        comprobante_img = ""

        if self.metodo_pago == "Efectivo":
            texto_recibido = self.input_recibido.text.strip().replace(",", ".")
            try:
                recibido = float(texto_recibido) if texto_recibido else 0.0
            except ValueError:
                recibido = 0.0

            if recibido + 1e-6 < self.total_cobrar:
                self.mostrar_dialogo(
                    "Monto insuficiente",
                    f"El monto recibido (${recibido:.2f}) es menor al total (${self.total_cobrar:.2f})."
                )
                return

            cambio = max(0.0, round(recibido - self.total_cobrar, 2))
        else:
            comprobante_num = self.input_comprobante.text.strip()
            if not comprobante_num:
                self.mostrar_dialogo(
                    "Comprobante requerido",
                    "Ingresa el número de comprobante o referencia de la transferencia."
                )
                return

            recibido = round(self.total_cobrar, 2)
            cambio = 0.0
            comprobante_img = self.comprobante_img_path

        items_vendidos = self._extraer_items_normalizados()
        total_final = round(self.total_cobrar, 2)
        metodo_final = self.metodo_pago

        venta_id = database.insert_venta(
            total_final,
            recibido,
            cambio,
            metodo_final,
            comprobante=comprobante_num,
            comprobante_img=comprobante_img
        )

        database.descontar_stock_items(self.carrito)

        self.ultimo_ticket_path = self._generar_comprobante_venta(
            venta_id, items_vendidos, total_final, recibido, cambio, metodo_final, comprobante_num
        )

        self._limpiar_carrito_pos()
        self.total_cobrar = 0.0
        self.carrito = []

        self.mostrar_comprobante_modal(
            venta_id, items_vendidos, total_final, recibido, cambio, metodo_final, comprobante_num
        )

    def mostrar_comprobante_modal(self, venta_id, items_vendidos, total, recibido, cambio, metodo, comprobante_num):
        wrapper = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(260),
            padding=[0, dp(4), 0, 0]
        )
        scroll = MDScrollView(do_scroll_x=False, do_scroll_y=True)
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=[dp(2), dp(4), dp(4), dp(8)]
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(
            MDLabel(
                text=f"Ticket #{venta_id:04d} • {datetime.datetime.now().strftime('%d/%m/%Y %I:%M %p')}",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(20)
            )
        )
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.88, 0.90, 0.92, 1)))

        for item in items_vendidos:
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            row.add_widget(MDLabel(text=f"{item['cantidad']}x {item['nombre']}", font_style="Body2", shorten=True, size_hint_x=0.72))
            row.add_widget(MDLabel(text=f"${item['subtotal']:.2f}", font_style="Body2", bold=True, halign="right", size_hint_x=0.28))
            content.add_widget(row)

        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.88, 0.90, 0.92, 1)))

        row_total = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        row_total.add_widget(MDLabel(text="TOTAL:", font_style="Subtitle1", bold=True))
        row_total.add_widget(
            MDLabel(
                text=f"${total:.2f}",
                font_style="Subtitle1",
                bold=True,
                halign="right",
                theme_text_color="Custom",
                text_color=(0.13, 0.55, 0.25, 1)
            )
        )
        content.add_widget(row_total)

        info_pago = (
            f"Transferencia • Comp: {comprobante_num}"
            if metodo == "Transferencia"
            else f"Efectivo • Recibido: ${recibido:.2f} • Cambio: ${cambio:.2f}"
        )
        content.add_widget(
            MDLabel(text=info_pago, font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=dp(20))
        )

        scroll.add_widget(content)
        wrapper.add_widget(scroll)

        def cerrar_y_volver(inst):
            self.dialog.dismiss()
            self.volver_a_pos()

        def compartir_ticket(inst):
            mobile_utils.compartir_o_abrir_archivo(
                self.ultimo_ticket_path,
                titulo=f"Comprobante Ticket #{venta_id:04d}"
            )

        self.dialog = MDDialog(
            title="¡Comprobante Generado!",
            type="custom",
            size_hint_x=0.92,
            content_cls=wrapper,
            buttons=[
                MDRoundFlatButton(
                    text="IMPRIMIR / COMPARTIR",
                    icon="share-variant",
                    line_color=(0.13, 0.52, 0.89, 1),
                    text_color=(0.13, 0.52, 0.89, 1),
                    on_release=compartir_ticket
                ),
                MDFillRoundFlatButton(
                    text="LISTO",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=cerrar_y_volver
                )
            ]
        )
        self.dialog.open()

    def _limpiar_carrito_pos(self):
        if not self.manager or "pos" not in self.manager.screen_names:
            return
        pos_screen = self.manager.get_screen("pos")
        for attr in ("carrito", "cart", "items", "orden"):
            coleccion = getattr(pos_screen, attr, None)
            if isinstance(coleccion, (list, dict)):
                coleccion.clear()
        for fn_name in ("limpiar_carrito", "clear_cart", "actualizar_carrito_ui"):
            fn = getattr(pos_screen, fn_name, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass

    def mostrar_dialogo(self, titulo, mensaje, volver_pos=False):
        def cerrar(inst):
            self.dialog.dismiss()
            if volver_pos:
                self.volver_a_pos()

        self.dialog = MDDialog(
            title=titulo,
            text=mensaje,
            size_hint_x=0.90,
            buttons=[
                MDFillRoundFlatButton(
                    text="ACEPTAR",
                    md_bg_color=(0.13, 0.55, 0.25, 1),
                    on_release=cerrar
                )
            ]
        )
        self.dialog.open()

    def volver_a_pos(self):
        if self.manager and "pos" in self.manager.screen_names:
            self.manager.current = "pos"