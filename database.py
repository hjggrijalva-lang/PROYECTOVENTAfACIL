import os
import sqlite3
import datetime
import mobile_utils

ULTIMA_ALERTA_STOCK = ""
_BUFFER_ITEMS_VENTA = []
_BUFFER_TIMESTAMP = None
_ULTIMA_VENTA_SIN_DETALLE = None


def get_db_path():
    return os.path.join(mobile_utils.get_data_dir(), "ventafacil.db")


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn


def _migrar_detalle_ventas(cursor):
    """Asegura que la tabla detalle_ventas tenga todas las columnas necesarias incluso en BD antiguas."""
    cursor.execute("PRAGMA table_info(detalle_ventas)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}

    columnas_requeridas = {
        "venta_id": "INTEGER DEFAULT 0",
        "producto_id": "INTEGER",
        "sku": "TEXT DEFAULT ''",
        "nombre_producto": "TEXT DEFAULT ''",
        "categoria": "TEXT DEFAULT 'General'",
        "cantidad": "INTEGER DEFAULT 1",
        "precio_costo": "REAL DEFAULT 0.0",
        "precio_unitario": "REAL DEFAULT 0.0",
        "subtotal": "REAL DEFAULT 0.0",
    }

    for col, definicion in columnas_requeridas.items():
        if col not in columnas_existentes:
            try:
                cursor.execute(f"ALTER TABLE detalle_ventas ADD COLUMN {col} {definicion}")
            except sqlite3.OperationalError:
                pass


def _reconstruir_detalle_ticket_historico(cursor, venta_id, total_venta, catalogo):
    """Asocia productos del catálogo a tickets antiguos que no tenían filas en detalle_ventas."""
    objetivo_centavos = int(round(float(total_venta or 0.0) * 100))
    if objetivo_centavos <= 0 or not catalogo:
        return False

    for prod in catalogo:
        if objetivo_centavos % prod["centavos"] == 0:
            cant = objetivo_centavos // prod["centavos"]
            if 1 <= cant <= 10:
                _guardar_detalle_venta(
                    cursor,
                    venta_id,
                    [
                        {
                            "producto_id": prod["id"],
                            "sku": prod["sku"],
                            "nombre_producto": prod["nombre"],
                            "categoria": prod["categoria"],
                            "cantidad": cant,
                            "precio_costo": prod["precio_costo"],
                            "precio_unitario": prod["precio_venta"],
                            "subtotal": round(prod["precio_venta"] * cant, 2),
                        }
                    ],
                )
                return True

    seleccion = []

    def buscar_combinacion(idx_inicio, restante, unidades_usadas):
        if restante == 0:
            return True
        if unidades_usadas >= 5:
            return False
        for i in range(idx_inicio, len(catalogo)):
            p = catalogo[i]
            if p["centavos"] <= restante:
                seleccion.append(p)
                if buscar_combinacion(i, restante - p["centavos"], unidades_usadas + 1):
                    return True
                seleccion.pop()
        return False

    if buscar_combinacion(0, objetivo_centavos, 0) and seleccion:
        agrupados = {}
        for p in seleccion:
            pid = p["id"]
            if pid not in agrupados:
                agrupados[pid] = {
                    "producto_id": pid,
                    "sku": p["sku"],
                    "nombre_producto": p["nombre"],
                    "categoria": p["categoria"],
                    "cantidad": 0,
                    "precio_costo": p["precio_costo"],
                    "precio_unitario": p["precio_venta"],
                    "subtotal": 0.0,
                }
            agrupados[pid]["cantidad"] += 1
            agrupados[pid]["subtotal"] = round(
                agrupados[pid]["cantidad"] * agrupados[pid]["precio_unitario"], 2
            )

        _guardar_detalle_venta(cursor, venta_id, list(agrupados.values()))
        return True

    return False


def init_db():
    """Crea las tablas, índices de velocidad y migra esquemas anteriores."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            negocio TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            pin TEXT NOT NULL,
            rol TEXT DEFAULT 'admin',
            fecha_creacion TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            sku TEXT,
            categoria TEXT DEFAULT 'Granos y Cereales',
            precio_costo REAL DEFAULT 0.0,
            precio_venta REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            imagen TEXT DEFAULT ''
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL,
            recibido REAL DEFAULT 0.0,
            cambio REAL DEFAULT 0.0,
            metodo_pago TEXT DEFAULT 'Efectivo',
            comprobante TEXT DEFAULT '',
            comprobante_img TEXT DEFAULT '',
            fecha TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER,
            sku TEXT DEFAULT '',
            nombre_producto TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            cantidad INTEGER NOT NULL DEFAULT 1,
            precio_costo REAL DEFAULT 0.0,
            precio_unitario REAL NOT NULL DEFAULT 0.0,
            subtotal REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            monto REAL NOT NULL,
            metodo_pago TEXT DEFAULT 'Efectivo',
            fecha TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    migraciones = [
        "ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'admin'",
        "ALTER TABLE productos ADD COLUMN sku TEXT DEFAULT ''",
        "ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'Granos y Cereales'",
        "ALTER TABLE productos ADD COLUMN precio_costo REAL DEFAULT 0.0",
        "ALTER TABLE productos ADD COLUMN precio_venta REAL DEFAULT 0.0",
        "ALTER TABLE productos ADD COLUMN imagen TEXT DEFAULT ''",
        "ALTER TABLE ventas ADD COLUMN recibido REAL DEFAULT 0.0",
        "ALTER TABLE ventas ADD COLUMN cambio REAL DEFAULT 0.0",
        "ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'",
        "ALTER TABLE ventas ADD COLUMN comprobante TEXT DEFAULT ''",
        "ALTER TABLE ventas ADD COLUMN comprobante_img TEXT DEFAULT ''",
        "ALTER TABLE gastos ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'",
    ]
    for sql in migraciones:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass

    _migrar_detalle_ventas(cursor)

    # Índices para acelerar consultas de reportes, tickets y alertas de stock
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_detalle_venta_id ON detalle_ventas(venta_id)",
        "CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_productos_stock ON productos(stock)",
    ]
    for idx_sql in indices:
        cursor.execute(idx_sql)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO usuarios (nombre, negocio, email, password, pin, rol)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Administrador", "Abarrotes VentaFácil", "admin@ventafacil.com", "admin1234", "1234", "admin"),
        )
        cursor.execute(
            """
            INSERT INTO usuarios (nombre, negocio, email, password, pin, rol)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Carlos Cajero", "Abarrotes VentaFácil", "cajero@ventafacil.com", "cajero1234", "0000", "cajero"),
        )

    conn.commit()
    conn.close()


