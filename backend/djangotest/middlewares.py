from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.urls import resolve
from jobs.models import User
from django.core.exceptions import ObjectDoesNotExist

class ProcMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response
    # One-time configuration and initialization.
      
  def __call__(self, request):
    # Code to be executed for each request before
    # the view (and later middleware) are called.
    current_url = resolve(request.path_info).url_name
    if(current_url == 'register'):
      if request.user.is_authenticated:
        try:
          if request.session.get('email') or request.COOKIES.get('email'):
            return redirect('home')
        except:
            pass
    
    response = self.get_response(request)
    return response
      
  def process_exception(self, request, exception):
    pass

  # def process_view(self, request, view_func, view_args, view_kwargs):
  #   if request.path !=  '/register/' and request.path.split('/')[1] != 'admin' and request.path.split('/')[1] != 'ckeditor':
  #     if request.session.get('email') is None:
  #       if request.COOKIES.get('email') is None:
  #         if request.method == "POST":
  #           try:
  #             username = User.objects.get(email=request.POST['email']).username
  #             user = authenticate(request, username = username, password = request.POST['password'])
  #             if user is None:
  #               return render(request, 'home/login.html', {'message': "Your username and password didn't match."})
  #           except ObjectDoesNotExist:
  #             return render(request, 'home/login.html', {'message': "Your username and password didn't match."})
  #         else:
  #           return render(request, 'home/login.html')