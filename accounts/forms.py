from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from applicants.models import ApplicantProfile, Education, StudyGoal

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'})
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm'})


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-[#1261a0] focus:border-[#1261a0] focus:outline-none text-sm',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-[#1261a0] focus:border-[#1261a0] focus:outline-none text-sm',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.strip().lower()



from django.conf import settings

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Account Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-[#1261a0] focus:border-[#1261a0] focus:outline-none text-sm',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )

    def save(self, **kwargs):
        email = self.cleaned_data.get('email', '')
        matching_users = list(self.get_users(email))
        if getattr(settings, 'DEBUG', False) and not matching_users:
            print("\n" + "=" * 70)
            print(f"  [FLII DEV WARNING] Password reset requested for: '{email}'")
            print(f"  NO MATCHING ACTIVE USER FOUND in database with this email!")
            print(f"  Existing user emails in DB: {[u.email for u in User.objects.all()]}")
            print(f"  Django suppresses email dispatch when no user matches.")
            print("=" * 70 + "\n")
        return super().save(**kwargs)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        super().send_mail(subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=html_email_template_name)
        if getattr(settings, 'DEBUG', False):
            protocol = context.get('protocol', 'http')
            domain = context.get('domain', '127.0.0.1:8000')
            uid = context.get('uid', '')
            token = context.get('token', '')
            reset_url = f"{protocol}://{domain}/password-reset-confirm/{uid}/{token}/"
            print("\n" + "=" * 70)
            print(f"  [FLII DEV] PASSWORD RESET LINK GENERATED FOR: {to_email}")
            print(f"  CLICKABLE RESET URL:")
            print(f"  --> {reset_url}")
            print("=" * 70 + "\n")


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-[#1261a0] focus:border-[#1261a0] focus:outline-none text-sm'
        if 'new_password1' in self.fields:
            self.fields['new_password1'].widget.attrs.update({
                'class': input_classes,
                'placeholder': 'Enter new password (min. 8 characters)'
            })
        if 'new_password2' in self.fields:
            self.fields['new_password2'].widget.attrs.update({
                'class': input_classes,
                'placeholder': 'Re-enter new password to confirm'
            })
