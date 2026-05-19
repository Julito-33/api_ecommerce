# ─────────────────────────────────────────────────────────────────────────────
# apps/users/models.py
#
# Modelo de usuario personalizado.
# Django trae un User por defecto pero lo extendemos para agregar:
# - Login con email en vez de username
# - Roles: cliente o administrador
# - Teléfono y dirección para los pedidos
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    """
    Manager personalizado para que Django use email en vez de username
    al crear usuarios con createsuperuser y create_user.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        # Normaliza el email: convierte el dominio a minúsculas
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        # hash_password encripta la contraseña automáticamente
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Un superusuario tiene todos los permisos activados
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Usuario principal de la tienda.
    Hereda de AbstractBaseUser para tener control total del modelo,
    y de PermissionsMixin para el sistema de permisos de Django.
    """

    # Roles disponibles en la tienda
    ROLES = [
        ('customer', 'Cliente'),
        ('admin',    'Administrador'),
    ]

    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20, blank=True)
    role       = models.CharField(max_length=20, choices=ROLES, default='customer')

    # Campos requeridos por Django para el sistema de autenticación
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    # Timestamps automáticos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Le decimos a Django que el login es con email, no con username
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == 'admin'