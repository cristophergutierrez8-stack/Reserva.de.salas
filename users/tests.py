from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from rooms.models import Room
from reservations.models import Reservation
from datetime import date, time, timedelta


class ViewsAndPermissionsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Alumno
        self.alumno = User.objects.create_user(
            username='alumno1',
            password='Password123!',
            rut='11.111.111-1',
            role=User.Role.ALUMNO,
            is_regular_student=True
        )

        # Secretaría
        self.secretaria = User.objects.create_user(
            username='secretaria',
            password='Password123!',
            rut='44.444.444-4',
            role=User.Role.SECRETARIA,
            is_staff=True
        )

        # Admin
        self.admin = User.objects.create_superuser(
            username='admin',
            password='Password123!',
            rut='99.999.999-9',
            role=User.Role.ADMINISTRADOR
        )

        # Sala
        self.sala = Room.objects.create(
            name='Sala Test',
            code='SALA-T1',
            capacity=10,
            is_active=True
        )

        self.tomorrow = date.today() + timedelta(days=1)

    def test_login_logout_flow(self):
        # GET Login page
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completar usuario de prueba')
        self.assertContains(response, "fillUsername('alumno1')")
        self.assertContains(response, "fillUsername('secretaria')")
        self.assertContains(response, "fillUsername('admin')")
        self.assertNotContains(response, 'Password123!')

        # POST Login exitoso
        response = self.client.post(reverse('login'), {
            'username': 'alumno1',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

        # GET Dashboard autenticado
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Logout
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_user_creation_requires_explicit_password(self):
        self.client.login(username='admin', password='Password123!')
        user_data = {
            'username': 'nuevo_alumno',
            'email': 'nuevo@example.test',
            'rut': '55.555.555-5',
            'first_name': 'Nuevo',
            'last_name': 'Alumno',
            'role': User.Role.ALUMNO,
            'is_regular_student': 'on',
            'is_active': 'on',
            'password': '',
        }

        response = self.client.post(reverse('user_create'), user_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('password', response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='nuevo_alumno').exists())

        user_data['password'] = 'Password123!'
        response = self.client.post(reverse('user_create'), user_data)

        self.assertRedirects(response, reverse('user_list'))
        new_user = User.objects.get(username='nuevo_alumno')
        self.assertTrue(new_user.check_password('Password123!'))

    def test_dashboard_includes_secure_logout_form(self):
        self.client.login(username='alumno1', password='Password123!')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="logout_form"', html=False)
        self.assertContains(response, 'method="post"', html=False)
        self.assertContains(response, 'Cerrar sesión', html=False)

    def test_alumno_no_puede_acceder_a_rutas_secretaria_admin(self):
        self.client.login(username='alumno1', password='Password123!')

        # Reserva asistida restringida
        res_asistida = self.client.get(reverse('assisted_reservation'))
        self.assertRedirects(res_asistida, reverse('dashboard'))

        # No-Show restringido
        res_noshow = self.client.get(reverse('noshow_list'))
        self.assertRedirects(res_noshow, reverse('dashboard'))

        # Usuarios restringido
        res_users = self.client.get(reverse('user_list'))
        self.assertRedirects(res_users, reverse('dashboard'))

    def test_reserva_asistida_secretaria_por_rut(self):
        self.client.login(username='secretaria', password='Password123!')

        response = self.client.post(reverse('assisted_reservation'), {
            'rut': '11.111.111-1',
            'room': self.sala.pk,
            'date': self.tomorrow.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '15:00',
            'attendees_count': 4
        })
        self.assertRedirects(response, reverse('my_reservations'))

        # Verificar que la reserva fue creada en BD para el alumno1
        reserva = Reservation.objects.get(student=self.alumno)
        self.assertEqual(reserva.created_by, self.secretaria)
        self.assertEqual(reserva.room, self.sala)
        self.assertEqual(reserva.status, Reservation.Status.CONFIRMADA)
