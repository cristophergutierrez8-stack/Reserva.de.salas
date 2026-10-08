# RESERVA-SALAS

Sistema web responsive de reserva de salas para una institución educativa.

## Base documental
- `AGENTS.md`: reglas para agentes.
- `MEMORY.md`: memoria del proyecto.
- `docs/constitution.md`: principios obligatorios.
- `specs/001-reserva-salas/spec.md`: especificación.
- `specs/001-reserva-salas/plan.md`: plan.
- `specs/001-reserva-salas/tasks.md`: tareas.
- `.agents/skills/`: frontend, Django, base de datos, testing, seguridad y UML.
- `.opencode/agents/`: agentes especializados.
- `.opencode/commands/`: comandos.

## Inicio previsto
1. Crear entorno virtual.
2. Instalar Django 4.2.x.
3. Configurar MySQL/MariaDB.
4. Crear proyecto Django.
5. Implementar autenticación y roles.
6. Implementar salas y reservas.
7. Implementar reglas de negocio.
8. Implementar frontend responsive.
9. Implementar No-Show y bloqueo.
10. Ejecutar pruebas.
11. Actualizar UML con base en el código real.

Los resultados de pruebas y evidencias se generan solo después de ejecutar el prototipo.

## Despliegue en Render
1. Sube el proyecto a un repositorio de GitHub. El archivo `.gitignore` excluye `.env`, `db.sqlite3` y archivos generados; no subas secretos ni datos locales.
2. En Render, selecciona **New +** > **Blueprint**, conecta el repositorio y aplica el blueprint definido en `render.yaml`.
3. Render creará el servicio web y PostgreSQL. El servicio ejecuta las migraciones al iniciar y sirve los archivos estáticos con WhiteNoise.
4. El blueprint deja desactivado el bootstrap inicial de Administrador por defecto. Para crear el primero sin Render Shell, sigue el procedimiento de **Acceso inicial en Render** antes de desplegar.

El blueprint genera `SECRET_KEY` y enlaza `DATABASE_URL` automáticamente. Render proporciona `RENDER_EXTERNAL_HOSTNAME`, que Django usa para validar el dominio asignado. La configuración actual usa planes gratuitos, sujetos a límites y políticas de retención de Render; revisa sus condiciones antes de usar datos reales.

Para desarrollo local, crea un `.env` a partir de `.env.example` y define `SECRET_KEY` con un valor aleatorio generado por Django. No uses la clave de desarrollo como secreto de producción.

### Correo de confirmación

Las reservas confirmadas envían un correo si el alumno tiene una dirección válida. En Render, configura `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y `DEFAULT_FROM_EMAIL` con los datos SMTP de un proveedor elegido por la institución. `EMAIL_PORT` usa `587` y `EMAIL_USE_TLS` usa `True` por defecto. No guardes credenciales SMTP en GitHub. En desarrollo, `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` escribe el mensaje en la consola en lugar de enviarlo.

La protección de login bloquea una combinación de usuario e IP después de 5 intentos fallidos y aplica un período de espera de 15 minutos. Los intentos quedan registrados por django-axes en la base de datos.

### Reportes

Los reportes están disponibles para Secretaría y Administración en `/reportes/`. Permiten filtrar por fechas y sala e informan reservas por estado, sala y fecha, bloqueos vigentes y horas de reservas confirmadas. Las horas reservadas describen duración registrada; no son un porcentaje de ocupación, ya que el sistema no define horarios disponibles por sala.

## Acceso para evaluación
### Acceso inicial en Render

Para el primer despliegue que necesite una cuenta administradora, configura estas variables en **Render > servicio web > Environment**:

- `INITIAL_ADMIN_BOOTSTRAP=true`
- `INITIAL_ADMIN_USERNAME=admin`
- `INITIAL_ADMIN_PASSWORD`: una contraseña fuerte, introducida solo en Render y que cumpla la política vigente.

Después del despliegue, el comando ejecutado tras las migraciones trabaja únicamente con el username configurado `admin`, aunque ya existan otros administradores. Si `admin` no existe, lo crea con rol Administrador y permisos de superusuario. Si ya existe como administrador o superusuario, restablece su contraseña durante el bootstrap. En ambos casos valida la contraseña con los validadores actuales y usa `set_password()`. Al restablecerla, limpia solo los intentos de django-axes asociados a `admin`; Axes permanece habilitado. Si `admin` existe como cuenta no administrativa, el arranque falla sin modificarla. No crea `alumno1` ni `secretaria`, ni modifica otros usuarios. Estos cambios ocurren solo cuando `INITIAL_ADMIN_BOOTSTRAP=true`.

Inicia sesión en `/login/` y confirma que puedes administrar usuarios. **Inmediatamente después**, cambia `INITIAL_ADMIN_BOOTSTRAP` a `false` (o elimínala) y elimina `INITIAL_ADMIN_PASSWORD` de Environment en Render. El comando permanece en el arranque, pero cuando el indicador no es `true` no crea ni modifica usuarios. No escribas la contraseña en GitHub, en este archivo ni en el chat.

Una vez dentro, crea las cuentas Alumno y Secretaría desde **Usuarios > Crear Nuevo Usuario** (`/usuarios/nuevo/`). La gestión normal de usuarios utiliza la interfaz y no necesita Render Shell.
