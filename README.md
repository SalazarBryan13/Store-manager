# Sistema de Gestión de Citas Dentales

Este es un sistema de gestión de citas para una clínica dental, desarrollado con FastAPI y PostgreSQL.

## Características

- Panel de administración para gestionar citas
- Filtrado y búsqueda de citas
- Estadísticas de servicios
- Exportación a CSV y PDF
- Gráficos interactivos
- Sistema de autenticación seguro

## Requisitos

- Python 3.8 o superior
- PostgreSQL
- Dependencias listadas en requirements.txt

## Configuración

1. Clonar el repositorio:
```bash
git clone https://github.com/SalazarBryan13/Store-manager.git
cd Store-manager
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
Crear un archivo `.env` con:
```
DATABASE_URL=postgresql://user:password@localhost/clinica
SECRET_KEY=tu_clave_secreta
OPENAI_API_KEY=tu_clave_api_openai
```

4. Ejecutar la aplicación:
```bash
uvicorn main:app --reload
```

## Despliegue

La aplicación está configurada para ser desplegada en Vercel. Ver `vercel.json` para la configuración del despliegue.

## Licencia

MIT
