import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Toplevel
import random
from barcode import Code128
from barcode.writer import ImageWriter
from datetime import datetime
import conexion as con
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Buscar producto por código
def buscar_producto(codigo):
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
    producto = cursor.fetchone()
    conn.close()
    return producto

# Agregar producto a la factura
def agregar_producto_facturar(event=None):
    codigo = codigo_entry.get()
    producto = buscar_producto(codigo)
    if producto:
        nombre, precio = producto[1], producto[2]
        factura_tree.insert('', 'end', values=(codigo, nombre, f"${precio:.2f}"))
        calcular_total()
        codigo_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Producto no encontrado")

# Calcular el total de la factura
def calcular_total():
    total = 0.0
    for item in factura_tree.get_children():
        total += float(factura_tree.item(item, 'values')[2][1:])
    total_label.config(text=f"Total: ${total:.2f}")

# Generar la factura
def generar_factura():
    items = factura_tree.get_children()
    if not items:
        messagebox.showwarning("Advertencia", "La factura está vacía")
        return
    factura = "Factura:\n\n"
    for item in items:
        valores = factura_tree.item(item, 'values')
        factura += f"{valores[1]} - {valores[2]}\n"
    factura += f"\nTotal: {total_label.cget('text')}"
    messagebox.showinfo("Factura Generada", factura)

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Sistema de Facturación")

# Campo de entrada del código
frame_codigo = tk.Frame(root)
frame_codigo.pack(pady=10)
tk.Label(frame_codigo, text="Código de Barras:").pack(side=tk.LEFT, padx=5)
codigo_entry = tk.Entry(frame_codigo, width=20)
codigo_entry.pack(side=tk.LEFT)
codigo_entry.bind("<Return>", agregar_producto_facturar)

# Tabla de factura
factura_frame = tk.Frame(root)
factura_frame.pack(pady=10)
columns = ("codigo", "nombre", "precio")
factura_tree = ttk.Treeview(factura_frame, columns=columns, show="headings", height=10)
factura_tree.heading("codigo", text="Código")
factura_tree.heading("nombre", text="Nombre")
factura_tree.heading("precio", text="Precio")
factura_tree.pack(side=tk.LEFT)

# Barra de desplazamiento
scrollbar = ttk.Scrollbar(factura_frame, orient="vertical", command=factura_tree.yview)
factura_tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Total y botón de generar factura
total_label = tk.Label(root, text="Total: $0.00", font=("Arial", 14))
total_label.pack(pady=5)

tk.Button(root, text="Generar Factura", command=generar_factura).pack(pady=10)



# Registrar venta en la base de datos
def registrar_venta(codigo, cantidad):
    conn = con.conectar_mysql()
    cursor = conn.cursor()

    # Verificar stock disponible
    cursor.execute("SELECT stock FROM productos WHERE codigo = %s", (codigo,))
    stock_disponible = cursor.fetchone()
    if stock_disponible and stock_disponible[0] >= cantidad:
        # Registrar la venta
        cursor.execute(
            "INSERT INTO ventas (codigo_producto, cantidad) VALUES (%s, %s)",
            (codigo, cantidad)
        )
        # Actualizar el stock
        cursor.execute(
            "UPDATE productos SET stock = stock - %s WHERE codigo = %s",
            (cantidad, codigo)
        )
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False

# Agregar producto a la factura y registrar venta
def agregar_producto(event=None):
    codigo = codigo_entry.get()
    producto = buscar_producto(codigo)
    if producto:
        nombre, precio, stock = producto[1], producto[2], producto[3]
        if stock > 0:
            cantidad = 1  # Aquí puedes implementar un campo para seleccionar cantidad
            if registrar_venta(codigo, cantidad):
                factura_tree.insert('', 'end', values=(codigo, nombre, f"${precio:.2f}", cantidad))
                calcular_total()
                codigo_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "No hay suficiente stock para este producto.")
        else:
            messagebox.showerror("Error", "Este producto está agotado.")
    else:
        messagebox.showerror("Error", "Producto no encontrado")

