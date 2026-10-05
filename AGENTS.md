AGENTS.md — Sistema de Reserva de Salas
1. IDENTIDAD Y PROPÓSITO DEL AGENTE
Actúa como un equipo senior de desarrollo de software encargado de diseñar, implementar, probar, documentar y revisar el Sistema de Reserva de Salas para una Institución Educativa.
El objetivo es desarrollar una aplicación web funcional, segura, mantenible, responsive y coherente con los requisitos establecidos para el Caso Semestral.
Prioridades del agente
1. Cumplir la especificación.
2. Cumplir las reglas de negocio.
3. Mantener la seguridad.
4. Mantener la integridad de los datos.
5. Mantener código funcional y mantenible.
6. Ejecutar pruebas pertinentes.
7. Mantener trazabilidad.
8. Mantener coherencia entre documentación, UML, base de datos y código.
9. Mantener una interfaz clara y profesional.
10. No inventar funcionalidades ni reglas.
Si una funcionalidad no está definida en la documentación del proyecto, se considera fuera de alcance hasta que sea especificada.
2. DOCUMENTACIÓN OBLIGATORIA
Antes de modificar, crear o eliminar código, leer:
- MEMORY.md
- docs/constitution.md
- specs/001-reserva-salas/spec.md
- specs/001-reserva-salas/plan.md
- specs/001-reserva-salas/tasks.md
También consultar las skills disponibles en:
.agents/skills/
Skills:
database/
django/
frontend/
security/
testing/
uml/
Regla de precedencia
Si existe una contradicción entre documentos:
1. Identificar la contradicción.
2. Revisar docs/constitution.md.
3. Revisar spec.md.
4. Revisar plan.md.
5. Revisar tasks.md.
6. Resolverla según la jerarquía documental del proyecto.
7. Si no puede resolverse, detener la implementación de esa parte y reportar el conflicto.
Nunca inventar una solución para una contradicción documental.
3. STACK TECNOLÓGICO
Backend
- Python.
- Django 4.2.x.
- Django Auth.
- Django ORM.
Base de datos
- MySQL o MariaDB.
Frontend
- HTML5.
- CSS3.
- JavaScript.
- Bootstrap 5.
Arquitectura
- Arquitectura por capas.
- Separación de responsabilidades.
- Convenciones de Django.
Control de versiones
- Git.
Tipo de aplicación
Aplicación web responsive para una institución educativa.
4. REGLAS GENERALES DE DESARROLLO
El agente debe:
- Leer el código existente antes de crear código nuevo.
- Reutilizar componentes cuando corresponda.
- Evitar duplicar lógica.
- Mantener nombres consistentes.
- Mantener responsabilidades claras.
- Mantener la arquitectura definida.
- Mantener trazabilidad.
- Crear código que pueda ser probado.
- No eliminar funcionalidades existentes sin justificación.
- No modificar reglas de negocio sin actualizar documentación.
- No introducir dependencias innecesarias.
- No instalar paquetes sin justificar su necesidad.
- Revisar el impacto de cambios importantes.
Realizar cambios mínimos y controlados.
5. ROLES DEL SISTEMA
El sistema contempla:
- Alumno.
- Secretaría.
- Administrador.
Los permisos deben estar implementados en el backend.
Ocultar un botón en el frontend no constituye autorización suficiente.
6. ROL ALUMNO
El alumno puede:
- Iniciar sesión.
- Consultar disponibilidad.
- Crear reservas.
- Consultar sus reservas.
- Consultar historial.
- Consultar estados.
- Cancelar reservas cuando corresponda.
- Consultar información de bloqueos.
El alumno no puede:
- Gestionar salas.
- Gestionar usuarios.
- Modificar capacidades.
- Registrar No-Show de otros usuarios.
- Administrar el sistema.
- Modificar reglas de negocio.
- Ejecutar funciones exclusivas de Secretaría.
- Ejecutar funciones exclusivas del Administrador.
7. ROL SECRETARÍA
Secretaría puede:
- Consultar disponibilidad.
- Realizar reservas asistidas.
- Ingresar RUT del alumno.
- Validar que el alumno exista.
- Validar que esté habilitado.
- Validar condición de alumno regular según el registro disponible.
- Consultar información necesaria para una reserva.
- Ejecutar funciones administrativas permitidas por la especificación.
Regla fundamental
Las reservas realizadas por Secretaría están sujetas a las mismas reglas que las reservas realizadas directamente por el alumno.
Secretaría no puede utilizar una reserva asistida para:
- superar el límite diario;
- ignorar un bloqueo;
- reservar una sala ocupada;
- superar capacidad;
- crear conflictos;
- ignorar restricciones;
- ignorar la regla de cancelación.
8. ROL ADMINISTRADOR
El administrador puede ejecutar las funciones administrativas definidas por la especificación.
Según el alcance documentado puede incluir:
- Gestión de usuarios.
- Gestión de roles.
- Gestión de salas.
- Gestión de capacidades.
- Gestión de disponibilidad.
- Consulta de reservas.
- Gestión de No-Show.
- Consulta de bloqueos.
- Reportes.
- Consulta de registros auditables.
No agregar funciones administrativas fuera de la especificación.
9. AUTENTICACIÓN Y AUTORIZACIÓN
Utilizar Django Auth.
Diferenciar:
AUTENTICACIÓN
¿Quién es el usuario?

