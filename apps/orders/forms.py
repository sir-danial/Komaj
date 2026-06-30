import re

from django import forms

from .models import PROVINCE_CHOICES

PHONE_RE = re.compile(r"^0\d{10}$")  # Iranian: 11 digits starting with 0


def _normalize_digits(value):
    """Convert Persian/Arabic digits to ASCII so validation is locale-agnostic."""
    if not value:
        return value
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return value.translate(trans)


class CheckoutForm(forms.Form):
    receiver_name = forms.CharField(label="نام گیرنده", max_length=120)
    phone = forms.CharField(label="شماره تماس", max_length=15)
    email = forms.EmailField(label="ایمیل (اختیاری)", required=False)
    province = forms.ChoiceField(label="استان", choices=PROVINCE_CHOICES)
    city = forms.CharField(label="شهر", max_length=60)
    postal_code = forms.CharField(label="کد پستی", max_length=10)
    address_line = forms.CharField(label="آدرس کامل", widget=forms.Textarea)
    shipping_method = forms.ChoiceField(label="روش ارسال")
    note = forms.CharField(label="توضیحات سفارش (اختیاری)", required=False, widget=forms.Textarea)
    accept_terms = forms.BooleanField(label="شرایط و قوانین را می‌پذیرم")

    def __init__(self, *args, shipping_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shipping_method"].choices = shipping_choices or []
        # apply design-system classes to text/select/textarea widgets
        for name, field in self.fields.items():
            if name in ("shipping_method", "accept_terms"):
                continue
            widget = field.widget
            css = "field"
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 3)
            widget.attrs["class"] = css
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "dir": "ltr", "placeholder": "۰۹۱۲۳۴۵۶۷۸۹"})
        self.fields["postal_code"].widget.attrs.update({"inputmode": "numeric", "dir": "ltr"})

    def clean_phone(self):
        phone = _normalize_digits(self.cleaned_data["phone"]).strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError("شماره تماس باید ۱۱ رقم و با ۰ شروع شود.")
        return phone

    def clean_postal_code(self):
        code = _normalize_digits(self.cleaned_data["postal_code"]).strip()
        if not re.match(r"^\d{10}$", code):
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return code
