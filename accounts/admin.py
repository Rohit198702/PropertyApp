from django.contrib import admin
from .models import Menu, RoleMenu
from .models import Notification
# Register your models here.

admin.site.register(Menu)
admin.site.register(RoleMenu)
admin.site.register(Notification)
