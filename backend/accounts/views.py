from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.serializers import serialize

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.forms import PasswordResetForm
from jobs.forms import JobForm, UserRegisterForm, UserForm
from jobs.models import Job, User
from .utils import *
import json
import base64
from djangotest import refresh_statuses
# email confirm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from django.core.mail import EmailMessage, BadHeaderError
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.db.models.query_utils import Q
from django.conf import settings
import threading

class EmailThread(threading.Thread):
  def __init__(self, email):
    self.email = email
    threading.Thread.__init__(self)
    
  def run(self):
    self.email.send()

def send_activation_email(user, request):
  current_site = get_current_site(request)
  email_subject = 'Verify your email address for ' + user.username
  email_body = render_to_string('users/activate.html', {
    'user': user,
    'domain': current_site,
    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    'token': generate_token.make_token(user)
  })
  plain_message = strip_tags(email_body)

  # email = EmailMessage(subject=email_subject, body=plain_message, 
  #              from_email=settings.DEFAULT_FROM_EMAIL, 
  #              to=[user.email])
  email = EmailMultiAlternatives(subject=email_subject, body=plain_message, 
               from_email=settings.DEFAULT_FROM_EMAIL, 
               to=[user.email])
  email.attach_alternative(email_body, "text/html")
  # email.send()
  EmailThread(email).run()

def send_reset_password(user, request):
  current_site = get_current_site(request)
  email_subject = 'Verify your email address for ' + user.username
  email_body = render_to_string('users/password-message.html', {
    'user': user,
    'domain': current_site,
    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    'token': generate_token.make_token(user)
  })
  plain_message = strip_tags(email_body)

  # email = EmailMessage(subject=email_subject, body=plain_message, 
  #              from_email=settings.DEFAULT_FROM_EMAIL, 
  #              to=[user.email])
  email = EmailMultiAlternatives(subject=email_subject, body=plain_message, 
               from_email=settings.DEFAULT_FROM_EMAIL, 
               to=[user.email])
  email.attach_alternative(email_body, "text/html")
  # email.send()
  EmailThread(email).run()

# Create your views here.
def login(request): 
  if request.session.get('email') is None:
    if request.COOKIES.get('email') is None:
      print(request.method)
      if request.method == "POST":
        try:
          email = request.POST['email']
          user1 = User.objects.filter(email=email).first()
          if not user1:
            messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
            return render(request, 'users/login.html')
          user = authenticate(email=user1.email, password=request.POST['password'])
          if user is not None:
            # check user confirmed
            if not user.is_email_confirmed:
              messages.add_message(request, messages.ERROR, 
                                    'Email is not verified, please check your email inbox.')
              return render(request, 'users/login.html')
            else:
              auth_login(request, user)
              # Redirect to a success page.
              request.session['email'] = user.email
              request.session['username'] = user.username
              if request.POST.get('checkbox') == 'remember-me':
                response = HttpResponseRedirect('users/')
                response.set_cookie('email', request.POST["email"])
                return response
              request.session['email'] = request.POST["email"]
              return redirect('home')
          else:
            messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
            return render(request, 'users/login.html')
        except ObjectDoesNotExist:
          messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
          return render(request, 'users/login.html')
      else:
        return render(request, 'users/login.html')
    else:
      try:
        u = User.objects.get(email=request.COOKIES.get('email'))
        request.session['email'] = u.email
        request.session['username'] = u.username
      except ObjectDoesNotExist:
        return render(request, 'users/login.html')
  else:
    return redirect('home')

def logout(request):
  try:
    del request.session['email']
    response = redirect('/')
    response.delete_cookie('email')
    auth_logout(request)
    return response
  except KeyError:
    response = redirect('/')
    response.delete_cookie('email')
    auth_logout(request)
    return response
  
def register(request):
  if request.method == 'POST' and request.is_ajax:
    _form = get_register_form(1)
    form = _form(request.POST)
    user_name = request.POST.get('email').split('@')[0]
    # save_form is User Model
    if form.is_valid():
      user = form.save(commit=False)
      user.username = user_name
      user.set_password(form.cleaned_data['password'])
      user.save()
      
      # send confirmation
      send_activation_email(user, request)

      group = Group.objects.get(name=request.POST.get('group'))
      user.groups.add(group)
      messages.add_message(request, messages.INFO, 
                           "We sent you an email to verify your account. <a href='https://mail.google.com/mail/u/0/#inbox' target='_blank'>Click Here</a>")
      return redirect('login')
    if (request.is_ajax()):
      return HttpResponse(json.dumps({'status': "failed", 'form-errors': form.errors}), content_type='application/json')
  else:
    form = UserRegisterForm()
  return render(request, 'users/register.html', {'form': form})

def activate_user(request, uidb64, token):
  try:
    uid = force_text(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)
  except Exception as e:
    user=None

  if user and generate_token.check_token(user, token):
    user.is_email_confirmed=True
    user.save()
    messages.add_message(request, messages.SUCCESS, 'Email verified, you can now login.')
    return redirect(reverse('login'))
  
  return render(request, 'users/activate-failed.html', {'user': user})

def password_reset_request(request):
  if request.method == 'POST':
    password_form = PasswordResetForm(request.POST)
    user_filter = User.objects.filter(Q(email=request.POST['email']))
    if password_form.is_valid():
      if user_filter.exists():
        user = User.objects.get(Q(email=request.POST['email']))
        print('test ton tai')
        send_reset_password(user, request)
        return redirect('password_reset_done')
      else:
        messages.add_message(request, messages.ERROR, 
                            "Please enter your email or phone.")
        return render(request, 'users/password-reset.html')
    else:
      messages.add_message(request, messages.ERROR, 
                            "Please enter your email or phone.")
      return render(request, 'users/password-reset.html')
  
  else:
    password_form = PasswordResetForm()  
  context = {
    'password_form': password_form,
  }
  return render(request, 'users/password-reset.html', context)