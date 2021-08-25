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

# Create your views here.

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