# -------------------------------------------------------------
# GESTIÓN DE USUARIOS Y AUTENTICACIÓN
# -------------------------------------------------------------
def get_usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, negocio, email, pin, rol FROM usuarios ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "nombre": r[1],
            "negocio": r[2],
            "email": r[3],
            "pin": r[4],
            "rol": r[5] or "admin",
        }
        for r in rows
    ]


def register_usuario(nombre, negocio, email, password, pin, rol="admin"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE lower(email) = lower(?)", (email.strip(),))
        if cursor.fetchone():
            return False, "Ya existe un usuario registrado con ese correo o teléfono."

        cursor.execute("SELECT id FROM usuarios WHERE pin = ?", (pin.strip(),))
        if cursor.fetchone():
            return False, "Ese PIN ya está en uso por otro usuario. Elige uno diferente."

        cursor.execute(
            """
            INSERT INTO usuarios (nombre, negocio, email, password, pin, rol)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nombre.strip(), negocio.strip(), email.strip(), password.strip(), pin.strip(), rol),
        )
        conn.commit()
        return True, f"Usuario '{nombre.strip()}' creado correctamente."
    except Exception as e:
        return False, f"Error al registrar usuario: {e}"
    finally:
        conn.close()


def delete_usuario(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre, rol FROM usuarios WHERE id = ?", (user_id,))
        fila = cursor.fetchone()
        if not fila:
            return False, "El usuario seleccionado ya no existe."

        nombre, rol = fila[0], (fila[1] or "admin")

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] <= 1:
            return False, "No se puede eliminar el único usuario registrado."

        if rol == "admin":
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' OR rol IS NULL")
            if cursor.fetchone()[0] <= 1:
                return False, "Debe quedar al menos un Administrador activo en el sistema."

        cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
        return True, f"Usuario '{nombre}' eliminado correctamente."
    except Exception as e:
        return False, f"Error al eliminar usuario: {e}"
    finally:
        conn.close()


def login_usuario(email_o_tel, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nombre, negocio, email, pin, rol
        FROM usuarios
        WHERE lower(email) = lower(?) AND password = ?
        """,
        (email_o_tel.strip(), password.strip()),
    )
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0],
        "nombre": r[1],
        "negocio": r[2],
        "email": r[3],
        "pin": r[4],
        "rol": r[5] or "admin",
    }


