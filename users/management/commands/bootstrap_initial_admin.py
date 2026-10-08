import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.models import Q

from axes.utils import reset as reset_axes_attempts

from users.models import User


class Command(BaseCommand):
    help = "Optionally creates the initial admin account for a fresh deployment."

    def handle(self, *args, **options):
        bootstrap_enabled = os.environ.get(
            "INITIAL_ADMIN_BOOTSTRAP", ""
        ).strip().lower()
        if bootstrap_enabled not in {"true", "false", ""}:
            raise CommandError("INITIAL_ADMIN_BOOTSTRAP must be true or false.")
        if bootstrap_enabled != "true":
            self.stdout.write("Initial administrator bootstrap is disabled.")
            return

        existing_account = User.objects.filter(username="admin").first()
        if existing_account:
            if not (
                existing_account.is_superuser
                or existing_account.role == User.Role.ADMINISTRADOR
            ):
                raise CommandError(
                    "Bootstrap stopped: the configured username belongs to a non-admin user. "
                    "No existing account was changed."
                )

            reset_axes_attempts(username="admin")
            self.stdout.write(
                "Initial administrator already exists; its Axes attempts were reset."
            )
            return

        if User.objects.filter(
            Q(is_superuser=True) | Q(role=User.Role.ADMINISTRADOR)
        ).exists():
            self.stdout.write(
                "Initial administrator bootstrap skipped; an administrator already exists."
            )
            return

        username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
        password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
        if username != "admin":
            raise CommandError(
                "INITIAL_ADMIN_USERNAME must be set to the required bootstrap username."
            )
        if not password:
            raise CommandError(
                "INITIAL_ADMIN_PASSWORD is required while bootstrap is enabled."
            )

        if User.objects.filter(username=username).exists():
            raise CommandError(
                "Bootstrap stopped: the configured username belongs to a non-admin user. "
                "No existing account was changed."
            )

        try:
            with transaction.atomic():
                if User.objects.filter(
                    Q(is_superuser=True) | Q(role=User.Role.ADMINISTRADOR)
                ).exists():
                    self.stdout.write(
                        "Initial administrator bootstrap skipped; an administrator already exists."
                    )
                    return

                if User.objects.filter(username=username).exists():
                    raise CommandError(
                        "Bootstrap stopped: the configured username belongs to a "
                        "non-admin user. No existing account was changed."
                    )

                user = User(
                    username=username,
                    role=User.Role.ADMINISTRADOR,
                    is_active=True,
                    is_staff=True,
                    is_superuser=True,
                )
                try:
                    validate_password(password, user=user)
                except ValidationError as error:
                    raise CommandError("; ".join(error.messages)) from error

                user.set_password(password)
                user.save(force_insert=True)
        except IntegrityError:
            existing_user = User.objects.filter(username=username).first()
            if existing_user and (
                existing_user.is_superuser
                or existing_user.role == User.Role.ADMINISTRADOR
            ):
                self.stdout.write(
                    "Initial administrator bootstrap skipped; an administrator already exists."
                )
                return
            raise CommandError(
                "Bootstrap could not create the initial administrator because the "
                "configured username is already in use. No existing account was changed."
            ) from None

        self.stdout.write("Initial administrator created successfully.")
