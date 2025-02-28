import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/clinica")

# Si estamos en Vercel, la URL comienza con postgres://, pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear el engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Establece en False para producción
    pool_pre_ping=True  # Verifica la conexión antes de usarla
)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la base para los modelos
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        # Verificar que la conexión está activa usando text()
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"Error de conexión a la base de datos: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close() 