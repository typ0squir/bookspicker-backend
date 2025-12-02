from django.dispatch import receiver
from allauth.account.signals import user_logged_in, user_signed_up
from rest_framework.authtoken.models import Token

@receiver(user_signed_up)
def create_auth_token_on_signup(request, user, **kwargs):
    Token.objects.get_or_create(user=user)

@receiver(user_logged_in)
def create_auth_token_on_login(request, user, **kwargs):
    Token.objects.get_or_create(user=user)