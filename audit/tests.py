from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reservations.models import Reservation
from rooms.models import Room
from users.models import User


class ReportsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='reportes_admin',
            password='Password123!',
            role=User.Role.ADMINISTRADOR,
        )
        self.secretaria = User.objects.create_user(
            username='reportes_secretaria',
            password='Password123!',
            role=User.Role.SECRETARIA,
        )
        self.alumno = User.objects.create_user(
            username='reportes_alumno',
            password='Password123!',
            role=User.Role.ALUMNO,
        )
        self.room = Room.objects.create(
            name='Sala Reportes',
            code='REP-01',
            capacity=12,
        )
        self.other_room = Room.objects.create(
            name='Sala Sin Uso',
            code='REP-02',
            capacity=8,
        )
        self.report_date = date.today() + timedelta(days=2)
        self.confirmed = Reservation.objects.create(
            student=self.alumno,
            created_by=self.alumno,
            room=self.room,
            date=self.report_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            attendees_count=4,
            status=Reservation.Status.CONFIRMADA,
        )
        Reservation.objects.create(
            student=self.alumno,
            created_by=self.alumno,
            room=self.room,
            date=self.report_date,
            start_time=time(12, 0),
            end_time=time(13, 0),
            attendees_count=4,
            status=Reservation.Status.CANCELADA,
        )
        Reservation.objects.create(
            student=self.alumno,
            created_by=self.alumno,
            room=self.other_room,
            date=self.report_date - timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            attendees_count=4,
            status=Reservation.Status.NO_SHOW,
        )
        self.alumno.blocked_until = timezone.now() + timedelta(days=1)
        self.alumno.save(update_fields=['blocked_until'])

    def test_cp22_reportes_filtran_por_fecha_y_sala_y_calculan_indicadores(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse('reports'), {
            'date_from': self.report_date.isoformat(),
            'date_to': self.report_date.isoformat(),
            'room': self.room.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_reservations'], 2)
        self.assertEqual(response.context['confirmadas_count'], 1)
        self.assertEqual(response.context['canceladas_count'], 1)
        self.assertEqual(response.context['noshow_count'], 0)
        self.assertEqual(response.context['active_blocked_users_count'], 1)
        self.assertEqual(len(response.context['reservations_by_period']), 1)
        room_stat = next(
            item for item in response.context['room_stats']
            if item['room'].pk == self.room.pk
        )
        self.assertEqual(room_stat['reservation_count'], 2)
        self.assertEqual(room_stat['reserved_hours'], 1.0)

    def test_reportes_son_restringidos_por_rol_y_administracion_puede_acceder(self):
        self.client.force_login(self.alumno)
        self.assertRedirects(
            self.client.get(reverse('reports')),
            reverse('dashboard'),
        )

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('reports')).status_code, 200)

    def test_cp12_filtro_no_interpreta_entrada_como_sql(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('reports'), {
            'room': f"{self.room.pk} OR 1=1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(response.context['total_reservations'], 0)
