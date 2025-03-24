import mysql.connector
# Configuración de la conexión a MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="localhost",        # Cambia si tu host es diferente
        user="root",       # Cambia por tu usuario de MySQL
        password="root",# Cambia por tu contraseña de MySQL
        database="facturacion"   # Base de datos creada en MySQL Workbench
    )