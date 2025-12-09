from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import datetime
import os

# ------------------------------------------------
#   Generar PDF del reporte diario
# ------------------------------------------------
def generar_pdf(nombre_archivo, ventas):
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    c.setFont("Helvetica", 12)

    c.drawString(50, 750, "REPORTE DIARIO DE VENTAS")
    c.drawString(50, 735, f"Fecha: {datetime.date.today()}")

    y = 700
    c.drawString(50, y, "Ventas realizadas:")
    y -= 20

    total_dia = 0

    for venta in ventas:
        monto = float(venta["monto_total"])
        fecha = venta["fecha"]

        total_dia += monto

        c.drawString(50, y, f"Monto: ${monto:.2f}  |  Fecha: {fecha}")
        y -= 15

        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 750

    y -= 30
    c.drawString(50, y, f"TOTAL DEL DÍA: ${total_dia:.2f}")
    y -= 20
    c.drawString(50, y, f"VENTAS REALIZADAS: {len(ventas)}")

    c.save()


