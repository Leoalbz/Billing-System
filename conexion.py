import sqlite3
import os


DB_FILE = os.path.join(os.path.dirname(__file__), "facturacion.db")

def conectar():
    """Retorna una conexión sqlite3. Usa row_factory para facilitar el acceso."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Inicializando base de datos en:", DB_FILE)

    conn = conectar()
    cur = conn.cursor()

    try:
        print("Creando tabla productos...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        );
        """)
        print("Tabla productos OK")

        print("Creando tabla ventas...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monto_total REAL NOT NULL,
            fecha TEXT NOT NULL
        );
        """)
        print("Tabla ventas OK")

        conn.commit()
    except Exception as e:
        print("ERROR EN init_db():", e)
    finally:
        conn.close()



