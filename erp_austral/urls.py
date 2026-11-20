# erp_austral/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 1. La raíz del sitio nos manda directo a NUESTRO login personalizado
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    
    # 2. Nuestro Login y Logout personalizados
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 3. Password reset (lo dejamos por si acaso lo usas)
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # 4. El admin de Django normal (ya no está secuestrado)
    path('admin/', admin.site.urls),
    
    # 5. Tus aplicaciones
    path('bi/', include('bi.urls')),
    path('logistica/', include('logistica.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ===== TÍTULOS DEL ADMIN =====
admin.site.site_header = "Austral V&T ERP"
admin.site.site_title = "Austral V&T ERP"
admin.site.index_title = "Panel de control"
