from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import ValidationError


class PickyAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                ("This account is inactive."),
                code='inactive',
            )
        if user.username.startswith('b'):
            raise ValidationError(
                ("Sorry, accounts starting with 'b' aren't welcome here."),
                code='no_b_users',
            )
