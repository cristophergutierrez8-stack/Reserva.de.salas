# Constitución del proyecto

## 1. Fuente de verdad
La especificación funcional y las decisiones documentadas son la fuente principal.

## 2. Coherencia
Código, base de datos, interfaz, UML y pruebas deben representar el mismo comportamiento.

## 3. Seguridad por diseño
La seguridad se considera desde el diseño: autenticación, autorización, CSRF, validación de entradas y protección de datos.

## 4. Integridad de reservas
Debe evitarse doble reserva de sala, sobrepaso de capacidad, más de dos reservas diarias, reservas consecutivas/simultáneas y reservas durante bloqueo.

## 5. Trazabilidad
Cada requisito crítico debe relacionarse con regla de negocio, caso de uso, implementación, prueba y evidencia.

## 6. No inventar evidencia
Nunca afirmar resultados de pruebas, capturas, logs o métricas que no hayan sido obtenidos realmente.

## 7. No-Show
No-Show pertenece al ciclo de vida de una reserva. El bloqueo de 3 días es una restricción temporal aplicada al usuario.

## 8. Diseño web
El prototipo será web responsive. No se requiere aplicación móvil nativa.

## 9. Cambios
Toda modificación que afecte reglas, actores, permisos, estados o requisitos debe actualizar documentación.

## 10. Calidad
Antes de terminar una funcionalidad se revisan funcionamiento, validaciones, seguridad, pruebas y coherencia documental.
