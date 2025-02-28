import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def fix_sequence():
    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Crear la secuencia si no existe
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'formulario_id_seq') THEN
                    CREATE SEQUENCE formulario_id_seq;
                END IF;
            END $$;
        """)
        
        # Establecer el valor actual de la secuencia
        cur.execute("""
            SELECT setval('formulario_id_seq', COALESCE((SELECT MAX(id) FROM formulario), 0) + 1, false);
        """)
        
        # Modificar la columna id para usar la secuencia
        cur.execute("""
            ALTER TABLE formulario ALTER COLUMN id SET DEFAULT nextval('formulario_id_seq');
        """)
        
        # Confirmar los cambios
        conn.commit()
        print("Secuencia arreglada exitosamente")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_sequence() 