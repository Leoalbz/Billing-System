from conexion import conectar
import datetime

# -------------------------
# Productos
# -------------------------

def agregar_producto(codigo, nombre, precio, stock):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO productos (codigo, nombre, precio, stock)
        VALUES (?, ?, ?, ?)
    """, (codigo, nombre, float(precio), int(stock)))
    conn.commit()
    conn.close()

def buscar_producto(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def listar_productos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def actualizar_stock(codigo, cantidad):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False

    nuevo_stock = row["stock"] + int(cantidad)
    if nuevo_stock < 0:
        nuevo_stock = 0

    cur.execute(
        "UPDATE productos SET stock = ? WHERE codigo = ?",
        (nuevo_stock, codigo)
    )

    conn.commit()
    conn.close()
    return True

def eliminar_producto(codigo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()

# -------------------------
# Ventas
# -------------------------

def registrar_venta(monto_total):
    conn = conectar()
    cur = conn.cursor()
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO ventas (monto_total, fecha)
        VALUES (?, ?)
    """, (float(monto_total), fecha))

    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def obtener_ventas_del_dia():
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    inicio = hoy + " 00:00:00"
    fin = hoy + " 23:59:59"

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM ventas
        WHERE fecha BETWEEN ? AND ?
    """, (inicio, fin))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]

def borrar_ventas_del_dia():
    hoy = datetime.date.today().strftime("%Y-%m-%d")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM ventas
        WHERE date(fecha) = ?
    """, (hoy,))
    conn.commit()
    conn.close()