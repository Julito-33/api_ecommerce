from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # El nombre debe coincidir exactamente con la ruta de la carpeta
    name = 'apps.users'