def login_pin(pin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nombre, negocio, email, pin, rol
        FROM usuarios
        WHERE pin = ?
        """,
        (str(pin).strip(),),
    )
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0],
        "nombre": r[1],
        "negocio": r[2],
        "email": r[3],
        "pin": r[4],
        "rol": r[5] or "admin",
    }


verificar_pin = login_pin
login_por_pin = login_pin
verificar_usuario = login_usuario
eliminar_usuario = delete_usuario


# -------------------------------------------------------------
# GESTIÓN DE PRODUCTOS E INVENTARIO
# -------------------------------------------------------------
def get_productos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nombre, sku, categoria, precio_costo, precio_venta, stock, imagen
        FROM productos
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "nombre": r[1],
            "sku": r[2] or "",
            "categoria": r[3] or "Granos y Cereales",
            "precio_costo": float(r[4] or 0.0),
            "precio_venta": float(r[5] or 0.0),
            "precio": float(r[5] or 0.0),
            "stock": int(r[6] or 0),
            "imagen": r[7] or "",
        }
        for r in rows
    ]


def insert_producto(nombre, sku, categoria, precio_costo, precio_venta, stock, imagen=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO productos (nombre, sku, categoria, precio_costo, precio_venta, stock, imagen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (nombre, sku, categoria, float(precio_costo), float(precio_venta), int(stock), imagen or ""),
    )
    conn.commit()
    prod_id = cursor.lastrowid
    conn.close()
    return prod_id


def update_producto(prod_id, nombre, categoria, precio_costo, precio_venta, stock, imagen=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE productos
        SET nombre = ?, categoria = ?, precio_costo = ?, precio_venta = ?, stock = ?, imagen = ?
        WHERE id = ?
        """,
        (nombre, categoria, float(precio_costo), float(precio_venta), int(stock), imagen or "", prod_id),
    )
    conn.commit()
    conn.close()


