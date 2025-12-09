import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import init_db
from database import (
    borrar_ventas_del_dia,
    buscar_producto,
    obtener_ventas_del_dia,
    registrar_venta,
    actualizar_stock,
    eliminar_producto
)
from pdf_email import generar_pdf, enviar_email


# -----------------------------
#   Función: Agregar producto a la factura
# -----------------------------
def agregar_producto_facturar(codigo_entry, factura_tree, total_label):
    codigo = codigo_entry.get().strip()
    if not codigo:
        return

    producto = buscar_producto(codigo)
    if not producto:
        messagebox.showerror("Error", "Producto no encontrado")
        return

    
    nombre = producto["nombre"]
    monto = float(producto["precio"])
    stock = int(producto["stock"])

    if stock <= 0:
        messagebox.showerror("Error", "Sin stock disponible")
        return

    cantidad = 1

    factura_tree.insert('', 'end', values=(codigo, nombre, f"${monto:.2f}", cantidad))

    calcular_total(factura_tree, total_label)
    codigo_entry.delete(0, tk.END)


# -----------------------------
#   Ventana: Agregar producto al stock
# -----------------------------
def agregar_producto_window():
    win = tk.Toplevel()
    win.title("Agregar Producto al Stock")

    tk.Label(win, text="Código:").grid(row=0, column=0, padx=10, pady=5)
    codigo_entry = tk.Entry(win)
    codigo_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(win, text="Nombre:").grid(row=1, column=0, padx=10, pady=5)
    nombre_entry = tk.Entry(win)
    nombre_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(win, text="Monto:").grid(row=2, column=0, padx=10, pady=5)
    monto_entry = tk.Entry(win)
    monto_entry.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(win, text="Stock inicial:").grid(row=3, column=0, padx=10, pady=5)
    stock_entry = tk.Entry(win)
    stock_entry.grid(row=3, column=1, padx=10, pady=5)

    def confirmar():
        codigo = codigo_entry.get().strip()
        nombre = nombre_entry.get().strip()
        monto = monto_entry.get().strip()
        stock = stock_entry.get().strip()

        if not codigo or not nombre or not monto or not stock:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        try:
            monto = float(monto)
            stock = int(stock)
        except:
            messagebox.showerror("Error", "Monto o stock inválidos.")
            return

        # IMPORTACIÓN CORRECTA PARA SQLite
        from database import agregar_producto as agregar_producto_db
        agregar_producto_db(codigo, nombre, monto, stock)

        messagebox.showinfo("Éxito", "Producto guardado correctamente", parent=root)
        win.destroy()

    tk.Button(win, text="Guardar", command=confirmar).grid(row=4, column=0, columnspan=2, pady=10)


# -----------------------------
#   Calcular total
# -----------------------------
def calcular_total(factura_tree, total_label):
    total = 0
    for item in factura_tree.get_children():
        _, _, monto, cantidad = factura_tree.item(item, 'values')
        total += float(monto.replace("$", "")) * int(cantidad)

    total_label.config(text=f"Total: ${total:.2f}")


# -----------------------------
#    Generar factura
# -----------------------------
def generar_factura(factura_tree, total_label):
    total_text = total_label.cget("text").replace("Total:", "").replace("$", "").strip()
    total = float(total_text)

    if total == 0:
        messagebox.showerror("Error", "No hay productos cargados en la factura.")
        return

    id_venta = registrar_venta(total)

    messagebox.showinfo(
        "Factura generada",
        f"La venta se registró correctamente.\n\nID de venta: {id_venta}\nTotal: ${total:.2f}"
    )

    for item in factura_tree.get_children():
        factura_tree.delete(item)

    total_label.config(text="Total: $0.00")


# -----------------------------
#    Cierre del día
# -----------------------------
def cierre_del_dia():
    ventas = obtener_ventas_del_dia()
    print("DEBUG - Ventas del día obtenidas:", ventas)


    if not ventas:
        messagebox.showinfo("Cierre del día", "No hay ventas registradas hoy.")
        return

    import os
    carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")

    nombre_archivo = os.path.join(
        carpeta_descargas,
        f"reporte_{datetime.date.today()}.pdf"
    )

    generar_pdf(nombre_archivo, ventas)

    borrar_ventas_del_dia()

    messagebox.showinfo("Cierre del día", f"El PDF se guardó correctamente en:\n{nombre_archivo}")


