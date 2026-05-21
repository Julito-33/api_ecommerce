# ─────────────────────────────────────────────────────────────────────────────
# tienda_naranja/urls.py
#
# Rutas principales del proyecto.
# Cada app tiene sus propias rutas en su urls.py,
# aquí solo las registramos con su prefijo correspondiente.
# A medida que creemos cada app, la vamos descomentando.
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración de Django — viene gratis
    path('admin/', admin.site.urls),

    # Rutas de cada módulo con su prefijo en la API
    path('api/usuarios/',  include('apps.users.urls')),
    path('api/productos/', include('apps.products.urls')),
    path('api/carrito/',   include('apps.cart.urls')),
    path('api/ordenes/',   include('apps.orders.urls')),
    path('api/pagos/',     include('apps.payments.urls')),
    path('api/resenas/',   include('apps.reviews.urls')),
    # path('api/facturas/',  include('apps.invoices.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Lo de arriba sirve las imágenes de productos en desarrollo