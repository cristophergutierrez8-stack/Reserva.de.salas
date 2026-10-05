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
4. Cuando el servicio esté disponible, abre **Shell** en el servicio y ejecuta `python manage.py createsuperuser` para crear el primer administrador.

El blueprint genera `SECRET_KEY` y enlaza `DATABASE_URL` automáticamente. Render proporciona `RENDER_EXTERNAL_HOSTNAME`, que Django usa para validar el dominio asignado. La configuración actual usa planes gratuitos, sujetos a límites y políticas de retención de Render; revisa sus condiciones antes de usar datos reales.

## Acceso para evaluación
No hay cuentas ni contraseñas demo preconfiguradas. Después del despliegue, crea el primer administrador desde **Shell** en Render con `python manage.py createsuperuser`. Inicia sesión y crea las cuentas de evaluación desde **Usuarios > Nuevo** (`/usuarios/nuevo/`), asignando el rol que corresponda y una contraseña distinta para cada cuenta.

Los botones de la pantalla de login solo completan el nombre de usuario; no completan la contraseña ni envían el formulario. Comparte las contraseñas de evaluación con el profesor por un canal privado, no en este README ni en GitHub. Usa contraseñas temporales y cámbialas después de la evaluación.
