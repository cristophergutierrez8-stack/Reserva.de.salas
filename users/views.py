from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.forms import LoginForm, UserAdminForm
from users.models import User
from reservations.models import Reservation
from rooms.models import Room
from django.utils import timezone


def login_view(request):
    # Si viene el parámetro ?switch=1, cerramos sesión y mostramos el formulario de login
    if request.GET.get('switch'):
        logout(request)
        messages.info(request, "Seleccione un nuevo usuario para iniciar sesión.")
        return redirect('login')

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Su cuenta de usuario se encuentra desactivada.")
                else:
                    login(request, user)
                    messages.success(request, f"¡Bienvenido(a) {user.get_full_name() or user.username} ({user.get_role_display()})!")
                    return redirect('dashboard')
            else:
                messages.error(request, "Credenciales de inicio de sesión inválidas.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Ha cerrado sesión correctamente.")
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}

    if user.is_alumno():
        # Reservas del alumno
        context['upcoming_reservations'] = Reservation.objects.filter(
            student=user,
            date__gte=timezone.now().date(),
            status=Reservation.Status.CONFIRMADA
        ).order_by('date', 'start_time')
        context['recent_history'] = Reservation.objects.filter(student=user).order_by('-date', '-start_time')[:5]

    if user.is_secretaria() or user.is_administrador():
        context['today_reservations_count'] = Reservation.objects.filter(
            date=timezone.now().date(),
            status=Reservation.Status.CONFIRMADA
        ).count()
        context['active_rooms_count'] = Room.objects.filter(is_active=True).count()
        context['blocked_users'] = User.objects.filter(blocked_until__gt=timezone.now())

    return render(request, 'users/dashboard.html', context)


@login_required
def user_list_view(request):
    if not request.user.is_administrador():
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    users_list = User.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users_list': users_list})


@login_required
def user_create_view(request):
    if not request.user.is_administrador():
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserAdminForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                new_user.set_password(password)
            new_user.save()
            messages.success(request, f"Usuario '{new_user.username}' creado exitosamente.")
            return redirect('user_list')
    else:
        form = UserAdminForm()

    return render(request, 'users/user_form.html', {'form': form, 'title': 'Crear Usuario'})


@login_required
def user_edit_view(request, user_id):
    if not request.user.is_administrador():
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    target_user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=target_user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                updated_user.set_password(password)
            updated_user.save()
            messages.success(request, f"Usuario '{updated_user.username}' actualizado exitosamente.")
            return redirect('user_list')
    else:
        form = UserAdminForm(instance=target_user)

    return render(request, 'users/user_form.html', {'form': form, 'title': f'Editar Usuario: {target_user.username}', 'target_user': target_user})
