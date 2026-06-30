from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CodeForm, PhoneForm
from .otp import OTPError, request_otp, verify_otp

User = get_user_model()
PHONE_SESSION_KEY = "otp_phone"
NEXT_SESSION_KEY = "login_next"


def _safe_next(request, default="/"):
    nxt = request.session.get(NEXT_SESSION_KEY) or request.GET.get("next") or default
    if url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return nxt
    return default


def login_request(request):
    """Step 1 — enter mobile, receive OTP."""
    if request.user.is_authenticated:
        return redirect("/")
    if request.GET.get("next"):
        request.session[NEXT_SESSION_KEY] = request.GET["next"]

    if request.method == "POST":
        form = PhoneForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            try:
                request_otp(phone)
            except OTPError as exc:
                messages.error(request, str(exc))
                return render(request, "accounts/login_phone.html", {"form": form})
            request.session[PHONE_SESSION_KEY] = phone
            messages.success(request, "کد تأیید ارسال شد.")
            return redirect("accounts:verify")
    else:
        form = PhoneForm()
    return render(request, "accounts/login_phone.html", {"form": form})


def login_verify(request):
    """Step 2 — enter the 6-digit code."""
    phone = request.session.get(PHONE_SESSION_KEY)
    if not phone:
        return redirect("accounts:login")

    if request.method == "POST":
        form = CodeForm(request.POST)
        if form.is_valid():
            try:
                ok = verify_otp(phone, form.cleaned_data["code"])
            except OTPError as exc:
                messages.error(request, str(exc))
                request.session.pop(PHONE_SESSION_KEY, None)
                return redirect("accounts:login")
            if ok:
                user, _ = User.objects.get_or_create(
                    username=phone, defaults={"first_name": ""}
                )
                if not user.has_usable_password():
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                login(request, user)  # preserves the session cart
                request.session.pop(PHONE_SESSION_KEY, None)
                messages.success(request, "خوش آمدید!")
                return redirect(_safe_next(request))
            messages.error(request, "کد وارد‌شده نادرست است.")
    else:
        form = CodeForm()
    return render(request, "accounts/login_code.html", {"form": form, "phone": phone})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "از حساب خود خارج شدید.")
    return redirect("/")


def resend_code(request):
    phone = request.session.get(PHONE_SESSION_KEY)
    if not phone:
        return redirect("accounts:login")
    try:
        request_otp(phone)
        messages.success(request, "کد تأیید مجدداً ارسال شد.")
    except OTPError as exc:
        messages.error(request, str(exc))
    return redirect("accounts:verify")
