#  TechStore Paraguay — Backend API

API REST construida con Django 6.0 y Django REST Framework para la plataforma de e-commerce de componentes informáticos TechStore Paraguay.

---

##  Arquitectura general

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE (Browser)                     │
│                  localhost:3000 (Next.js)                │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP + JWT (Bearer Token)
                        │ CORS habilitado para :3000
┌───────────────────────▼─────────────────────────────────┐
│               BACKEND (Django REST API)                  │
│                  localhost:8000                          │
│                                                          │
│  urls.py → views.py → serializers.py → models.py        │
└──────────────┬─────────────────────┬────────────────────┘
               │                     │
┌──────────────▼──────┐   ┌──────────▼──────────────────┐
│   PostgreSQL :5432   │   │       Redis :6379            │
│  (Docker container) │   │   (Docker container)         │
│                      │   │                              │
│  - usuarios          │   │  - carrito_del_usuario_1     │
│  - productos         │   │  - carrito_del_usuario_2     │
│  - variantes         │   │  (expira en 7 días)          │
│  - categorias        │   │                              │
│  - ordenes           │   │                              │
│  - pagos             │   │                              │
│  - resenas           │   │                              │
└──────────────────────┘   └──────────────────────────────┘
```

---

##  Infraestructura con Docker

El proyecto usa **Docker Compose** para levantar PostgreSQL y Redis en contenedores. Esto garantiza que el entorno sea idéntico en cualquier máquina sin instalar nada manualmente.

```yaml
# docker-compose.yml
services:
  base_de_datos:      # PostgreSQL 16
    puerto: 5432
    
  cache_y_carrito:    # Redis 7
    puerto: 6379
```

### ¿Por qué Docker?
- Sin Docker: cada desarrollador instala PostgreSQL y Redis en su máquina → versiones distintas → bugs difíciles de reproducir
- Con Docker: un solo comando levanta todo → mismo entorno en desarrollo y producción

---

## 🚀 Instalación y ejecución

### Requisitos previos
- Python 3.14+
- Docker Desktop
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/Julito-33/api_ecommerce.git
cd api_ecommerce
```

### 2. Crear el entorno virtual
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear un archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=django-insecure-cambia-esto-en-produccion
DEBUG=True
DB_NAME=tienda_naranja_db
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
```

### 5. Levantar la infraestructura con Docker
```bash
docker-compose up -d
```

Esto levanta:
- PostgreSQL en `localhost:5432`
- Redis en `localhost:6379`

### 6. Aplicar migraciones
```bash
python manage.py migrate
```

### 7. Crear superusuario (admin)
```bash
python manage.py createsuperuser
```

### 8. Correr el servidor
```bash
python manage.py runserver
```

La API estará disponible en `http://localhost:8000`

---

##  Estructura del proyecto

```
tienda_naranja/
│
├── manage.py                    # CLI principal de Django
├── requirements.txt             # Dependencias Python
├── docker-compose.yml           # PostgreSQL + Redis
├── .env                         # Variables de entorno (no subir a Git)
├── .gitignore
│
├── tienda_naranja/              # Configuración global
│   ├── settings.py              # Apps, BD, JWT, CORS, Redis
│   ├── urls.py                  # Rutas raíz con include()
│   ├── wsgi.py                  # Entry point síncrono (Gunicorn)
│   └── asgi.py                  # Entry point asíncrono (WebSockets)
│
└── apps/                        # Módulos del negocio
    ├── users/                   # Autenticación JWT y roles
    ├── products/                # Productos, variantes, stock
    ├── cart/                    # Carrito en Redis
    ├── orders/                  # Órdenes con @transaction.atomic
    ├── payments/                # Pasarela de pagos propia
    ├── reviews/                 # Reseñas con moderación
    └── invoices/                # Generación de facturas PDF
```

---

## 🔌 Endpoints principales

