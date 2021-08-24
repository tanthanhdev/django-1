from .forms import *
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

def get_register_form(step):
    if step:
        _form = {
            1: UserRegisterForm,
        }
        return _form.get(step)
    
class TokenGenerator(PasswordResetTokenGenerator):
    def make_hash_value(self, user, timestamp):
        return six.text_type(user.pk) + six.text_type(timestamp) + six.texT_type(user.is_email_confirmed)

generate_token = TokenGenerator()