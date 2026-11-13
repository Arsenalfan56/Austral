import os
import django

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_austral.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Lee las credenciales de las variables de entorno de Render
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'ruben')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'ruben123')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'ruben@example.com')

# Busca al usuario o lo crea si no existe
user, created = User.objects.get_or_create(username=username, defaults={'email': email})

# Asegura los permisos de administrador y activa la cuenta
user.is_staff = True
user.is_superuser = True
user.is_active = True

# Asigna la contraseña
user.set_password(password)
user.save()

if created:
    print(f"Superusuario '{username}' creado exitosamente.")
else:
    print(f"Contraseña y permisos del superusuario '{username}' actualizados.")
