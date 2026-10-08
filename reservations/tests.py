from django.core import mail
from django.test import Client, TestCase, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, date, time, timedelta
from audit.models import AuditLog
from users.models import User
from rooms.models import Room
from reservations.models import Reservation
from reservations.services import (
    validate_and_create_reservation,
    cancel_reservation,
    register_noshow
)
from reservations.forms import ReservationForm


class ReservationBusinessRulesTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.alumno1 = User.objects.create_user(
            username='alumno1',
            rut='11.111.111-1',
            role=User.Role.ALUMNO,
            is_regular_student=True
        )
        self.alumno2 = User.objects.create_user(
            username='alumno2',
            rut='22.222.222-2',
            role=User.Role.ALUMNO,
            is_regular_student=True
        )
        self.secretaria = User.objects.create_user(
            username='secretaria',
            rut='44.444.444-4',
            role=User.Role.SECRETARIA,
            is_staff=True
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            rut='99.999.999-9',
            role=User.Role.ADMINISTRADOR,
            password='Password123!'
        )

        # Crear salas de prueba
        self.sala_pequena = Room.objects.create(
            name='Sala Pequeña',
            code='SALA-P1',
            capacity=4,
            is_active=True
        )
        self.sala_grande = Room.objects.create(
            name='Sala Grande',
            code='SALA-G1',
            capacity=20,
            is_active=True
        )

        self.tomorrow = date.today() + timedelta(days=1)

    def test_cp04_crear_reserva_valida(self):
        """CP04: Creación exitosa de reserva directa con todos los datos válidos."""
        reserva = validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=3
        )
        self.assertIsNotNone(reserva.pk)
        self.assertEqual(reserva.status, Reservation.Status.CONFIRMADA)
        self.assertEqual(reserva.student, self.alumno1)
        self.assertTrue(
            AuditLog.objects.filter(
                entity_affected=f"Reserva #{reserva.pk}",
                action="Reserva Creada",
            ).exists()
        )

    def test_cp21_limita_reserva_a_una_hora_en_formulario_y_backend(self):
        form = ReservationForm(data={
            'room': self.sala_pequena.pk,
            'date': self.tomorrow.isoformat(),
            'start_time': '10:00',
            'end_time': '11:01',
            'attendees_count': 2,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)

        with self.assertRaisesRegex(ValidationError, 'duración máxima'):
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.secretaria,
                room=self.sala_pequena,
                date=self.tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 1),
                attendees_count=2
            )

    def test_cp05_capacidad_maxima_excedida(self):
        """CP05: Rechazo si la cantidad de asistentes supera la capacidad de la sala."""
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.alumno1,
                room=self.sala_pequena, # Capacidad: 4
                date=self.tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 0),
                attendees_count=5 # Excede capacidad
            )
        self.assertIn("capacidad suficiente", str(ctx.exception))

    def test_cp06_limite_diario_2_reservas(self):
        """CP06: Rechazo si el alumno intenta realizar una 3ª reserva en el mismo día."""
        # 1ª Reserva
        validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(8, 0),
            end_time=time(9, 0),
            attendees_count=2
        )
        # 2ª Reserva (Horario separado)
        validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_grande,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            attendees_count=2
        )
        # 3ª Reserva -> Debe fallar
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.alumno1,
                room=self.sala_pequena,
                date=self.tomorrow,
                start_time=time(17, 0),
                end_time=time(18, 0),
                attendees_count=2
            )
        self.assertIn("ya tiene 2 reservas para este día", str(ctx.exception))

    def test_cp07_conflicto_de_sala_ocupada(self):
        """CP07: Rechazo si otra persona intenta reservar la misma sala en horario superpuesto."""
        # Alumno 1 reserva 10:00 - 11:00
        validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2
        )
        # Alumno 2 intenta reservar 10:30 - 11:30 en la misma sala -> Superposición
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno2,
                created_by=self.alumno2,
                room=self.sala_pequena,
                date=self.tomorrow,
                start_time=time(10, 30),
                end_time=time(11, 30),
                attendees_count=2
            )
        self.assertIn("ya fue reservada para ese horario", str(ctx.exception))

    def test_cp08_reservas_simultaneas_mismo_alumno(self):
        """CP08: Rechazo si el mismo alumno intenta tener reservas solapadas en salas distintas."""
        # Alumno 1 reserva Sala Pequeña 10:00 - 11:00
        validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2
        )
        # Alumno 1 intenta reservar Sala Grande 10:30 - 11:30 -> Solapamiento propio
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.alumno1,
                room=self.sala_grande,
                date=self.tomorrow,
                start_time=time(10, 30),
                end_time=time(11, 30),
                attendees_count=2
            )
        self.assertIn("reserva superpuesta", str(ctx.exception))

    def test_cp09_reservas_consecutivas_mismo_alumno(self):
        """CP09: Rechazo si el mismo alumno intenta reservar un bloque inmediatamente consecutivo."""
        # Reserva 1: 10:00 - 11:00
        validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2
        )
        # Reserva 2 consecutiva: 11:00 - 12:00 -> Debe fallar
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.alumno1,
                room=self.sala_grande,
                date=self.tomorrow,
                start_time=time(11, 0),
                end_time=time(12, 0),
                attendees_count=2
            )
        self.assertIn("reservas consecutivas", str(ctx.exception))

    def test_cp10_cancelacion_exitosa_24_horas(self):
        """CP10: Cancelación exitosa si faltan 24 horas o más."""
        future_date = date.today() + timedelta(days=3)
        reserva = validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=future_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2
        )
        cancelada = cancel_reservation(reserva, self.alumno1)
        self.assertEqual(cancelada.status, Reservation.Status.CANCELADA)

    def test_cp11_rechazo_cancelacion_menos_24_horas(self):
        """CP11: Rechazo de cancelación si faltan menos de 24 horas para el inicio."""
        # Crear reserva para hoy dentro de unas pocas horas
        today = date.today()
        # Para probar la regla de 24h en backend, creamos la reserva directamente en BD para un horario cercano
        reserva = Reservation.objects.create(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=today,
            start_time=time(23, 0),
            end_time=time(23, 30),
            attendees_count=2,
            status=Reservation.Status.CONFIRMADA
        )
        with self.assertRaises(ValidationError) as ctx:
            cancel_reservation(reserva, self.alumno1)
        self.assertIn("faltan menos de 24 horas", str(ctx.exception))

    def test_cp18_cp19_cp20_noshow_y_bloqueo_3_dias(self):
        """CP18, CP19, CP20: Registro No-Show, aplicación de bloqueo de 3 días y rechazo de nuevas reservas."""
        past_date = date.today() - timedelta(days=1)
        # Reserva ya finalizada ayer
        reserva_pasada = Reservation.objects.create(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=past_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2,
            status=Reservation.Status.CONFIRMADA
        )

        # CP18: Registrar No-Show por Secretaría
        register_noshow(reserva_pasada, self.secretaria)
        reserva_pasada.refresh_from_db()
        self.alumno1.refresh_from_db()
        self.assertEqual(reserva_pasada.status, Reservation.Status.NO_SHOW)

        # CP19: Verificar que el alumno1 tiene bloqueo de 3 días activo
        self.assertTrue(self.alumno1.is_blocked())
        self.assertIsNotNone(self.alumno1.blocked_until)

        # CP20: Rechazo de intento de reserva del alumno1 durante el período de bloqueo
        with self.assertRaises(ValidationError) as ctx:
            validate_and_create_reservation(
                student=self.alumno1,
                created_by=self.alumno1,
                room=self.sala_grande,
                date=self.tomorrow,
                start_time=time(14, 0),
                end_time=time(15, 0),
                attendees_count=2
            )
        self.assertIn("bloqueo vigente", str(ctx.exception))

    def test_cp03_consulta_de_disponibilidad_requiere_login_y_muestra_reservas(self):
        reserva = validate_and_create_reservation(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2,
        )
        client = Client()

        self.assertRedirects(
            client.get(reverse('availability')),
            f"{reverse('login')}?next={reverse('availability')}",
        )
        client.force_login(self.alumno2)
        response = client.get(reverse('availability'), {'date': self.tomorrow.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sala_pequena.code)
        room_row = next(
            item for item in response.context['rooms_availability']
            if item['room'].pk == self.sala_pequena.pk
        )
        self.assertEqual(
            list(room_row['reservations']),
            [reserva],
        )

    def test_cp13_historial_solo_muestra_reservas_del_alumno(self):
        own_reservation = Reservation.objects.create(
            student=self.alumno1,
            created_by=self.alumno1,
            room=self.sala_pequena,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2,
        )
        other_reservation = Reservation.objects.create(
            student=self.alumno2,
            created_by=self.alumno2,
            room=self.sala_grande,
            date=self.tomorrow,
            start_time=time(12, 0),
            end_time=time(13, 0),
            attendees_count=2,
        )
        client = Client()
        client.force_login(self.alumno1)

        response = client.get(reverse('my_reservations'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['reservations']),
            [own_reservation],
        )
        self.assertNotContains(response, f"Reserva #{other_reservation.pk}")


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ReservationConfirmationEmailTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='correo_alumno',
            email='alumno@example.test',
            role=User.Role.ALUMNO,
        )
        self.room = Room.objects.create(
            name='Sala Correo',
            code='MAIL-01',
            capacity=10,
        )
        self.reservation_date = date.today() + timedelta(days=1)

    def create_reservation(self):
        return validate_and_create_reservation(
            student=self.student,
            created_by=self.student,
            room=self.room,
            date=self.reservation_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=2,
        )

    def test_cp15_correo_se_envia_despues_de_confirmar_la_reserva(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            reservation = self.create_reservation()

        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['alumno@example.test'])
        self.assertIn(str(reservation.pk), mail.outbox[0].subject)
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMADA)

    def test_reserva_no_falla_si_el_alumno_no_tiene_correo(self):
        self.student.email = ''
        self.student.save(update_fields=['email'])

        with self.captureOnCommitCallbacks(execute=True):
            reservation = self.create_reservation()

        self.assertIsNotNone(reservation.pk)
        self.assertEqual(len(mail.outbox), 0)