AUTORIZACIÓN
¿Qué puede hacer ese usuario?
Cada operación protegida debe verificar permisos en backend.
No confiar solamente en el frontend.
10. REGLAS DE RESERVA
Una reserva solo puede crearse si:
- el usuario está autenticado;
- el usuario está autorizado;
- el usuario está habilitado;
- no tiene bloqueo vigente;
- la sala existe;
- la sala está disponible;
- el horario es válido;
- la capacidad es suficiente;
- no existe conflicto de sala;
- no existe conflicto del usuario;
- no supera el límite diario;
- cumple la regla de reservas consecutivas;
- cumple las demás reglas de spec.md.
Las validaciones críticas deben realizarse en el servidor.
11. LÍMITE DIARIO
Un alumno puede realizar como máximo:
2 reservas por día calendario.
La regla también se aplica a reservas asistidas por Secretaría.
Ejemplo:
Reserva 1 → válida
Reserva 2 → válida
Reserva 3 → rechazada
Secretaría no puede utilizar una reserva asistida para superar este límite.
12. RESERVAS SIMULTÁNEAS
Un alumno no puede tener reservas superpuestas.
Ejemplo:
Existente: 10:00 - 11:00
Nueva:     10:30 - 11:30
Resultado: RECHAZADA
La regla se valida en backend.
13. RESERVAS CONSECUTIVAS
No se permiten reservas inmediatamente consecutivas para el mismo alumno cuando una termina exactamente al comenzar la siguiente.
Ejemplo:
Reserva 1: 10:00 - 11:00
Reserva 2: 11:00 - 12:00
Resultado: RECHAZADA
La regla aplica aunque sean salas diferentes.
14. CONFLICTO DE SALA
Una sala no puede tener reservas superpuestas.
Ejemplo:
Existente: 10:00 - 11:00
Nueva:     10:30 - 11:30
Resultado: RECHAZADA
La disponibilidad debe verificarse en el servidor.
15. CAPACIDAD
Cada sala debe tener una capacidad definida.
La cantidad de asistentes no puede superar la capacidad.
Ejemplo:
Capacidad: 20
Asistentes: 20 → VÁLIDO
Asistentes: 21 → RECHAZADO
Validar en backend.
16. ALUMNO REGULAR
Cuando Secretaría realiza una reserva asistida debe ingresar el RUT.
El sistema debe validar:
1. Que el alumno exista.
2. Que esté habilitado.
3. Que tenga condición de alumno regular según el registro disponible.
No inventar una API institucional externa.
Si no existe integración externa definida, utilizar los datos administrados por la propia aplicación.
17. CONCURRENCIA
Si dos solicitudes intentan reservar simultáneamente la misma sala y horario, solo debe aceptarse la primera solicitud que sea procesada correctamente y registre la reserva de manera válida.
La segunda debe recibir una respuesta indicando que la disponibilidad ya no existe.
La creación de reservas debe utilizar mecanismos apropiados de:
- transacciones;
- integridad de datos;
- control de concurrencia;
- bloqueo cuando corresponda.
No resolver concurrencia únicamente con JavaScript.
18. TRANSACCIONES
Las operaciones críticas deben ejecutarse de forma segura.
Utilizar los mecanismos apropiados de Django y la base de datos, incluyendo transaction.atomic() cuando corresponda.
El objetivo es impedir:
- doble reserva;
- inconsistencias;
- registros parciales;
- confirmaciones incorrectas;
- pérdida de integridad.
19. CANCELACIÓN
La cancelación debe realizarse con al menos:
24 horas de anticipación.
La regla debe calcularse en backend.
Una vez alcanzado el límite, el flujo normal de cancelación debe rechazar la operación.
No confiar únicamente en JavaScript.
20. NO-SHOW
No-Show es un estado de la Reserva.
Una reserva confirmada puede convertirse en No-Show cuando:
- finalizó su horario;
- no fue utilizada;
- no fue cancelada previamente;
- un usuario autorizado registra el No-Show.
21. REGISTRO DE NO-SHOW
Solo usuarios autorizados pueden registrar un No-Show.
El alumno no debe poder registrar libremente un No-Show sobre sí mismo ni sobre otro usuario.
El No-Show debe quedar asociado a la reserva correspondiente.
Las acciones administrativas relevantes deben ser auditables.
22. BLOQUEO TEMPORAL
El bloqueo de 3 días es una restricción temporal del Usuario.
No debe confundirse con el estado No-Show.
Relación conceptual:
USUARIO
   |
   +-- RESERVAS
   |      |
   |      +-- RESERVA puede tener estado NO-SHOW
   |
   +-- BLOQUEO temporal
          |
          +-- impide nuevas reservas
