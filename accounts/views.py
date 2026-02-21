from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from .forms import RegisterForm
from .models import Profile
from .forms import ProfileForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.http import HttpResponse
import base64
import pyotp

#LogOut
def user_logout(request):
    logout(request)
    return redirect('login')


# Registration Page
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            try:
                group = Group.objects.get(name='User')
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
	    
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


# dashboard
@login_required(login_url="login")
def dashboard(request):
    return render(request, "dashboard.html")


# profile form
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            form.save()
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    messages.success(request, "Profile updated successfully.")
    return render(request, 'profile.html', {'form': form})

# OTP 
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            profile = user.profile
            profile.generate_otp()
   # If 2FA NOT enabled → send email OTP
            if not profile.is_totp_enabled:
                profile.generate_otp()
            # Send OTP email
            send_mail(
                "Your OTP Code",
                f"Your OTP is {profile.otp}",
                "your_email@gmail.com",
                [user.email],
                fail_silently=False,
            )

            request.session["otp_user"] = user.id
            return redirect("verify_otp")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "login.html")



def verify_otp(request):
    user_id = request.session.get("otp_user")

    if not user_id:
        return redirect("login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("login")

    profile, created = Profile.objects.get_or_create(user=user)

    # 🔁 RESEND OTP (Only if email OTP mode)
    if request.method == "POST" and "resend_otp" in request.POST:

        if profile.is_totp_enabled:
            return redirect("verify_otp")  # no resend if TOTP enabled

        if profile.otp_created_at and \
           timezone.now() <= profile.otp_created_at + timedelta(seconds=30):
            messages.error(request, "Please wait before requesting a new OTP.")
            return redirect("verify_otp")

        profile.generate_otp()

        send_mail(
            subject="Your New OTP Code",
            message=f"Your OTP is {profile.otp}",
            from_email="your_email@gmail.com",
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(request, "A new OTP has been sent to your email.")
        return redirect("verify_otp")

    # ✅ VERIFY
    if request.method == "POST" and "resend_otp" not in request.POST:

        entered_otp = request.POST.get("otp")

        if not entered_otp:
            messages.error(request, "Please enter the OTP.")
            return redirect("verify_otp")

        # 🔐 IF 2FA ENABLED → VERIFY TOTP
        if profile.is_totp_enabled and profile.totp_secret:
            totp = pyotp.TOTP(profile.totp_secret)

            if totp.verify(entered_otp):
                login(request, user)
                del request.session["otp_user"]
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid Google Authenticator code.")
                return redirect("verify_otp")

        # 📧 ELSE VERIFY EMAIL OTP
        else:
            if profile.otp and \
               profile.otp == entered_otp and \
               profile.otp_created_at and \
               timezone.now() <= profile.otp_created_at + timedelta(minutes=5):

                login(request, user)
                del request.session["otp_user"]
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid or expired OTP.")
                return redirect("verify_otp")

    return render(request, "verify_otp.html", {
        "is_totp_enabled": profile.is_totp_enabled
    })


@login_required
def setup_totp(request):
    profile = request.user.profile

    # Generate secret if not exists
    if not profile.totp_secret:
        profile.totp_secret = pyotp.random_base32()
        profile.save()

    totp = pyotp.TOTP(profile.totp_secret)
    uri = totp.provisioning_uri(
        name=request.user.email,
        issuer_name="PropertyApp"
    )

    # Generate QR
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode()

    # 🔐 VERIFY ENTERED CODE
    if request.method == "POST":
        entered_code = request.POST.get("code")

        if totp.verify(entered_code):
            profile.is_totp_enabled = True
            profile.save()
            messages.success(request, "2FA enabled successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Invalid code. Try again.")

    return render(request, "setup_totp.html", {
        "qr_code": qr_image
    })

@login_required
def disable_totp(request):
    profile = request.user.profile

    profile.totp_secret = None
    profile.is_totp_enabled = False
    profile.save()

    messages.success(request, "Two-Factor Authentication has been disabled.")
    return redirect("profile")


def mark_notifications_read(request):
    if request.user.is_authenticated:
        request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))