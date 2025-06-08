from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserRegisterForm
import random
import string
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def generate_code():
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        input_code = request.POST.get("input_code")
        session_code = request.session.get("code")
        if form.is_valid() and input_code == session_code:
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect("login")
        else:
            messages.error(request, "Kode verifikasi salah atau form tidak valid.")
    else:
        form = UserRegisterForm()
        request.session["code"] = generate_code()
    return render(
        request,
        "accounts/register.html",
        {"form": form, "code": request.session["code"]},
    )


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")  # arahkan ke dashboard setelah login
        else:
            messages.error(request, "Username atau password salah.")

    return render(request, "accounts/login.html")  # ganti ke form login yang benar


def landing_page(request):
    return render(request, "accounts/landing.html")


@login_required
def dashboard_view(request):
    return render(request, "dataset/dashboard.html")
