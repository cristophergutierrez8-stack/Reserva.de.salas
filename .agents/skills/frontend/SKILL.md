# Frontend Skill — Reserva de Salas

## Objetivo
Construir una interfaz web profesional, clara y responsive.

## Tecnologías
HTML5, CSS3, JavaScript, Bootstrap 5 y Django Templates.

## Principios
- Responsive para escritorio, tablet y móvil.
- Acciones principales visibles.
- Navegación según rol.
- Formularios con labels y mensajes claros.
- No depender solo del color para estados.
- Accesibilidad razonable: foco visible, teclado, contraste y labels.

## Pantallas
Login; dashboard alumno; disponibilidad; nueva reserva; mis reservas/historial; cancelación; Secretaría con RUT; administración; salas; reportes; No-Show y bloqueo.

## Mensajes sugeridos
- "La sala ya fue reservada para ese horario."
- "La sala no tiene capacidad suficiente."
- "El alumno ya tiene 2 reservas para este día."
- "No se permiten reservas consecutivas."
- "La reserva no puede cancelarse porque faltan menos de 24 horas."
- "El alumno tiene un bloqueo vigente hasta [fecha]."

## Seguridad
El frontend nunca reemplaza las validaciones del backend. Las reglas críticas se validan nuevamente en Django.
