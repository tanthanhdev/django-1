from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
  path('login/', login, name = 'accounts-login'),
    # email confirmation
  path('activate-user/<uidb64>/<token>', activate_user, name='activate'),
  
  # Submit email form
  # path("password-reset", auth_views.PasswordResetView.as_view( template_name="users/password-reset.html"), name="password_reset"),
  path("password-reset", password_reset_request, name="password_reset"),
  # Email send success message
  path("password-reset/done/", auth_views.PasswordResetDoneView.as_view( template_name="users/password-reset-sent.html"), name="password_reset_done"),
  # Link to password reset form in email
  path("password-reset-confirm/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view( template_name="users/password-reset-confirm.html"), name="password_reset_confirm"),
  # Password successfully changed message
  path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view( template_name="users/password-reset-complete.html"), name="password_reset_complete")
]