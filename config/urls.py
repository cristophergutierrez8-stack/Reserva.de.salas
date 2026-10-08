from django.contrib import admin
from django.urls import path
from users import views as user_views
from rooms import views as room_views
from reservations import views as reservation_views
from audit import views as audit_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación y Dashboard
    path('', user_views.login_view, name='home'),
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('usuarios/cambiar-contrasena/', user_views.UserPasswordChangeView.as_view(), name='password_change'),
    path('dashboard/', user_views.dashboard_view, name='dashboard'),

    # Disponibilidad y Reservas
    path('disponibilidad/', reservation_views.availability_view, name='availability'),
    path('reservas/nueva/', reservation_views.create_reservation_view, name='create_reservation'),
    path('reservas/asistida/', reservation_views.assisted_reservation_view, name='assisted_reservation'),
    path('reservas/mis-reservas/', reservation_views.my_reservations_view, name='my_reservations'),
    path('reservas/<int:reservation_id>/', reservation_views.reservation_detail_view, name='reservation_detail'),
    path('reservas/<int:reservation_id>/cancelar/', reservation_views.cancel_reservation_view, name='cancel_reservation'),

    # No-Show y Bloqueos
    path('noshow/', reservation_views.noshow_list_view, name='noshow_list'),
    path('noshow/<int:reservation_id>/registrar/', reservation_views.register_noshow_view, name='register_noshow'),

    # Administración de Salas
    path('salas/', room_views.room_list_view, name='room_list'),
    path('salas/nueva/', room_views.room_create_view, name='room_create'),
    path('salas/<int:room_id>/editar/', room_views.room_edit_view, name='room_edit'),
    path('salas/<int:room_id>/toggle/', room_views.room_toggle_active_view, name='room_toggle'),

    # Administración de Usuarios
    path('usuarios/', user_views.user_list_view, name='user_list'),
    path('usuarios/nuevo/', user_views.user_create_view, name='user_create'),
    path('usuarios/<int:user_id>/editar/', user_views.user_edit_view, name='user_edit'),

    # Auditoría y Reportes
    path('auditoria/', audit_views.audit_log_view, name='audit_log'),
    path('reportes/', audit_views.reports_view, name='reports'),
]