# -----------------------------
# Quitar item de la factura
# -----------------------------
def quitar_item_factura(factura_tree, total_label):
    selected = factura_tree.selection()

    if not selected:
        messagebox.showerror("Error", "Seleccioná un producto para quitar.")
        return

    for item in selected:
        factura_tree.delete(item)

    calcular_total(factura_tree, total_label)


# -----------------------------
#    Ventana actualizar stock
# -----------------------------
def actualizar_stock_window():
    win = tk.Toplevel()
    win.title("Actualizar Stock")

    tk.Label(win, text="Código del producto:").grid(row=0, column=0, padx=10, pady=5)
    codigo_entry = tk.Entry(win)
    codigo_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(win, text="Cantidad (+ agregar / - quitar):").grid(row=1, column=0, padx=10, pady=5)
    cantidad_entry = tk.Entry(win)
    cantidad_entry.grid(row=1, column=1, padx=10, pady=5)

    def confirmar():
        codigo = codigo_entry.get().strip()
        try:
            cantidad = int(cantidad_entry.get())
            actualizado = actualizar_stock(codigo, cantidad)

            if actualizado:
                messagebox.showinfo("Éxito", "Stock actualizado correctamente.")
            else:
                messagebox.showerror("Error", "Producto no encontrado.")

            win.destroy()
        except:
            messagebox.showerror("Error", "Cantidad inválida.")

    tk.Button(win, text="Confirmar", command=confirmar).grid(row=2, column=0, columnspan=2, pady=10)


# -----------------------------
#    Ventana eliminar producto
# -----------------------------
def eliminar_producto_window():
    win = tk.Toplevel()
    win.title("Eliminar Producto")

    tk.Label(win, text="Código del producto:").grid(row=0, column=0, padx=10, pady=5)
    codigo_entry = tk.Entry(win)
    codigo_entry.grid(row=0, column=1, padx=10, pady=5)

    def confirmar():
        codigo = codigo_entry.get().strip()

        if not codigo:
            messagebox.showerror("Error", "Debe ingresar un código.")
            return

        if messagebox.askyesno("Confirmar", f"¿Eliminar el producto con código {codigo}?"):
            eliminar_producto(codigo)
            messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")
            win.destroy()

    tk.Button(win, text="Eliminar", command=confirmar).grid(row=1, column=0, columnspan=2, pady=10)


# -----------------------------
#      Construcción de Interfaz
# -----------------------------
def build_gui(root):
    root.title("Sistema de Facturación")

    frame = ttk.Frame(root, padding=20)
    frame.grid(row=0, column=0, sticky="nsew")

    ttk.Label(frame, text="Código del producto:").grid(row=0, column=0, padx=5, pady=5)
    codigo_entry = ttk.Entry(frame)
    codigo_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Button(frame, text="Agregar", command=agregar_producto_window).grid(row=0, column=2, padx=5)
    ttk.Button(frame, text="Actualizar Stock", command=actualizar_stock_window).grid(row=0, column=3, padx=5)
    ttk.Button(frame, text="Eliminar Producto", command=eliminar_producto_window).grid(row=0, column=4, padx=5)

    columns = ("Código", "Nombre", "Monto", "Cantidad")
    global factura_tree
    factura_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)

    for col in columns:
        factura_tree.heading(col, text=col)

    factura_tree.grid(row=1, column=0, columnspan=6, pady=10)

    global total_label
    total_label = ttk.Label(frame, text="Total: $0.00", font=("Arial", 14))
    total_label.grid(row=2, column=0, columnspan=2, pady=10)

    ttk.Button(frame, text="Generar Factura",
               command=lambda: generar_factura(factura_tree, total_label)).grid(row=4, column=0, pady=10, padx=10)

    ttk.Button(root, text="Quitar",
               command=lambda: quitar_item_factura(factura_tree, total_label)).grid(row=4, column=2, pady=10, padx=10)

    ttk.Button(frame, text="Cerrar Día", command=cierre_del_dia).grid(row=4, column=1, pady=10, padx=10)

    root.bind("<Return>",
              lambda e: agregar_producto_facturar(codigo_entry, factura_tree, total_label))


init_db()

root = tk.Tk()
build_gui(root)
root.mainloop()