def delete_producto(prod_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()


def enviar_notificacion_sistema(titulo, mensaje):
    try:
        from plyer import notification
        notification.notify(
            title=titulo,
            message=mensaje,
            app_name="VentaFácil",
            timeout=6,
        )
    except Exception:
        pass


def _normalizar_items_carrito(cursor, carrito):
    items_normalizados = []
    if not carrito:
        return items_normalizados

    pares = []
    if isinstance(carrito, dict):
        for key, item in carrito.items():
            if isinstance(item, dict):
                pid = item.get("id", key)
                cant = int(item.get("cantidad", item.get("qty", 1)))
                pares.append((pid, cant, item))
            else:
                pares.append((key, int(item), {}))
    elif isinstance(carrito, list):
        for item in carrito:
            if isinstance(item, dict) and "id" in item:
                pid = item["id"]
                cant = int(item.get("cantidad", item.get("qty", 1)))
                pares.append((pid, cant, item))

    if not pares:
        return items_normalizados

    pids = list({p[0] for p in pares})
    placeholders = ",".join("?" for _ in pids)
    cursor.execute(
        f"SELECT id, nombre, sku, categoria, precio_costo, precio_venta FROM productos WHERE id IN ({placeholders})",
        tuple(pids),
    )
    mapa_prods = {r[0]: r[1:] for r in cursor.fetchall()}

    for pid, cant, raw in pares:
        prod_db = mapa_prods.get(pid)
        if prod_db:
            nombre = raw.get("nombre") or prod_db[0]
            sku = raw.get("sku") or prod_db[1] or ""
            categoria = raw.get("categoria") or prod_db[2] or "General"
            costo = float(raw.get("precio_costo") if raw.get("precio_costo") is not None else (prod_db[3] or 0.0))
            precio = float(
                raw.get("precio_venta")
                if raw.get("precio_venta") is not None
                else (raw.get("precio") if raw.get("precio") is not None else (prod_db[4] or 0.0))
            )
        else:
            nombre = raw.get("nombre", f"Producto #{pid}")
            sku = raw.get("sku", "")
            categoria = raw.get("categoria", "General")
            costo = float(raw.get("precio_costo", 0.0))
            precio = float(raw.get("precio_venta", raw.get("precio", 0.0)))

        subtotal = round(precio * cant, 2)
        items_normalizados.append(
            {
                "producto_id": pid,
                "sku": sku,
                "nombre_producto": nombre,
                "categoria": categoria,
                "cantidad": cant,
                "precio_costo": round(costo, 2),
                "precio_unitario": round(precio, 2),
                "subtotal": subtotal,
            }
        )

    return items_normalizados


def _guardar_detalle_venta(cursor, venta_id, items_norm):
    if not venta_id or not items_norm:
        return
    cursor.executemany(
        """
        INSERT INTO detalle_ventas (
            venta_id, producto_id, sku, nombre_producto, categoria,
            cantidad, precio_costo, precio_unitario, subtotal
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                venta_id,
                it.get("producto_id"),
                it.get("sku", ""),
                it.get("nombre_producto", "Producto"),
                it.get("categoria", "General"),
                int(it.get("cantidad", 1)),
                float(it.get("precio_costo", 0.0)),
                float(it.get("precio_unitario", 0.0)),
                float(it.get("subtotal", 0.0)),
            )
            for it in items_norm
        ],
    )


def descontar_stock_items(carrito):
    global ULTIMA_ALERTA_STOCK, _BUFFER_ITEMS_VENTA, _BUFFER_TIMESTAMP, _ULTIMA_VENTA_SIN_DETALLE
    if not carrito:
        return
    conn = get_connection()
    cursor = conn.cursor()

    items_norm = _normalizar_items_carrito(cursor, carrito)
    pids_afectados = []

    for it in items_norm:
        pid = it["producto_id"]
        cant = it["cantidad"]
        pids_afectados.append(pid)
        cursor.execute(
            "UPDATE productos SET stock = MAX(0, stock - ?) WHERE id = ?",
            (cant, pid),
        )

    ahora = datetime.datetime.now()
    if (
        _ULTIMA_VENTA_SIN_DETALLE is not None
        and _BUFFER_TIMESTAMP is not None
        and (ahora - _BUFFER_TIMESTAMP).total_seconds() <= 10
    ):
        cursor.execute("DELETE FROM detalle_ventas WHERE venta_id = ?", (_ULTIMA_VENTA_SIN_DETALLE,))
        _guardar_detalle_venta(cursor, _ULTIMA_VENTA_SIN_DETALLE, items_norm)
        _ULTIMA_VENTA_SIN_DETALLE = None
        _BUFFER_ITEMS_VENTA = []
    else:
        _BUFFER_ITEMS_VENTA = items_norm
        _BUFFER_TIMESTAMP = ahora

    conn.commit()

    if pids_afectados:
        placeholders = ",".join("?" for _ in pids_afectados)
        cursor.execute(
            f"SELECT nombre, stock FROM productos WHERE id IN ({placeholders}) AND stock <= 5 ORDER BY stock ASC",
            tuple(pids_afectados),
        )
        criticos = cursor.fetchall()
        if criticos:
            if len(criticos) == 1:
                nom, stk = criticos[0]
                estado_txt = "agotado (0 uds)" if stk == 0 else f"con stock bajo ({stk} uds)"
                aviso = f"'{nom}' quedó {estado_txt}."
            else:
                nombres = ", ".join(f"{r[0]} ({r[1]})" for r in criticos[:3])
                aviso = f"Stock bajo en: {nombres}"

            ULTIMA_ALERTA_STOCK = aviso
            enviar_notificacion_sistema("Alerta de Stock • VentaFácil", aviso)

    conn.close()


def _construir_alertas_desde_cursor(cursor, ventas_hoy_total):
    alertas = []
    cursor.execute(
        """
        SELECT id, nombre, categoria, stock
        FROM productos
        WHERE stock <= 5
        ORDER BY stock ASC, nombre ASC
        """
    )
    for pid, nombre, categoria, stock in cursor.fetchall():
        stk = int(stock or 0)
        cat = categoria or "General"
        if stk == 0:
            alertas.append(
                {
                    "tipo": "agotado",
                    "titulo": f"Agotado: {nombre}",
                    "detalle": f"{cat} • 0 unidades disponibles",
                    "icono": "alert-octagon",
                    "color": (0.85, 0.18, 0.18, 1),
                    "bg": (1.0, 0.94, 0.94, 1),
                    "destino": "inventory",
                }
            )
        else:
            alertas.append(
                {
                    "tipo": "stock_bajo",
                    "titulo": f"Stock bajo: {nombre}",
                    "detalle": f"Quedan {stk} ud(s) • {cat}",
                    "icono": "alert-outline",
                    "color": (0.90, 0.48, 0.10, 1),
                    "bg": (1.0, 0.97, 0.92, 1),
                    "destino": "inventory",
                }
            )

    ahora = datetime.datetime.now()
    if ahora.hour >= 20 and ventas_hoy_total > 0:
        cierres_dir = mobile_utils.get_subdir("cierres_caja")
        prefijo_hoy = f"Cierre_{ahora.strftime('%Y%m%d')}_"
        existe_cierre = (
            any(f.startswith(prefijo_hoy) for f in os.listdir(cierres_dir))
            if os.path.exists(cierres_dir)
            else False
        )
        if not existe_cierre:
            alertas.append(
                {
                    "tipo": "cierre",
                    "titulo": "Cierre de caja pendiente",
                    "detalle": "Realiza el arqueo de efectivo y transferencias del día",
                    "icono": "cash-lock",
                    "color": (0.13, 0.52, 0.89, 1),
                    "bg": (0.94, 0.97, 1.0, 1),
                    "destino": "closure",
                }
            )
    return alertas


def get_notificaciones_activas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha) = date('now', 'localtime')")
    val = cursor.fetchone()[0]
    ventas_hoy = float(val) if val is not None else 0.0
    alertas = _construir_alertas_desde_cursor(cursor, ventas_hoy)
    conn.close()
    return alertas


def get_dashboard_resumen():
    """Obtiene todas las métricas, alertas y últimas 15 ventas en UNA sola conexión SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0.0) FROM ventas WHERE date(fecha) = date('now', 'localtime')")
    tickets_hoy, ventas_hoy = cursor.fetchone()
    tickets_hoy = int(tickets_hoy or 0)
    ventas_hoy = float(ventas_hoy or 0.0)

    cursor.execute("SELECT COALESCE(SUM(monto), 0.0) FROM gastos WHERE date(fecha) = date('now', 'localtime')")
    gastos_hoy = float(cursor.fetchone()[0] or 0.0)

    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END) FROM productos")
    total_prods, stock_bajo = cursor.fetchone()
    total_prods = int(total_prods or 0)
    stock_bajo = int(stock_bajo or 0)

    alertas = _construir_alertas_desde_cursor(cursor, ventas_hoy)

    cursor.execute(
        """
        SELECT id, total, recibido, cambio, metodo_pago, comprobante, comprobante_img, fecha
        FROM ventas
        ORDER BY id DESC
        LIMIT 15
        """
    )
    ultimas_ventas = []
    for r in cursor.fetchall():
        fecha_obj = r[7]
        if isinstance(fecha_obj, str):
            try:
                fecha_obj = datetime.datetime.strptime(fecha_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                fecha_obj = datetime.datetime.now()
        ultimas_ventas.append(
            {
                "id": r[0],
                "total": float(r[1] or 0.0),
                "recibido": float(r[2] or 0.0),
                "cambio": float(r[3] or 0.0),
                "metodo_pago": r[4] or "Efectivo",
                "comprobante": r[5] or "",
                "comprobante_img": r[6] or "",
                "fecha": fecha_obj,
            }
        )

    conn.close()
    return {
        "ventas_hoy": ventas_hoy,
        "tickets_hoy": tickets_hoy,
        "gastos_hoy": gastos_hoy,
        "balance_neto": ventas_hoy - gastos_hoy,
        "total_prods": total_prods,
        "stock_bajo": stock_bajo,
        "alertas": alertas,
        "ultimas_ventas": ultimas_ventas,
    }


# -------------------------------------------------------------
# GESTIÓN DE VENTAS Y GASTOS
# -------------------------------------------------------------
def insert_venta(total, recibido, cambio, metodo_pago="Efectivo", comprobante="", comprobante_img="", items=None):
    global _BUFFER_ITEMS_VENTA, _BUFFER_TIMESTAMP, _ULTIMA_VENTA_SIN_DETALLE
    conn = get_connection()
    cursor = conn.cursor()
    ahora = datetime.datetime.now()
    fecha_actual = ahora.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO ventas (total, recibido, cambio, metodo_pago, comprobante, comprobante_img, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            float(total),
            float(recibido),
            float(cambio),
            metodo_pago,
            comprobante or "",
            comprobante_img or "",
            fecha_actual,
        ),
    )
    venta_id = cursor.lastrowid

    if items:
        items_norm = _normalizar_items_carrito(cursor, items)
        _guardar_detalle_venta(cursor, venta_id, items_norm)
        _ULTIMA_VENTA_SIN_DETALLE = None
        _BUFFER_ITEMS_VENTA = []
    elif (
        _BUFFER_ITEMS_VENTA
        and _BUFFER_TIMESTAMP is not None
        and (ahora - _BUFFER_TIMESTAMP).total_seconds() <= 10
    ):
        _guardar_detalle_venta(cursor, venta_id, _BUFFER_ITEMS_VENTA)
        _BUFFER_ITEMS_VENTA = []
        _ULTIMA_VENTA_SIN_DETALLE = None
    else:
        _ULTIMA_VENTA_SIN_DETALLE = venta_id
        _BUFFER_TIMESTAMP = ahora

    conn.commit()
    conn.close()
    return venta_id


