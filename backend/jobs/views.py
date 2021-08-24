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
from jobs.forms import JobForm, UserRegisterForm, UserForm
from jobs.models import Job, User
from .decorators import unauthenticated_user, allowed_users, admin_only
from .utils import *
import json
import base64
from djangotest import refresh_statuses
# email confirm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
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
  email_body = render_to_string('home/activate.html', {
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
      if request.method == "POST":
        try:
          email = request.POST['email']
          user1 = User.objects.filter(email=email).first()
          if not user1:
            messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
            return render(request, 'home/login.html')
          user = authenticate(email=user1.email, password=request.POST['password'])
          if user is not None:
            # check user confirmed
            if not user.is_email_confirmed:
              messages.add_message(request, messages.ERROR, 
                                    'Email is not verified, please check your email inbox.')
              return render(request, 'home/login.html')
            else:
              auth_login(request, user)
              # Redirect to a success page.
              request.session['email'] = user.email
              request.session['username'] = user.username
              if request.POST.get('checkbox') == 'remember-me':
                response = HttpResponseRedirect('home/')
                response.set_cookie('email', request.POST["email"])
                return response
              request.session['email'] = request.POST["email"]
              return redirect('home')
          else:
            messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
            return render(request, 'home/login.html')
        except ObjectDoesNotExist:
          messages.add_message(request, messages.ERROR, 
                                "Your username and password didn't match.")
          return render(request, 'home/login.html')
      else:
        return render(request, 'home/login.html')
    else:
      try:
        u = User.objects.get(email=request.COOKIES.get('email'))
        request.session['email'] = u.email
        request.session['username'] = u.username
      except ObjectDoesNotExist:
        return render(request, 'home/login.html')
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
  return render(request, 'home/register.html', {'form': form})

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
  
  return render(request, 'home/activate-failed.html', {'user': user})

@allowed_users(allowed_roles=['customer'])
def user(request):
  return render(request, 'users/users.html', )

class HomeView(LoginRequiredMixin, View):
  __doc__ = """
      Home view
    """
  
  def get(self, request, *args, **kwargs):
    print(request.user.is_authenticated)
    jobForm = JobForm()
    jobs = Job.objects.all()
    status = request.GET.get('status', None)
    if status == 'stop':
      jobs = jobs.filter(status=False)
    elif status == 'running':
      jobs = jobs.filter(status=True)
    context = {
      'list_job': jobs,
      'parameter': status,
      'form': jobForm,
    }
    return render(request, 'jobs/dashboard.html', context=context)


# @allowed_users(allowed_roles=['employer'])
# def home(request):
#   jobForm = JobForm()
#   jobs = Job.objects.all()
#   status = request.GET.get('status', None)
#   if status == 'stop':
#     jobs = jobs.filter(status=False)
#   elif status == 'running':
#     jobs = jobs.filter(status=True)
#   context = {
#     'list_job': jobs,
#     'parameter': status,
#     'form': jobForm,
#   }
#   return render(request, 'jobs/dashboard.html', context=context)

# You can add multiple roles
@allowed_users(allowed_roles=['employer'])
def auto_refresh(request):
  if request.is_ajax:
    jobs = Job.objects.all()
    jsonJobs = serialize('json', jobs)
    return JsonResponse({'data': jsonJobs, }, status=200)
  return JsonResponse({'data':False}, status=400)

@allowed_users(allowed_roles=['employer'])
def refresh_status(request):
  if request.is_ajax:
    refresh_statuses.get_jobs()
    return JsonResponse({'data': True}, status=200)
  return JsonResponse({'data': False}, status=400)

@allowed_users(allowed_roles=['employer']) 
def delete_job(request, pk):
  if request.is_ajax:
    job = Job.objects.get(id=pk)
    job.delete()
    return JsonResponse ({'data': True, }, status=200)
  return JsonResponse({'data':False}, status=400)

@allowed_users(allowed_roles=['employer'])
def add_job(request):
  if request.is_ajax and request.method == 'POST':
    jobForm = JobForm(request.POST, request.FILES)
    print(request.FILES)
    if jobForm.is_valid():
      jobForm.save()
      job = Job.objects.first()
      data = {
        'id': job.id,
        'name': job.name,
        'thumb': job.thumb.url,
        'document': job.document.url,
        'document_name': jobForm.cleaned_data['document'].name,
        'status': job.status,
      }
      return JsonResponse ({'data': data, }, status=200)
    else:
      print(jobForm.errors.as_text())
      return JsonResponse({'data':False}, status=200)
  return JsonResponse({'data':False}, status=400)

@allowed_users(allowed_roles=['employer'])
def edit_job(request, pk):
  if request.is_ajax:
    job = Job.objects.get(id=pk)
    data = {
      'name': job.name,
      'thumb': job.thumb.url,
      'document': job.document.url,
      'status': job.status,
      'start_time': job.start_time,
      'end_time': job.end_time,
    }
    return JsonResponse ({'data': data, }, status=200)
  return JsonResponse({'data':False}, status=400)

@allowed_users(allowed_roles=['employer'])
def update_job(request, pk):
  if request.is_ajax and request.method == 'POST':
    job = Job.objects.get(id=pk)
    jobForm = JobForm(request.POST, request.FILES, instance=job)
    if jobForm.is_valid():
      jobForm.save()
    job = Job.objects.last()
    data = {
      'id': job.id,
      'name': job.name,
      'thumb': job.thumb.url,
      'document': job.document.url,
      'document_name': job.document.url.split('/')[-1],
      'status': job.status,
    }
    return JsonResponse ({'data': data, }, status=200)
  return JsonResponse({'data':False}, status=400)

def validate_exists(request):
  if request.is_ajax and request.method == 'POST':
    try:
      Job.objects.get(name=request.POST.get('value'))
      return JsonResponse({'data':'true', }, status=200)
    except Job.DoesNotExist:
      return JsonResponse({'data':'false'}, status=200)
  return JsonResponse({'data':False}, status=400)