# Calcular el total de ventas del día
def calcular_total_ventas():
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT SUM(p.precio * v.cantidad) AS total_ventas
        FROM ventas v
        JOIN productos p ON v.codigo_producto = p.codigo
        WHERE DATE(v.fecha) = %s
    """, (hoy,))
    total_ventas = cursor.fetchone()[0] or 0.0
    conn.close()
    messagebox.showinfo("Total de Ventas", f"El total de ventas del día es: ${total_ventas:.2f}")

# Mostrar productos vendidos y stock disponible
def mostrar_productos_vendidos():
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT p.nombre, SUM(v.cantidad) AS cantidad_vendida, p.stock
        FROM ventas v
        JOIN productos p ON v.codigo_producto = p.codigo
        WHERE DATE(v.fecha) = %s
        GROUP BY p.nombre
    """, (hoy,))
    productos = cursor.fetchall()
    conn.close()

    if productos:
        info = "Productos Vendidos Hoy:\n\n"
        for nombre, cantidad, stock in productos:
            info += f"{nombre}: Vendidos {cantidad}, Stock Restante {stock}\n"
        messagebox.showinfo("Productos Vendidos", info)
    else:
        messagebox.showinfo("Productos Vendidos", "No se han registrado ventas hoy.")

# Botones adicionales para mostrar estadísticas
tk.Button(root, text="Total Ventas del Día", command=calcular_total_ventas).pack(pady=5)
tk.Button(root, text="Productos Vendidos y Stock", command=mostrar_productos_vendidos).pack(pady=5)

# Umprimir el código y el nombre del producto
def imprimir_producto():
    try:
        # Obtener el producto seleccionado
        selected_item = productos_tree.selection()[0]
        values = productos_tree.item(selected_item, 'values')
        codigo, nombre = values[0], values[1]

        # Generar el archivo PDF con el nombre y el código
        archivo_pdf = f"producto_{codigo}.pdf"
        c = canvas.Canvas(archivo_pdf, pagesize=letter)
        c.setFont("Helvetica", 12)

        # Escribir los datos del producto en el PDF
        c.drawString(100, 750, "Producto Seleccionado:")
        c.drawString(100, 730, f"Código: {codigo}")
        c.drawString(100, 710, f"Nombre: {nombre}")

        # Guardar el PDF
        c.save()

        messagebox.showinfo("Éxito", f"Se ha generado el archivo '{archivo_pdf}'.")
    except IndexError:
        messagebox.showerror("Error", "No se ha seleccionado ningún producto.")

# Mostrar la ventana de selección de producto
def ventana_seleccionar_producto():
    global productos_tree

    # Crear una nueva ventana
    ventana_productos = Toplevel(root)
    ventana_productos.title("Seleccionar Producto")

    # Frame para la tabla
    frame_tabla = tk.Frame(ventana_productos)
    frame_tabla.pack(pady=10)

    # Configuración de la tabla
    columnas = ("codigo", "nombre", "precio", "stock")
    productos_tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)
    productos_tree.heading("codigo", text="Código")
    productos_tree.heading("nombre", text="Nombre")
    productos_tree.heading("precio", text="Precio")
    productos_tree.heading("stock", text="Stock")
    productos_tree.pack(side=tk.LEFT)

    # Barra de desplazamiento
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=productos_tree.yview)
    productos_tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Cargar los productos desde la base de datos
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre, precio, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()

    # Insertar los productos en la tabla
    for producto in productos:
        productos_tree.insert("", "end", values=producto)

    # Botón para imprimir el producto seleccionado
    tk.Button(ventana_productos, text="Imprimir Producto", command=imprimir_producto).pack(pady=10)

# Botón en la ventana principal para abrir la ventana de selección de producto
tk.Button(root, text="Seleccionar Producto e Imprimir", command=ventana_seleccionar_producto).pack(pady=5)