def get_detalle_venta(venta_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            d.id,
            d.producto_id,
            COALESCE(NULLIF(d.sku, ''), p.sku, ''),
            COALESCE(NULLIF(d.nombre_producto, ''), p.nombre, 'Producto'),
            COALESCE(NULLIF(d.categoria, ''), p.categoria, 'General'),
            d.cantidad,
            CASE WHEN d.precio_costo > 0 THEN d.precio_costo ELSE COALESCE(p.precio_costo, 0.0) END,
            CASE WHEN d.precio_unitario > 0 THEN d.precio_unitario ELSE COALESCE(p.precio_venta, 0.0) END,
            d.subtotal
        FROM detalle_ventas d
        LEFT JOIN productos p ON d.producto_id = p.id
        WHERE d.venta_id = ?
        ORDER BY d.id ASC
        """,
        (venta_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "producto_id": r[1],
            "sku": r[2] or "",
            "nombre_producto": r[3] or "Producto",
            "categoria": r[4] or "General",
            "cantidad": int(r[5] or 1),
            "precio_costo": float(r[6] or 0.0),
            "precio_unitario": float(r[7] or 0.0),
            "subtotal": float(r[8] or 0.0),
        }
        for r in rows
    ]


def get_ventas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, total, recibido, cambio, metodo_pago, comprobante, comprobante_img, fecha
        FROM ventas
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    resultado = []
    for r in rows:
        fecha_obj = r[7]
        if isinstance(fecha_obj, str):
            try:
                fecha_obj = datetime.datetime.strptime(fecha_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                fecha_obj = datetime.datetime.now()

        resultado.append(
            {
                "id": r[0],
                "total": float(r[1] or 0.0),
                "recibido": float(r[2] or 0.0),
                "cambio": float(r[3] or 0.0),
                "metodo_pago": r[4] or "Efectivo",
                "comprobante": r[5] or "",
                "comprobante_img": r[6] or "",
                "fecha": fecha_obj,
            }
        )
    return resultado


def get_ventas_hoy_total():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha) = date('now', 'localtime')")
    val = cursor.fetchone()[0]
    conn.close()
    return float(val) if val is not None else 0.0


def insert_gasto(descripcion, monto=None, categoria="General", metodo_pago="Efectivo", *extra):
    if isinstance(monto, str):
        cat_real = monto
        monto_real = float(categoria) if not isinstance(categoria, str) else 0.0
        metodo_real = extra[0] if extra else metodo_pago
        categoria = cat_real
        monto = monto_real
        metodo_pago = metodo_real
    else:
        monto = float(monto or 0.0)

    conn = get_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO gastos (descripcion, categoria, monto, metodo_pago, fecha)
        VALUES (?, ?, ?, ?, ?)
        """,
        (descripcion, categoria or "General", monto, metodo_pago or "Efectivo", fecha_actual),
    )
    conn.commit()
    gasto_id = cursor.lastrowid
    conn.close()
    return gasto_id


