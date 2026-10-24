# provision-inicial-administrador Specification

## Purpose
Permitir configurar una instalación vacía de forma segura para que un administrador pueda preparar espacios, cuentas y permisos desde la interfaz.

## Requirements

### Requirement: Crear localmente el primer administrador del sistema
El sistema DEBE (SHALL) proporcionar un comando local e interactivo para crear una cuenta activa con rol `ADMIN_SISTEMA` cuando aún no exista ninguna.

#### Scenario: Primera provisión
- WHEN una persona operadora ejecuta el comando local en una base inicializada que no contiene `ADMIN_SISTEMA` y proporciona un correo válido y una contraseña no vacía
- THEN el sistema crea una cuenta activa con rol `ADMIN_SISTEMA` y la contraseña queda almacenada como hash

### Requirement: Rechazar provisión repetida sin alterar cuentas
El sistema DEBE (SHALL) rechazar la creación inicial cuando ya existe una cuenta `ADMIN_SISTEMA` y no debe reemplazar cuentas, roles ni contraseñas. El aprovisionamiento NO DEBE estar disponible como ruta HTTP pública.

#### Scenario: Administrador ya existente
- WHEN una persona operadora intenta volver a provisionar el administrador en una base que ya tiene al menos una cuenta `ADMIN_SISTEMA`
- THEN el comando informa que ya existe un administrador y no modifica cuentas, roles ni contraseñas

### Requirement: Proteger las credenciales de provisión
El sistema DEBE (SHALL) solicitar la contraseña sin mostrarla, almacenarla solo mediante el hash seguro vigente y no ofrecer credenciales predeterminadas.

#### Scenario: Credenciales inválidas
- WHEN la persona operadora proporciona un correo inválido o una contraseña vacía
- THEN el comando informa el error, no crea una cuenta y no almacena la contraseña en texto plano

#### Scenario: Credenciales no se filtran
- WHEN el comando procesa la contraseña del primer administrador
- THEN no la muestra en terminales, mensajes de error ni registros de aplicación
