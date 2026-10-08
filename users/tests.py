from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse
from datetime import date, time, timedelta
from axes.models import AccessAttempt
from audit.models import AuditLog
from users.models import User
from rooms.models import Room
from reservations.models import Reservation


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
        self.assertContains(response, 'login-layout', html=False)
        self.assertContains(response, 'login-submit', html=False)
        self.assertNotContains(response, 'login-shortcuts', html=False)
        self.assertNotContains(response, 'Password123!')

        # POST Login exitoso
        response = self.client.post(reverse('login'), {
            'username': 'alumno1',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(
            AuditLog.objects.filter(user=self.alumno, action='Inicio de sesión').exists()
        )

        # GET Dashboard autenticado
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(
            AuditLog.objects.filter(user=self.alumno, action='Cierre de sesión').exists()
        )

    def test_duracion_maxima_informada_en_formularios_de_reserva(self):
        self.client.force_login(self.alumno)
        direct_response = self.client.get(reverse('create_reservation'))

        self.assertEqual(direct_response.status_code, 200)
        self.assertContains(direct_response, 'Duración máxima por reserva: 60 minutos.')

        self.client.force_login(self.secretaria)
        assisted_response = self.client.get(reverse('assisted_reservation'))

        self.assertEqual(assisted_response.status_code, 200)
        self.assertContains(assisted_response, 'Duración máxima por reserva: 60 minutos.')

    def test_user_creation_requires_explicit_password(self):
        self.client.force_login(self.admin)
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

        user_data['username'] = 'usuario_debil'
        user_data['password'] = 'debil'
        response = self.client.post(reverse('user_create'), user_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('password', response.context['form'].errors)
        self.assertContains(response, 'mayúscula')
        self.assertFalse(User.objects.filter(username='usuario_debil').exists())

    def test_password_change_requires_policy_and_updates_hash(self):
        self.client.force_login(self.alumno)
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('password_change'), {
            'old_password': 'Password123!',
            'new_password1': 'weakpass',
            'new_password2': 'weakpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('mayúscula', str(response.context['form'].errors))

        response = self.client.post(reverse('password_change'), {
            'old_password': 'Password123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.alumno.refresh_from_db()
        self.assertTrue(self.alumno.check_password('NewPassword456!'))
        self.assertNotEqual(self.alumno.password, 'NewPassword456!')

    def test_dashboard_includes_secure_logout_form(self):
        self.client.force_login(self.alumno)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="logout_form"', html=False)
        self.assertContains(response, 'method="post"', html=False)
        self.assertContains(response, 'Cerrar sesión', html=False)
        self.assertContains(response, 'btn-logout', html=False)

    def test_admin_navigation_shows_management_links(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Navegación principal', html=False)
        self.assertContains(response, 'Abrir menú de navegación', html=False)
        self.assertContains(response, 'bi-list', html=False)
        self.assertContains(response, 'Administración', html=False)
        self.assertContains(response, 'Gestión de Usuarios', html=False)
        self.assertContains(response, reverse('user_list'), html=False)

    def test_alumno_no_puede_acceder_a_rutas_secretaria_admin(self):
        self.client.force_login(self.alumno)

        # Reserva asistida restringida
        res_asistida = self.client.get(reverse('assisted_reservation'))
        self.assertRedirects(res_asistida, reverse('dashboard'))

        # No-Show restringido
        res_noshow = self.client.get(reverse('noshow_list'))
        self.assertRedirects(res_noshow, reverse('dashboard'))

        # Usuarios restringido
        res_users = self.client.get(reverse('user_list'))
        self.assertRedirects(res_users, reverse('dashboard'))
        res_reports = self.client.get(reverse('reports'))
        self.assertRedirects(res_reports, reverse('dashboard'))

    def test_reserva_asistida_secretaria_por_rut(self):
        self.client.force_login(self.secretaria)

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

    def test_secretaria_no_puede_gestionar_usuarios(self):
        self.client.force_login(self.secretaria)
        response = self.client.get(reverse('user_list'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_usuario_inactivo_no_puede_iniciar_sesion(self):
        self.alumno.is_active = False
        self.alumno.save(update_fields=['is_active'])

        response = self.client.post(reverse('login'), {
            'username': 'alumno1',
            'password': 'Password123!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(
    AXES_FAILURE_LIMIT=2,
    AXES_COOLOFF_TIME=timedelta(minutes=1),
    AXES_LOCKOUT_PARAMETERS=['username', 'ip_address'],
)
class LoginAttemptProtectionTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username='intentofallido',
            password='Password123!',
            role=User.Role.ALUMNO,
        )

    def test_cp02_bloquea_intentos_fallidos_y_registra_la_peticion(self):
        for _ in range(2):
            self.client.post(reverse('login'), {
                'username': 'intentofallido',
                'password': 'incorrecta',
            })

        response = self.client.post(reverse('login'), {
            'username': 'intentofallido',
            'password': 'Password123!',
        })

        self.assertEqual(response.status_code, 429)
        self.assertTrue(
            AccessAttempt.objects.filter(username='intentofallido').exists()
        )