def get_gastos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, descripcion, categoria, monto, metodo_pago, fecha
        FROM gastos
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    resultado = []
    for r in rows:
        fecha_obj = r[5]
        if isinstance(fecha_obj, str):
            try:
                fecha_obj = datetime.datetime.strptime(fecha_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                fecha_obj = datetime.datetime.now()

        resultado.append(
            {
                "id": r[0],
                "descripcion": r[1],
                "categoria": r[2] or "General",
                "monto": float(r[3] or 0.0),
                "metodo_pago": r[4] or "Efectivo",
                "fecha": fecha_obj,
            }
        )
    return resultado


def get_gastos_hoy():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, descripcion, categoria, monto, metodo_pago, fecha
        FROM gastos
        WHERE date(fecha) = date('now', 'localtime')
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "descripcion": r[1],
            "categoria": r[2] or "General",
            "monto": float(r[3] or 0.0),
            "metodo_pago": r[4] or "Efectivo",
            "fecha": r[5],
        }
        for r in rows
    ]


def get_gastos_hoy_total():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(monto) FROM gastos WHERE date(fecha) = date('now', 'localtime')")
    val = cursor.fetchone()[0]
    conn.close()
    return float(val) if val is not None else 0.0


def delete_gasto(gasto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()


# -------------------------------------------------------------
# MÓDULO DE REPORTES (SIN CONSULTAS N+1)
# -------------------------------------------------------------
def _filtro_fecha_sql(periodo):
    if periodo == "semanal":
        return "date(fecha) >= date('now', 'localtime', 'weekday 0', '-6 days')"
    elif periodo == "mensual":
        return "strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now', 'localtime')"
    return "date(fecha) = date('now', 'localtime')"


def get_ventas_semanal_total():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT SUM(total) FROM ventas WHERE {_filtro_fecha_sql('semanal')}")
    val = cursor.fetchone()[0]
    conn.close()
    return float(val) if val is not None else 0.0


def get_ventas_mensual_total():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT SUM(total) FROM ventas WHERE {_filtro_fecha_sql('mensual')}")
    val = cursor.fetchone()[0]
    conn.close()
    return float(val) if val is not None else 0.0


def get_reporte_periodo(periodo="diario"):
    conn = get_connection()
    cursor = conn.cursor()
    condicion = _filtro_fecha_sql(periodo)

    cursor.execute(
        f"""
        SELECT id, total, fecha, metodo_pago, comprobante, comprobante_img, recibido, cambio
        FROM ventas
        WHERE {condicion}
        ORDER BY id DESC
        """
    )
    rows_ventas = cursor.fetchall()

    cursor.execute(
        f"""
        SELECT id, descripcion, categoria, monto, metodo_pago, fecha
        FROM gastos
        WHERE {condicion}
        ORDER BY id DESC
        """
    )
    rows_gastos = cursor.fetchall()

    # Traer TODOS los detalles de los tickets del periodo en 1 sola consulta
    detalles_por_venta = {}
    venta_ids = [r[0] for r in rows_ventas]
    if venta_ids:
        placeholders = ",".join("?" for _ in venta_ids)
        cursor.execute(
            f"""
            SELECT
                d.venta_id,
                COALESCE(NULLIF(d.sku, ''), p.sku, '-'),
                COALESCE(NULLIF(d.nombre_producto, ''), p.nombre, 'Producto'),
                COALESCE(NULLIF(d.categoria, ''), p.categoria, 'General'),
                d.cantidad,
                CASE WHEN d.precio_costo > 0 THEN d.precio_costo ELSE COALESCE(p.precio_costo, 0.0) END,
                CASE WHEN d.precio_unitario > 0 THEN d.precio_unitario ELSE COALESCE(p.precio_venta, 0.0) END,
                CASE WHEN d.subtotal > 0 THEN d.subtotal ELSE (d.cantidad * COALESCE(p.precio_venta, 0.0)) END
            FROM detalle_ventas d
            LEFT JOIN productos p ON d.producto_id = p.id
            WHERE d.venta_id IN ({placeholders})
            ORDER BY d.id ASC
            """,
            tuple(venta_ids),
        )
        for rd in cursor.fetchall():
            detalles_por_venta.setdefault(rd[0], []).append(rd[1:])

    catalogo_cache = None
    hubo_reconstruccion = False

    ventas_lista = []
    filas_productos = []
    total_ventas = 0.0
    total_efectivo = 0.0
    total_transferencia = 0.0
    costo_mercaderia_total = 0.0

    for r in rows_ventas:
        vid = r[0]
        monto = float(r[1] or 0.0)
        metodo = r[3] or "Efectivo"
        comp = r[4] or ""
        comp_img = r[5] or ""
        recibido = float(r[6] or 0.0)
        cambio = float(r[7] or 0.0)

        total_ventas += monto
        if "transf" in metodo.lower():
            total_transferencia += monto
        else:
            total_efectivo += monto

        fecha_obj = r[2]
        if isinstance(fecha_obj, str):
            try:
                fecha_obj = datetime.datetime.strptime(fecha_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                fecha_obj = datetime.datetime.now()

        detalles = detalles_por_venta.get(vid, [])

        if not detalles and monto > 0:
            if catalogo_cache is None:
                cursor.execute(
                    "SELECT id, nombre, sku, categoria, precio_costo, precio_venta FROM productos WHERE precio_venta > 0 ORDER BY precio_venta DESC"
                )
                catalogo_cache = [
                    {
                        "id": pr[0],
                        "nombre": pr[1],
                        "sku": pr[2] or "",
                        "categoria": pr[3] or "General",
                        "precio_costo": float(pr[4] or 0.0),
                        "precio_venta": float(pr[5] or 0.0),
                        "centavos": int(round(float(pr[5]) * 100)),
                    }
                    for pr in cursor.fetchall()
                    if int(round(float(pr[5] or 0) * 100)) > 0
                ]
            if _reconstruir_detalle_ticket_historico(cursor, vid, monto, catalogo_cache):
                hubo_reconstruccion = True
                cursor.execute(
                    """
                    SELECT
                        COALESCE(NULLIF(d.sku, ''), p.sku, '-'),
                        COALESCE(NULLIF(d.nombre_producto, ''), p.nombre, 'Producto'),
                        COALESCE(NULLIF(d.categoria, ''), p.categoria, 'General'),
                        d.cantidad,
                        CASE WHEN d.precio_costo > 0 THEN d.precio_costo ELSE COALESCE(p.precio_costo, 0.0) END,
                        CASE WHEN d.precio_unitario > 0 THEN d.precio_unitario ELSE COALESCE(p.precio_venta, 0.0) END,
                        CASE WHEN d.subtotal > 0 THEN d.subtotal ELSE (d.cantidad * COALESCE(p.precio_venta, 0.0)) END
                    FROM detalle_ventas d
                    LEFT JOIN productos p ON d.producto_id = p.id
                    WHERE d.venta_id = ?
                    ORDER BY d.id ASC
                    """,
                    (vid,),
                )
                detalles = cursor.fetchall()

        items_ticket = []
        if detalles:
            for d in detalles:
                sku_d = d[0] or "-"
                nom_d = d[1] or "Producto"
                cat_d = d[2] or "General"
                cant_d = int(d[3] or 1)
                costo_u = float(d[4] or 0.0)
                precio_u = float(d[5] or 0.0)
                sub_d = float(d[6] or 0.0)
                costo_tot = round(costo_u * cant_d, 2)
                ganancia_d = round(sub_d - costo_tot, 2)
                costo_mercaderia_total += costo_tot

                item_dict = {
                    "sku": sku_d,
                    "nombre_producto": nom_d,
                    "categoria": cat_d,
                    "cantidad": cant_d,
                    "precio_costo": costo_u,
                    "precio_unitario": precio_u,
                    "subtotal": sub_d,
                    "costo_total": costo_tot,
                    "ganancia": ganancia_d,
                }
                items_ticket.append(item_dict)
                filas_productos.append(
                    {
                        "ticket_id": vid,
                        "fecha": fecha_obj.strftime("%d/%m/%Y"),
                        "hora": fecha_obj.strftime("%I:%M %p"),
                        "sku": sku_d,
                        "producto": nom_d,
                        "categoria": cat_d,
                        "cantidad": cant_d,
                        "precio_costo": costo_u,
                        "precio_unitario": precio_u,
                        "subtotal": sub_d,
                        "costo_total": costo_tot,
                        "ganancia": ganancia_d,
                        "metodo_pago": metodo,
                        "comprobante": comp or "-",
                    }
                )
        else:
            filas_productos.append(
                {
                    "ticket_id": vid,
                    "fecha": fecha_obj.strftime("%d/%m/%Y"),
                    "hora": fecha_obj.strftime("%I:%M %p"),
                    "sku": "-",
                    "producto": f"Venta en mostrador (Ticket #{vid:04d})",
                    "categoria": "General",
                    "cantidad": 1,
                    "precio_costo": 0.0,
                    "precio_unitario": monto,
                    "subtotal": monto,
                    "costo_total": 0.0,
                    "ganancia": monto,
                    "metodo_pago": metodo,
                    "comprobante": comp or "-",
                }
            )

        ventas_lista.append(
            {
                "id": vid,
                "total": monto,
                "recibido": recibido,
                "cambio": cambio,
                "fecha": fecha_obj,
                "metodo_pago": metodo,
                "comprobante": comp,
                "comprobante_img": comp_img,
                "items": items_ticket,
            }
        )

    gastos_lista = []
    total_gastos = 0.0
    for rg in rows_gastos:
        m_gasto = float(rg[3] or 0.0)
        total_gastos += m_gasto
        f_g = rg[5]
        if isinstance(f_g, str):
            try:
                f_g = datetime.datetime.strptime(f_g, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                f_g = datetime.datetime.now()
        gastos_lista.append(
            {
                "id": rg[0],
                "descripcion": rg[1],
                "categoria": rg[2] or "General",
                "monto": m_gasto,
                "metodo_pago": rg[4] or "Efectivo",
                "fecha": f_g,
            }
        )

    if hubo_reconstruccion:
        conn.commit()
    conn.close()

    return {
        "periodo": periodo,
        "total_ventas": round(total_ventas, 2),
        "cantidad_ventas": len(ventas_lista),
        "total_efectivo": round(total_efectivo, 2),
        "total_transferencia": round(total_transferencia, 2),
        "total_gastos": round(total_gastos, 2),
        "balance_neto": round(total_ventas - total_gastos, 2),
        "costo_mercaderia": round(costo_mercaderia_total, 2),
        "utilidad_bruta": round(total_ventas - costo_mercaderia_total, 2),
        "ventas": ventas_lista,
        "filas_productos": filas_productos,
        "gastos": gastos_lista,
    }