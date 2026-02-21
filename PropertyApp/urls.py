"""
URL configuration for PropertyApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from accounts import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from accounts.forms import CustomPasswordResetForm
from accounts.forms import CustomSetPasswordForm
from django.urls import reverse_lazy


urlpatterns = [    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('admin/', admin.site.urls),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html',form_class=CustomPasswordResetForm), name='password_reset'),
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html',form_class=CustomSetPasswordForm,success_url=reverse_lazy('login')), name='password_reset_confirm'),  
path('', views.login_view, name='login'), 
path('verify-otp/', views.verify_otp, name='verify_otp'),
path("setup-2fa/", views.setup_totp, name="setup_totp"),
path("disable-2fa/", views.disable_totp, name="disable_totp"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