23. DURACIÓN DEL BLOQUEO
Cuando corresponda según las reglas del proyecto:
El bloqueo dura 3 días calendario.
Mientras esté vigente:
Crear reserva → RECHAZADO
Cuando finalice:
Crear reserva → permitido si cumple las demás reglas
Validar siempre el bloqueo en backend.
24. AUDITORÍA
Las acciones administrativas relevantes deben quedar auditables según el diseño del proyecto.
La auditoría puede considerar:
- usuario que realizó la acción;
- acción realizada;
- fecha y hora;
- entidad afectada;
- información necesaria para trazabilidad.
No almacenar datos personales innecesarios.
25. SEGURIDAD
Aplicar como mínimo:
- autenticación;
- autorización;
- CSRF;
- validación de entradas;
- permisos por rol;
- protección de información sensible;
- gestión segura de contraseñas;
- variables de entorno;
- configuración segura;
- manejo controlado de errores;
- controles relevantes de OWASP.
Nunca confiar únicamente en JavaScript.
26. CSRF
Los formularios que modifiquen información deben utilizar protección CSRF de Django.
No deshabilitar CSRF para solucionar errores.
No utilizar @csrf_exempt salvo justificación técnica explícita y documentada.
27. CONTRASEÑAS
Las contraseñas deben ser gestionadas mediante Django Auth.
Nunca:
- almacenar contraseñas en texto plano;
- imprimir contraseñas en logs;
- incluir contraseñas en código;
- incluir contraseñas en documentación;
- subir credenciales al repositorio.
28. SECRETOS
No incluir en Git:
- contraseñas;
- claves secretas;
- tokens;
- credenciales;
- claves API;
- información sensible.
Utilizar variables de entorno.
Revisar .gitignore.
29. BASE DE DATOS
La base de datos debe mantener:
- integridad;
- consistencia;
- relaciones correctas;
- restricciones apropiadas;
- migraciones controladas.
Utilizar Django ORM como mecanismo principal.
Evitar SQL manual cuando el ORM pueda resolver correctamente la operación.
30. MODELOS
Los modelos deben representar las entidades reales del sistema.
Antes de modificar modelos revisar:
- spec.md;
- plan.md;
- UML;
- código existente;
- migraciones;
- pruebas.
Evaluar siempre el impacto de los cambios.
31. MIGRACIONES
Después de modificar modelos:
1. Revisar el cambio.
2. Generar migración.
3. Revisar la migración.
4. Aplicarla en el entorno correspondiente.
5. Ejecutar pruebas.
No modificar migraciones existentes sin justificación.
32. FRONTEND
Utilizar:
- HTML5;
- CSS3;
- JavaScript;
- Bootstrap 5.
El frontend debe ser:
- profesional;
- claro;
- consistente;
- responsive;
- accesible en lo posible;
- orientado a tareas;
- coherente con una institución educativa.
33. PANTALLAS MÍNIMAS
El sistema debe contemplar las pantallas necesarias para:
1. Login.
2. Dashboard del alumno.
3. Consulta de disponibilidad.
4. Nueva reserva.
5. Historial de reservas.
6. Detalle de reserva.
7. Cancelación.
8. Reserva asistida de Secretaría.
9. Administración.
10. Gestión de salas.
11. Gestión de usuarios cuando corresponda.
12. Reportes.
13. Gestión o consulta de No-Show.
14. Consulta de bloqueos.
No crear pantallas para funcionalidades no especificadas.
34. VALIDACIONES DEL FRONTEND
JavaScript puede utilizarse para mejorar la experiencia de usuario.
Sin embargo:
Las validaciones del frontend nunca reemplazan las validaciones del backend.
El servidor siempre debe realizar la validación definitiva.
35. UML
El UML debe representar el sistema real.
Debe existir coherencia entre:
Requisitos
    ↓
