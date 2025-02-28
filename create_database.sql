-- Crear la base de datos si no existe
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'CLINICA')
BEGIN
    CREATE DATABASE CLINICA;
END
GO

USE CLINICA;
GO

-- Crear la tabla formulario si no existe
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[formulario]') AND type in (N'U'))
BEGIN
    CREATE TABLE formulario (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100),
        email NVARCHAR(100),
        phone NVARCHAR(20),
        service NVARCHAR(50),
        message NVARCHAR(MAX),
        created_at DATETIME DEFAULT GETDATE(),
        status NVARCHAR(20) DEFAULT 'pendiente'
    );
END
GO

-- Agregar la columna status si no existe
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[formulario]') AND name = 'status')
BEGIN
    ALTER TABLE formulario
    ADD status NVARCHAR(20) DEFAULT 'pendiente';
END
GO

-- Actualizar registros existentes que no tengan status
UPDATE formulario
SET status = 'pendiente'
WHERE status IS NULL;
GO 