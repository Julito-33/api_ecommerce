from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class PanelDeUsuarios(UserAdmin):
    # Lo que ves en la tabla principal de usuarios
    list_display  = ['email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['-created_at']

    # Cómo se ve el formulario al abrir un usuario existente
    fieldsets = (
        ('Datos personales', {
            'fields': ('email', 'first_name', 'last_name', 'phone')
        }),
        ('Rol y permisos', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups')
        }),
        ('Último acceso', {
            'fields': ('last_login',)
        }),
    )

    # Formulario para crear un usuario nuevo desde el panel
    add_fieldsets = (
        ('Nuevo usuario', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')
        }),
    )