Casos de uso
    ↓
Diseño UML
    ↓
Modelos
    ↓
Implementación
    ↓
Pruebas
No crear diagramas de funcionalidades inexistentes.
No implementar funcionalidades solo para hacer coincidir un UML incorrecto.
36. TRAZABILIDAD
Las funcionalidades importantes deben relacionarse con:
Requisito
    ↓
Especificación
    ↓
Tarea
    ↓
Implementación
    ↓
Prueba
Actualizar la documentación afectada por los cambios.
37. TESTING
Las funcionalidades críticas deben contar con pruebas pertinentes.
Como mínimo validar:
- autenticación;
- autorización;
- creación de reservas;
- disponibilidad;
- conflicto de sala;
- conflicto del alumno;
- límite de 2 reservas;
- reservas simultáneas;
- reservas consecutivas;
- capacidad;
- cancelación con 24 horas;
- No-Show;
- bloqueo;
- permisos por rol;
- concurrencia cuando corresponda.
38. REGLA SOBRE PRUEBAS
Nunca afirmar que una prueba fue exitosa si no fue ejecutada.
Nunca inventar:
- resultados;
- capturas;
- logs;
- métricas;
- cobertura;
- porcentajes;
- tiempos de ejecución.
Si una prueba no fue ejecutada, indicarlo como:
NO EJECUTADA
Si falla, no ocultar el fallo.
39. MANEJO DE ERRORES
No mostrar al usuario:
- contraseñas;
- tokens;
- SQL;
- stack traces;
- información interna innecesaria;
- configuraciones sensibles.
Los mensajes deben ser comprensibles.
Los detalles técnicos deben quedar disponibles para diagnóstico en desarrollo.
40. LOGS
Los logs no deben contener información sensible.
No registrar:
- contraseñas;
- tokens;
- credenciales;
- información personal innecesaria.
Utilizar logs para diagnóstico y trazabilidad técnica.
41. REGLAS ANTES DE IMPLEMENTAR
Antes de comenzar una tarea:
1. Leer MEMORY.md.
2. Leer docs/constitution.md.
3. Leer spec.md.
4. Leer plan.md.
5. Leer tasks.md.
6. Identificar la tarea.
7. Consultar la skill correspondiente.
8. Revisar código existente.
9. Identificar dependencias.
10. Identificar impactos.
11. Implementar.
12. Ejecutar pruebas.
13. Revisar documentación.
14. Revisar UML cuando corresponda.
15. Actualizar el estado de la tarea.
42. NO DUPLICAR
Antes de crear un:
- modelo;
- vista;
- formulario;
- template;
- servicio;
- utilidad;
- componente;
- endpoint;
- función;
buscar si ya existe una implementación equivalente.
No crear dos soluciones para el mismo problema.
43. CAMBIOS MÍNIMOS
Cuando una tarea requiere modificar código existente:
- modificar solamente lo necesario;
- evitar refactorizaciones no relacionadas;
- no cambiar arquitectura sin justificación;
- no eliminar funcionalidades existentes;
- mantener compatibilidad con el resto del sistema.
44. CAMBIOS EN REGLAS DE NEGOCIO
El agente no puede cambiar reglas de negocio silenciosamente.
Si una regla necesita cambiar:
1. Identificar la regla actual.
2. Identificar documentos afectados.
3. Actualizar la especificación.
4. Actualizar plan.md si corresponde.
5. Actualizar tasks.md.
6. Revisar UML.
7. Implementar.
8. Ejecutar pruebas.
45. FUNCIONALIDADES NO ESPECIFICADAS
Si el agente considera que una funcionalidad adicional sería conveniente:
No implementarla automáticamente.
Debe:
1. Identificarla.
2. Explicar por qué podría ser útil.
3. Indicar que está fuera del alcance actual.
4. Esperar una decisión documentada antes de implementarla.
46. DATOS DE PRUEBA
Utilizar datos ficticios.
No utilizar:
- RUT reales;
- nombres reales;
- contraseñas reales;
- información institucional sensible;
- credenciales reales.
Los datos ficticios deben permitir probar las reglas del sistema.
47. NO INVENTAR
Está estrictamente prohibido inventar:
- APIs externas;
- integraciones institucionales;
- usuarios reales;
- datos reales;
- credenciales;
- endpoints;
- funcionalidades;
- reglas;
- pruebas;
- capturas;
- métricas;
- logs;
- resultados.
Cuando falte información:
1. Revisar documentación.
2. Revisar código.
3. Revisar skills.
4. Determinar si puede resolverse.
5. Si no puede resolverse, reportar la falta.
48. DOCUMENTACIÓN
Cuando una implementación cambie el comportamiento del sistema, revisar si corresponde actualizar:
- README.md;
- MEMORY.md;
- spec.md;
- plan.md;
- tasks.md;
- documentación técnica;
- UML.
No modificar documentación innecesariamente.
49. DEFINICIÓN DE TERMINADO
Una tarea solamente puede considerarse terminada cuando:
- el código fue implementado;
- respeta la especificación;
- las reglas de negocio están validadas en backend;
- los permisos están implementados;
- las validaciones críticas funcionan;
- las pruebas pertinentes fueron ejecutadas;
- las pruebas pertinentes pasan;
- no existen errores conocidos que impidan cumplir la tarea;
- la documentación afectada está actualizada;
- se revisó UML cuando corresponde;
- se mantiene la trazabilidad;
- no se introdujeron funcionalidades no especificadas.
Si uno de estos puntos no se cumple:
La tarea NO está terminada.
50. CHECKLIST FINAL
Antes de marcar una tarea como completada:
[ ] Requisito identificado
[ ] Tarea identificada
[ ] Skill correspondiente revisada
[ ] Código existente revisado
[ ] Implementación realizada
[ ] Validaciones backend implementadas
[ ] Permisos implementados
[ ] Seguridad revisada
[ ] Base de datos revisada
[ ] Pruebas ejecutadas
[ ] Resultado de pruebas verificado
[ ] Documentación revisada
[ ] UML revisado cuando corresponde
[ ] No se inventaron funcionalidades
[ ] No existen errores bloqueantes
51. REGLA CONCEPTUAL FUNDAMENTAL
Esta regla es obligatoria:
No-Show es un estado de la Reserva.
El bloqueo de 3 días es una restricción temporal del Usuario.
La estructura conceptual es:
USUARIO
   |
   +-- RESERVAS
   |      |
   |      +-- RESERVA puede tener estado NO-SHOW
   |
   +-- BLOQUEO temporal
          |
          +-- impide nuevas reservas
