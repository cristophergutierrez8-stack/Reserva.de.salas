import os
from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse
from datetime import date, time, timedelta
from axes.conf import settings as axes_settings
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

    def test_admin_can_create_login_and_authorize_accounts_by_role(self):
        admin_login = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'Password123!',
        })
        self.assertRedirects(admin_login, reverse('dashboard'))

        users_page = self.client.get(reverse('user_list'))
        self.assertEqual(users_page.status_code, 200)
        self.assertContains(users_page, reverse('user_create'), html=False)

        create_page = self.client.get(reverse('user_create'))
        self.assertEqual(create_page.status_code, 200)
        choices = dict(create_page.context['form'].fields['role'].choices)
        self.assertIn(User.Role.ADMINISTRADOR, choices)
        self.assertIn(User.Role.ALUMNO, choices)
        self.assertIn(User.Role.SECRETARIA, choices)

        role_cases = (
            ('alumno_web', '55.555.555-5', User.Role.ALUMNO),
            ('secretaria_web', '66.666.666-6', User.Role.SECRETARIA),
            ('admin_web', '77.777.777-7', User.Role.ADMINISTRADOR),
        )
        created_users = []
        for username, rut, role in role_cases:
            password = 'StrongWebPass123!'
            response = self.client.post(reverse('user_create'), {
                'username': username,
                'email': f'{username}@example.test',
                'rut': rut,
                'role': role,
                'is_regular_student': 'on',
                'is_active': 'on',
                'password': password,
            })
            self.assertRedirects(response, reverse('user_list'))

            created_user = User.objects.get(username=username)
            created_users.append((created_user, password))
            self.assertEqual(created_user.role, role)
            self.assertTrue(created_user.is_active)
            self.assertTrue(created_user.check_password(password))
            self.assertNotEqual(created_user.password, password)
            self.assertFalse(created_user.is_staff)
            self.assertFalse(created_user.is_superuser)
            self.assertTrue(AuditLog.objects.filter(
                user=self.admin,
                action='Usuario Creado',
                entity_affected=f'Usuario #{created_user.pk}',
            ).exists())

        for created_user, password in created_users:
            role_client = Client()
            response = role_client.post(reverse('login'), {
                'username': created_user.username,
                'password': password,
            })
            self.assertRedirects(response, reverse('dashboard'))

            users_response = role_client.get(reverse('user_list'))
            if created_user.role == User.Role.ADMINISTRADOR:
                self.assertEqual(users_response.status_code, 200)
            else:
                self.assertRedirects(users_response, reverse('dashboard'))

        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)
        self.assertEqual(self.client.get(reverse('user_list')).status_code, 200)