### Autenticación
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/usuarios/register/` | Registrar nuevo usuario | No |
| POST | `/api/usuarios/login/` | Iniciar sesión → devuelve JWT | No |
| POST | `/api/usuarios/token/refresh/` | Renovar access token | No |
| GET | `/api/usuarios/perfil/` | Ver perfil del usuario | Sí |

### Productos
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/productos/` | Listar productos (con filtros) | No |
| GET | `/api/productos/?categoria=procesadores` | Filtrar por categoría | No |
| GET | `/api/productos/?buscar=intel` | Buscar por nombre | No |
| GET | `/api/productos/?precio_min=500000` | Filtrar por precio | No |
| GET | `/api/productos/<slug>/` | Detalle de un producto | No |
| GET | `/api/productos/categorias/` | Listar categorías | No |

### Carrito (Redis)
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/carrito/` | Ver carrito actual | Sí |
| POST | `/api/carrito/agregar/` | Agregar variante al carrito | Sí |
| DELETE | `/api/carrito/quitar/<id>/` | Quitar variante del carrito | Sí |
| DELETE | `/api/carrito/vaciar/` | Vaciar todo el carrito | Sí |

### Órdenes
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/ordenes/crear/` | Crear orden (transacción atómica) | Sí |
| GET | `/api/ordenes/mis-ordenes/` | Historial de órdenes | Sí |
| GET | `/api/ordenes/<id>/` | Detalle de una orden | Sí |

### Pagos
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/pagos/tarjeta/<id>/` | Pagar con tarjeta | Sí |
| POST | `/api/pagos/transferencia/<id>/` | Registrar transferencia | Sí |
| POST | `/api/pagos/efectivo/<id>/` | Pagar en efectivo | Sí |

### Reseñas
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/resenas/<slug>/` | Ver reseñas de un producto | No |
| POST | `/api/resenas/<slug>/escribir/` | Escribir reseña | Sí |
| PUT | `/api/resenas/<id>/moderar/` | Aprobar/rechazar reseña | Admin |

### Facturas
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/facturas/<id>/` | Descargar factura PDF | Sí |

---

##  Lógica de negocio destacada

### Transacción atómica en órdenes
```python
@transaction.atomic
def post(self, request):
    # Todo ocurre en una sola operación de BD
    # Si cualquier paso falla → TODO se revierte automáticamente
    orden = Orden.objects.create(...)
    for item in carrito:
        ItemDeOrden.objects.create(...)
        variante.stock -= item['cantidad']  # descuenta stock
        variante.save()
    cache.delete(clave_del_carrito)         # vacía el carrito Redis
```

### Carrito en Redis vs órdenes en PostgreSQL
```
Redis      → temporal (carrito, expira 7 días, vive en RAM)
PostgreSQL → permanente (órdenes, usuarios, facturas)
```

### Separación de roles
```
customer → puede ver, comprar y reseñar
admin    → puede gestionar productos, órdenes y moderar reseñas
```

---

##  Credenciales de prueba

```
Admin:   admin@tiendanaranja.com  /  Admin2024!
Cliente: julio@tiendanaranja.com  /  Naranja2024!

Tarjeta aprobada:  4111111111111111
Tarjeta rechazada: 4000000000000002
```

---

##  Stack tecnológico

| Tecnología | Versión | Para qué |
|------------|---------|----------|
| Python | 3.14 | Lenguaje base |
| Django | 6.0.5 | Framework web |
| Django REST Framework | 3.x | API REST |
| SimpleJWT | 5.x | Autenticación JWT |
| PostgreSQL | 16 | Base de datos principal |
| Redis | 7 | Carrito y caché |
| ReportLab | 4.x | Generación de PDFs |
| Docker | - | Contenedores |
| python-decouple | - | Variables de entorno |
| django-cors-headers | - | CORS para el frontend |

---

##  Autor

**Julito** — Estudiante de Programación V  
Universidad — Asunción, Paraguay 🇵🇾  
GitHub: [@Julito-33](https://github.com/Julito-33)
