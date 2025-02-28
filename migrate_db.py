import os
import pyodbc
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.migration
load_dotenv('.env.migration')

# Configuración de SQL Server (origen)
sql_server_conn = pyodbc.connect(os.getenv('SQL_SERVER_CONNECTION'))

# Configuración de PostgreSQL (destino)
pg_conn = psycopg2.connect(os.getenv('NEON_DB_URL'))

try:
    # Crear cursor para SQL Server
    sql_cursor = sql_server_conn.cursor()
    
    # Crear cursor para PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    # Crear tabla en PostgreSQL
    pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS formulario (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(20),
        service VARCHAR(100),
        message TEXT,
        created_at TIMESTAMP,
        status VARCHAR(20) DEFAULT 'pendiente'
    )
    """)
    
    # Obtener datos de SQL Server
    sql_cursor.execute("SELECT id, name, email, phone, service, message, created_at, status FROM Formulario")
    rows = sql_cursor.fetchall()
    
    # Insertar datos en PostgreSQL
    for row in rows:
        pg_cursor.execute("""
        INSERT INTO formulario (id, name, email, phone, service, message, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, row)
    
    # Confirmar los cambios
    pg_conn.commit()
    print(f"Migración completada. {len(rows)} registros migrados.")

except Exception as e:
    print(f"Error durante la migración: {str(e)}")
    pg_conn.rollback()

finally:
    # Cerrar conexiones
    sql_cursor.close()
    pg_cursor.close()
    sql_server_conn.close()
    pg_conn.close() 