def generar_reporte_pdf():
    # Conectar a la base de datos y obtener los datos
    conn = con.conectar_mysql()
    cursor = conn.cursor()

    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT p.nombre, SUM(v.cantidad) AS cantidad_vendida, p.stock
        FROM ventas v
        JOIN productos p ON v.codigo_producto = p.codigo
        WHERE DATE(v.fecha) = %s
        GROUP BY p.nombre
    """, (hoy,))
    productos = cursor.fetchall()

    # Generar el archivo PDF
    archivo_pdf = "reporte_ventas.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Título
    c.drawString(100, 750, "Reporte de Ventas del Día")
    c.drawString(100, 730, f"Fecha: {hoy}")

    # Encabezados
    y = 700
    c.drawString(100, y, "Producto")
    c.drawString(300, y, "Vendidos")
    c.drawString(400, y, "Stock Restante")
    y -= 20

    # Productos vendidos
    for nombre, cantidad, stock in productos:
        c.drawString(100, y, nombre)
        c.drawString(300, y, str(cantidad))
        c.drawString(400, y, str(stock))
        y -= 20

    # Guardar el PDF
    c.save()
    conn.close()
    messagebox.showinfo("Reporte Generado", f"El reporte se ha guardado como '{archivo_pdf}'.")
    return archivo_pdf



def enviar_reporte_por_correo():
    # Configuración del correo
    remitente = "tu_correo@gmail.com"  # Cambia esto
    contraseña = "tu_contraseña"      # Cambia esto
    destinatario = "destinatario@gmail.com"  # Cambia esto

    asunto = "Reporte de Ventas del Día"
    cuerpo = "Adjunto encontrarás el reporte de ventas del día."

    # Generar el reporte en PDF
    archivo_pdf = generar_reporte_pdf()

    # Crear el mensaje de correo
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    # Adjuntar el cuerpo del mensaje
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar el archivo PDF
    with open(archivo_pdf, 'rb') as adjunto:
        parte = MIMEBase('application', 'octet-stream')
        parte.set_payload(adjunto.read())
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f"attachment; filename={archivo_pdf}")
        mensaje.attach(parte)

    # Enviar el correo
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)  # Cambia el servidor según el proveedor
        servidor.starttls()
        servidor.login(remitente, contraseña)
        servidor.sendmail(remitente, destinatario, mensaje.as_string())
        servidor.quit()
        messagebox.showinfo("Correo Enviado", "El reporte se ha enviado correctamente por correo.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo enviar el correo: {e}")

tk.Button(root, text="Enviar Reporte por Correo", command=enviar_reporte_por_correo).pack(pady=5)

# Generar un código único
def generar_codigo_unico():
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    while True:
        codigo = f"P{random.randint(10000, 99999)}"
        cursor.execute("SELECT COUNT(*) FROM productos WHERE codigo = %s", (codigo,))
        if cursor.fetchone()[0] == 0:
            break
    conn.close()
    return codigo

# Generar el código de barras
def generar_codigo_barras(codigo, nombre):
    codigo_barras = Code128(codigo, writer=ImageWriter(), add_checksum=False)
    filename = f"codigo_{codigo}.png"
    codigo_barras.save(filename)
    print(f"Código de barras generado: {filename}")

# Agregar stock
def agregar_stock():
    nombre = entry_nombre.get()
    cantidad = entry_cantidad.get()
    precio = entry_precio.get()

    if not nombre or not cantidad.isdigit() or not precio.replace(".", "").isdigit():
        messagebox.showerror("Error", "Todos los campos deben ser válidos.")
        return

    codigo = generar_codigo_unico()
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productos (codigo, nombre, stock, precio) VALUES (%s, %s, %s, %s)",
        (codigo, nombre, int(cantidad), float(precio))
    )
    conn.commit()
    conn.close()

    generar_codigo_barras(codigo, nombre)
    messagebox.showinfo("Éxito", f"Producto agregado con código: {codigo}")
    ventana_agregar.destroy()

# Ventana para agregar stock
def ventana_agregar_stock():
    global ventana_agregar, entry_nombre, entry_cantidad, entry_precio

    ventana_agregar = Toplevel(root)
    ventana_agregar.title("Agregar Stock")

    tk.Label(ventana_agregar, text="Nombre del Producto:").pack(pady=5)
    entry_nombre = tk.Entry(ventana_agregar)
    entry_nombre.pack(pady=5)

    tk.Label(ventana_agregar, text="Cantidad:").pack(pady=5)
    entry_cantidad = tk.Entry(ventana_agregar)
    entry_cantidad.pack(pady=5)

    tk.Label(ventana_agregar, text="Precio:").pack(pady=5)
    entry_precio = tk.Entry(ventana_agregar)
    entry_precio.pack(pady=5)

    tk.Button(ventana_agregar, text="Cargar", command=agregar_stock).pack(pady=10)

# Botón para abrir la ventana "Agregar Stock"
tk.Button(root, text="Agregar Stock", command=ventana_agregar_stock).pack(pady=5)
# Eliminar un producto de la base de datos
def eliminar_producto():
    try:
        # Obtener el producto seleccionado
        selected_item = productos_tree.selection()[0]
        values = productos_tree.item(selected_item, 'values')
        codigo, nombre = values[0], values[1]

        # Confirmar eliminación
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar el producto '{nombre}' con código '{codigo}'?"
        )
        if not confirmacion:
            return

        # Eliminar producto de la base de datos
        conn = con.conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE codigo = %s", (codigo,))
        conn.commit()
        conn.close()

        # Eliminar el producto de la tabla
        productos_tree.delete(selected_item)

        messagebox.showinfo("Éxito", f"El producto '{nombre}' ha sido eliminado correctamente.")
    except IndexError:
        messagebox.showerror("Error", "No se ha seleccionado ningún producto.")

# Ventana de eliminación de productos
def ventana_eliminar_producto():
    global productos_tree

    # Nueva ventana
    ventana_eliminar = Toplevel(root)
    ventana_eliminar.title("Eliminar Producto")

    # Frame para la tabla
    frame_tabla = tk.Frame(ventana_eliminar)
    frame_tabla.pack(pady=10)

    # Configuración de tabla
    columnas = ("codigo", "nombre", "precio", "stock")
    productos_tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)
    productos_tree.heading("codigo", text="Código")
    productos_tree.heading("nombre", text="Nombre")
    productos_tree.heading("precio", text="Precio")
    productos_tree.heading("stock", text="Stock")
    productos_tree.pack(side=tk.LEFT)

    # Barra de desplazamiento
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=productos_tree.yview)
    productos_tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Cargar productos desde database
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre, precio, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()

    # Insertar productos en la tabla
    for producto in productos:
        productos_tree.insert("", "end", values=producto)

    # Botón para eliminar
    tk.Button(ventana_eliminar, text="Eliminar Producto", command=eliminar_producto).pack(pady=10)

# Botón en la ventana principal para abrir la ventana de eliminación de productos
tk.Button(root, text="Eliminar Stock", command=ventana_eliminar_producto).pack(pady=5)
# Cargar datos del producto
def cargar_datos_producto(codigo, entry_nombre, entry_precio, entry_stock):
    conn = con.conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, precio, stock FROM productos WHERE codigo = %s", (codigo,))
    producto = cursor.fetchone()
    conn.close()

    if producto:
        entry_nombre.insert(0, producto[0])
        entry_precio.insert(0, producto[1])
        entry_stock.insert(0, producto[2])
    else:
        messagebox.showerror("Error", f"No se encontró el producto con código '{codigo}'.")

# Actualizar producto en la base de datos
def actualizar_producto(codigo, nombre, precio, stock):
    try:
        conn = con.conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos
            SET nombre = %s, precio = %s, stock = %s
            WHERE codigo = %s
        """, (nombre, precio, stock, codigo))
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", f"El producto con código '{codigo}' ha sido actualizado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un problema al actualizar el producto: {e}")

