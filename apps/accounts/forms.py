import re

from django import forms

from apps.orders.forms import _normalize_digits

PHONE_RE = re.compile(r"^09\d{9}$")  # Iranian mobile


class PhoneForm(forms.Form):
    phone = forms.CharField(label="شماره موبایل", max_length=15)

    def clean_phone(self):
        phone = _normalize_digits(self.cleaned_data["phone"]).strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError("شماره موبایل معتبر نیست (مثل ۰۹۱۲۳۴۵۶۷۸۹).")
        return phone


class CodeForm(forms.Form):
    code = forms.CharField(label="کد تأیید", max_length=6)

    def clean_code(self):
        code = _normalize_digits(self.cleaned_data["code"]).strip()
        if not re.match(r"^\d{4,6}$", code):
            raise forms.ValidationError("کد تأیید نامعتبر است.")
        return code