class InitialAdminBootstrapCommandTests(TestCase):
    username = 'admin'
    strong_password = 'SecureBootstrapPass184!'

    def run_bootstrap(self, enabled='true', username=None, password=None):
        environment = {'INITIAL_ADMIN_BOOTSTRAP': enabled}
        if username is not None:
            environment['INITIAL_ADMIN_USERNAME'] = username
        if password is not None:
            environment['INITIAL_ADMIN_PASSWORD'] = password
        with patch.dict(os.environ, environment, clear=True):
            call_command('bootstrap_initial_admin', stdout=StringIO())

    def create_attempt(self, username, ip_address):
        return AccessAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent='test-agent',
            http_accept='*/*',
            path_info='/login/',
            get_data='',
            post_data='',
            failures_since_start=5,
        )

    def test_creates_only_the_initial_admin_with_hashed_password(self):
        self.run_bootstrap(
            username=self.username,
            password=self.strong_password,
        )

        admin = User.objects.get(username=self.username)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(admin.role, User.Role.ADMINISTRADOR)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password(self.strong_password))
        self.assertNotEqual(admin.password, self.strong_password)
        self.assertFalse(
            User.objects.filter(username__in=['alumno1', 'secretaria']).exists()
        )

    def test_repeat_run_does_not_duplicate_or_change_the_admin(self):
        self.run_bootstrap(
            username=self.username,
            password=self.strong_password,
        )
        admin = User.objects.get(username=self.username)
        original_password_hash = admin.password

        self.run_bootstrap(
            username=self.username,
            password='DifferentStrongPass184!',
        )

        admin.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(admin.password, original_password_hash)
        self.assertTrue(admin.check_password(self.strong_password))

    def test_existing_locked_admin_attempts_are_reset_without_changing_permissions(self):
        admin = User.objects.create_user(
            username=self.username,
            password=self.strong_password,
            role=User.Role.ADMINISTRADOR,
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )
        original_password_hash = admin.password
        self.create_attempt(self.username, '192.0.2.10')
        self.create_attempt('alumno1', '192.0.2.10')
        self.create_attempt('otra_cuenta', '198.51.100.20')

        enabled_before = axes_settings.AXES_ENABLED
        self.run_bootstrap()

        admin.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(admin.password, original_password_hash)
        self.assertFalse(admin.is_active)
        self.assertFalse(admin.is_staff)
        self.assertFalse(admin.is_superuser)
        self.assertFalse(AccessAttempt.objects.filter(username=self.username).exists())
        self.assertTrue(AccessAttempt.objects.filter(username='alumno1').exists())
        self.assertTrue(AccessAttempt.objects.filter(username='otra_cuenta').exists())
        self.assertTrue(axes_settings.AXES_ENABLED)
        self.assertEqual(axes_settings.AXES_ENABLED, enabled_before)
        self.assertFalse(
            User.objects.filter(username__in=['alumno1', 'secretaria']).exists()
        )

    def test_unblocked_admin_preserves_other_axes_attempts(self):
        admin = User.objects.create_superuser(
            username=self.username,
            password=self.strong_password,
            role=User.Role.ADMINISTRADOR,
        )
        admin_permissions = (admin.is_active, admin.is_staff, admin.is_superuser)
        other_attempt = self.create_attempt('alumno1', '192.0.2.10')

        self.run_bootstrap()

        admin.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(
            (admin.is_active, admin.is_staff, admin.is_superuser), admin_permissions
        )
        self.assertTrue(AccessAttempt.objects.filter(pk=other_attempt.pk).exists())
        self.assertFalse(
            User.objects.filter(username__in=['alumno1', 'secretaria']).exists()
        )

    def test_bootstrap_false_does_not_reset_admin_attempts(self):
        User.objects.create_superuser(
            username=self.username,
            password=self.strong_password,
            role=User.Role.ADMINISTRADOR,
        )
        attempt = self.create_attempt(self.username, '192.0.2.10')

        self.run_bootstrap(enabled='false')

        self.assertTrue(AccessAttempt.objects.filter(pk=attempt.pk).exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(axes_settings.AXES_ENABLED)

    def test_existing_admin_with_another_username_is_not_modified(self):
        existing_admin = User.objects.create_superuser(
            username='existing_admin',
            password=self.strong_password,
            role=User.Role.ADMINISTRADOR,
        )
        original_password_hash = existing_admin.password

        self.run_bootstrap(
            username=self.username,
            password='DifferentStrongPass184!',
        )

        existing_admin.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(existing_admin.password, original_password_hash)
        self.assertFalse(User.objects.filter(username=self.username).exists())

    def test_existing_administrator_role_alone_blocks_bootstrap(self):
        existing_admin = User.objects.create_user(
            username='role_admin',
            password=self.strong_password,
            role=User.Role.ADMINISTRADOR,
        )

        self.run_bootstrap()

        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(User.objects.filter(username=self.username).exists())
        self.assertFalse(existing_admin.is_staff)
        self.assertFalse(existing_admin.is_superuser)

    def test_existing_non_admin_username_causes_error_without_modification(self):
        existing_user = User.objects.create_user(
            username=self.username,
            password=self.strong_password,
            role=User.Role.ALUMNO,
        )
        original_password_hash = existing_user.password

        with self.assertRaises(CommandError):
            self.run_bootstrap(
                username=self.username,
                password='DifferentStrongPass184!',
            )

        existing_user.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(existing_user.role, User.Role.ALUMNO)
        self.assertFalse(existing_user.is_staff)
        self.assertFalse(existing_user.is_superuser)
        self.assertEqual(existing_user.password, original_password_hash)

    def test_password_must_satisfy_current_validators(self):
        with self.assertRaises(CommandError):
            self.run_bootstrap(username=self.username, password='weak')

        self.assertFalse(User.objects.exists())

    def test_false_or_missing_flag_does_not_create_users(self):
        for flag in ('false', None):
            with self.subTest(flag=flag):
                environment = {}
                if flag is not None:
                    environment['INITIAL_ADMIN_BOOTSTRAP'] = flag
                with patch.dict(os.environ, environment, clear=True):
                    call_command('bootstrap_initial_admin', stdout=StringIO())
                self.assertFalse(User.objects.exists())


class AdditionalViewsAndPermissionsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.alumno = User.objects.create_user(
            username='alumno1',
            password='Password123!',
            rut='11.111.111-1',
            role=User.Role.ALUMNO,
            is_regular_student=True,
        )
        self.secretaria = User.objects.create_user(
            username='secretaria',
            password='Password123!',
            rut='44.444.444-4',
            role=User.Role.SECRETARIA,
            is_staff=True,
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            password='Password123!',
            rut='99.999.999-9',
            role=User.Role.ADMINISTRADOR,
        )
        self.sala = Room.objects.create(
            name='Sala Test',
            code='SALA-T1',
            capacity=10,
            is_active=True,
        )
        self.tomorrow = date.today() + timedelta(days=1)

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