# Actualizar el stock
def ventana_actualizar_stock():
    # Nueva ventana
    ventana_actualizar = Toplevel(root)
    ventana_actualizar.title("Actualizar Producto")

    # Código del producto
    frame_codigo = tk.Frame(ventana_actualizar)
    frame_codigo.pack(pady=10)
    tk.Label(frame_codigo, text="Código del Producto:").pack(side=tk.LEFT, padx=5)
    entry_codigo = tk.Entry(frame_codigo, width=20)
    entry_codigo.pack(side=tk.LEFT)

    # Datos del producto
    frame_formulario = tk.Frame(ventana_actualizar)
    frame_formulario.pack(pady=10)
    tk.Label(frame_formulario, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
    entry_nombre = tk.Entry(frame_formulario, width=30)
    entry_nombre.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_formulario, text="Precio:").grid(row=1, column=0, padx=5, pady=5)
    entry_precio = tk.Entry(frame_formulario, width=20)
    entry_precio.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(frame_formulario, text="Stock:").grid(row=2, column=0, padx=5, pady=5)
    entry_stock = tk.Entry(frame_formulario, width=20)
    entry_stock.grid(row=2, column=1, padx=5, pady=5)

    # Cargar datos del producto
    def cargar_datos():
        codigo = entry_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Error", "Debes ingresar un código de producto.")
            return
        cargar_datos_producto(codigo, entry_nombre, entry_precio, entry_stock)
    #Guardar datos
    def guardar_datos():
        codigo = entry_codigo.get().strip()
        nombre = entry_nombre.get().strip()
        precio = entry_precio.get().strip()
        stock = entry_stock.get().strip()

        if not codigo or not nombre or not precio or not stock:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número decimal y el stock debe ser un número entero.")
            return

        actualizar_producto(codigo, nombre, precio, stock)

    # Botones para cargar y guardar
    tk.Button(ventana_actualizar, text="Cargar Datos", command=cargar_datos).pack(pady=10)
    tk.Button(ventana_actualizar, text="Guardar Cambios", command=guardar_datos).pack(pady=10)

# Botón en la ventana principal para abrir la ventana de actualización de productos
tk.Button(root, text="Actualizar Stock", command=ventana_actualizar_stock).pack(pady=5)

root.mainloop()