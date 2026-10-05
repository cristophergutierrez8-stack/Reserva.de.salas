from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rooms.models import Room
from rooms.forms import RoomForm
from audit.models import AuditLog


@login_required
def room_list_view(request):
    rooms = Room.objects.all()
    return render(request, 'rooms/room_list.html', {'rooms': rooms})


@login_required
def room_create_view(request):
    if not request.user.is_administrador():
        messages.error(request, "Solo los administradores pueden gestionar salas.")
        return redirect('room_list')

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="Sala Creada",
                entity_affected=f"Sala {room.code}",
                details=f"Administrador creó la sala {room.name} con capacidad para {room.capacity} personas."
            )
            messages.success(request, f"La sala '{room.name}' fue creada exitosamente.")
            return redirect('room_list')
    else:
        form = RoomForm()

    return render(request, 'rooms/room_form.html', {'form': form, 'title': 'Crear Nueva Sala'})


@login_required
def room_edit_view(request, room_id):
    if not request.user.is_administrador():
        messages.error(request, "Solo los administradores pueden editar salas.")
        return redirect('room_list')

    room = get_object_or_404(Room, pk=room_id)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            updated_room = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="Sala Modificada",
                entity_affected=f"Sala {updated_room.code}",
                details=f"Administrador modificó la sala {updated_room.name} (Capacidad: {updated_room.capacity})."
            )
            messages.success(request, f"La sala '{updated_room.name}' fue actualizada exitosamente.")
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)

    return render(request, 'rooms/room_form.html', {'form': form, 'title': f'Editar Sala: {room.name}', 'room': room})


@login_required
def room_toggle_active_view(request, room_id):
    if not request.user.is_administrador():
        messages.error(request, "Solo los administradores pueden modificar el estado de salas.")
        return redirect('room_list')

    room = get_object_or_404(Room, pk=room_id)
    room.is_active = not room.is_active
    room.save(update_fields=['is_active'])

    status_str = "Activada" if room.is_active else "Desactivada"
    AuditLog.objects.create(
        user=request.user,
        action=f"Sala {status_str}",
        entity_affected=f"Sala {room.code}",
        details=f"Administrador cambió estado de la sala {room.code} a {status_str}."
    )
    messages.success(request, f"La sala '{room.name}' ahora está {status_str}.")
    return redirect('room_list')
