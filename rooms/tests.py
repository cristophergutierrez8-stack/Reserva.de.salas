from django.test import Client, TestCase
from django.urls import reverse

from audit.models import AuditLog
from rooms.models import Room
from users.models import User


class RoomStateChangeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='salas_admin',
            password='Password123!',
            role=User.Role.ADMINISTRADOR,
        )
        self.secretaria = User.objects.create_user(
            username='salas_secretaria',
            password='Password123!',
            role=User.Role.SECRETARIA,
        )
        self.room = Room.objects.create(
            name='Sala Estado',
            code='STATE-01',
            capacity=10,
        )

    def test_cp17_get_no_cambia_estado_y_post_protegido_actualiza_sala(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)

        response = client.get(reverse('room_toggle', args=[self.room.pk]))
        self.assertEqual(response.status_code, 405)
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_active)

        client.get(reverse('room_list'))
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('room_toggle', args=[self.room.pk]),
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_active)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.admin,
                action='Sala Desactivada',
                entity_affected=f'Sala {self.room.code}',
            ).exists()
        )

    def test_secretaria_no_puede_modificar_estado_de_sala(self):
        client = Client()
        client.force_login(self.secretaria)

        response = client.post(reverse('room_toggle', args=[self.room.pk]))

        self.assertRedirects(response, reverse('room_list'))
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_active)
