# ─────────────────────────────────────────────────────────────────────────────
# apps/users/urls.py
#
# Rutas del módulo de usuarios.
# simplejwt nos da los endpoints de login y refresh gratis,
# solo tenemos que registrarlos aquí.
# ─────────────────────────────────────────────────────────────────────────────

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Registro de usuario nuevo
    path('register/', views.RegisterView.as_view(), name='registro_usuario'),

    # Login — devuelve access token y refresh token
    path('login/', TokenObtainPairView.as_view(), name='inicio_sesion'),

    # Renovar el access token usando el refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='renovar_token'),

    # Ver y actualizar perfil del usuario autenticado
    path('profile/', views.ProfileView.as_view(), name='perfil_usuario'),
]