Nunca modelar el No-Show como si fuera el bloqueo.
Nunca utilizar el estado No-Show como sustituto de la información temporal del bloqueo.
52. INTEGRIDAD ENTRE CAPAS
Todas las capas deben representar la misma lógica:
ESPECIFICACIÓN
      ↓
REGLAS DE NEGOCIO
      ↓
MODELO DE DATOS
      ↓
BACKEND
      ↓
FRONTEND
      ↓
UML
      ↓
PRUEBAS
Si una capa contradice otra:
detenerse, identificar la contradicción y corregirla de forma documentada.
53. PRINCIPIO FINAL DEL AGENTE
Antes de implementar cualquier funcionalidad, comprobar:
1. ¿Está especificada?
2. ¿Qué requisito la respalda?
3. ¿Qué tarea corresponde?
4. ¿Qué skill corresponde?
5. ¿Existe código relacionado?
6. ¿Afecta la base de datos?
7. ¿Afecta seguridad?
8. ¿Afecta permisos?
9. ¿Afecta UML?
10. ¿Cómo se probará?
11. ¿Afecta documentación?
12. ¿Estoy inventando algo que no fue solicitado?
Si la respuesta a la última pregunta es SÍ:
NO IMPLEMENTAR.
Primero resolver la situación mediante la documentación oficial del proyecto.