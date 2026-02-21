import random
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.utils import timezone
import pyotp

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # 🔐 OTP Fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    # Google TOTP
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_totp_enabled = models.BooleanField(default=False)

    @property
    def formatted_employee_id(self):
        return f"{self.user.id:03d}"
#Email OTP    
    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save(update_fields=["otp", "otp_created_at"])

# Google TOTP
    def generate_totp_secret(self):
        self.totp_secret = pyotp.random_base32()
        self.save()

# Google TOTP
    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.user.email,
            issuer_name="PropertyApp"
        )
# Save Employee ID
    def save(self, *args, **kwargs):
        if not self.employee_id and self.user_id:
            self.employee_id = f"EMP{self.user_id:03d}"
        super().save(*args, **kwargs)

        if not self.employee_id:
            self.employee_id = f"EMP{self.user.id:03d}"

        super().save(*args, **kwargs)
     


    def __str__(self):
        return self.user.username

class Menu(models.Model):
    name=models.CharField(max_length=100)
    url=models.CharField(max_length=200)
    icon=models.CharField(max_length=50, blank=True, null=True)
    parent=models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return self.name

class RoleMenu(models.Model):
    group=models.ForeignKey(Group, on_delete=models.CASCADE)
    menu=models.ForeignKey(Menu, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.group.name} - {self.menu.name}"

def generate_totp_secret(self):
    self.totp_secret = pyotp.random_base32()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"
