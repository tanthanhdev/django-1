from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
# from django.contrib.auth.forms import UserCreationForm
from jobs.models import Job, User
import datetime
from django.conf import settings
User = get_user_model()
# regex
import re

required_message="This field is required!"

class JobForm(forms.ModelForm):
  name = forms.CharField(widget=forms.TextInput(
    attrs={
      'class': 'form-control',
    }
  ))
  CHOICES = ((False, 'Stop'), (True, 'Running'))
  status = forms.ChoiceField(label='Status', widget=forms.Select(attrs={
    'class' : 'form-control'
  }), choices=CHOICES)
  start_time = forms.CharField(widget=forms.TextInput(
    attrs={
      'class' : 'form-control my-icon'
    }
  ))
  end_time = forms.CharField(widget=forms.TextInput(
    attrs={
      'class' : 'form-control my-icon'
    }
  ))
  class Meta:
    model = Job
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['name'].required = False
    self.fields['status'].required = False
    self.fields['status'].initial = False
    self.fields['status'].widget.attrs['disabled'] = 'disabled'
    self.fields['start_time'].required = False
    self.fields['end_time'].required = False
    
    if self.instance and self.instance.pk:
      self.fields['name'].initial = self.instance.name
      self.fields['status'].initial = self.instance.status 
      self.fields['status'].widget.attrs.pop('disabled', None)
      self.fields['start_time'].initial = self.instance.start_time
      self.fields['end_time'].initial = self.instance.end_time
    
  def clean(self):
    name = self.cleaned_data.get('name')
    if len(name) == 0:
      self.add_error('name', 'Name is required')
    else:
      try:
        name_object = Job.objects.filter(name__iexact=name)
        if self.instance:
          name_object = name_object.exclude(name__iexact=self.instance.name)
        if name_object:
          self.add_error('name', 'Name already exists')
      except Job.DoesNotExist:
        pass
    
    start_time = self.cleaned_data.get('start_time')
    if len(start_time) == 0 or start_time is None:
      self.add_error('start_time', 'Start time is required')
    
    end_time = self.cleaned_data.get('end_time')
    if len(end_time) == 0 or end_time is None:
      self.add_error('end_time', 'End time is required')
    
    if len(end_time) != 0 and len(start_time) != 0:
      try:
        start_time_object = datetime.datetime.fromisoformat(start_time)
      except Exception as e:
        self.add_error('start_time', 'Enter correct format')
      try:
        end_time_object = datetime.datetime.fromisoformat(end_time)
      except Exception as e:
        self.add_error('end_time', 'Enter correct format')
      if start_time_object >= end_time_object:
        self.add_error('end_time', 'End time must be after Start time.')
    
class UserRegisterForm(forms.ModelForm):
  """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

  first_name = forms.CharField(widget=forms.TextInput(attrs={
    'type': 'text',
    'class': 'form-control',
    'placeholder': 'First name',
  }))
  last_name = forms.CharField(widget=forms.TextInput(attrs={
    'type': 'text',
    'class': 'form-control',
    'placeholder': 'Last name',
  }))
  email = forms.CharField(widget=forms.TextInput(attrs={
    'type': 'text',
    'class': 'form-control',
    'placeholder': 'Email address',
  }))
  password = forms.CharField(widget=forms.TextInput(attrs={
    'type': 'password',
    'class': 'form-control d-none',
    'placeholder': 'New password',
  }))
  confirm_password = forms.CharField(widget=forms.TextInput(attrs={
    'type': 'password',
    'class': 'form-control d-none',
    'placeholder': 'Re-enter password',
  }))
  
  class Meta:
    model = User
    fields = [ 'first_name', 'last_name', 'email', 
              'password', 'confirm_password', 'address', 'avatar']
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['first_name'].required = False
    self.fields['last_name'].required = False
    self.fields['email'].required = False
    self.fields['password'].required = False
    self.fields['confirm_password'].required = False
    
    if self.instance and self.instance.pk:
      self.fields['first_name'].initial = self.instance.user.first_name
      self.fields['last_name'].initial = self.instance.user.last_name
      self.fields['password'].initial = False
      self.fields.pop('password')
      self.fields['confirm_password'].initial = False
      self.fields.pop('confirm_password')
    
  def clean(self):
    first_name = self.cleaned_data.get('first_name')
    if first_name == "":
      self.add_error('first_name', required_message)

    last_name = self.cleaned_data.get('last_name')
    if last_name == "":
      self.add_error('last_name', required_message)
      
    email = self.cleaned_data.get('email')
    if email:
      try:
        check_email = User.objects.filter(email__iexact=email)
        if self.instance.pk and self.instance.user and self.instance.user.email:
          check_email = check_email.exclude(email__iexact=self.instance.user.email)
        if check_email:
          self.add_error('email', 'Email was registered')
      except User.DoesNotExist:
        pass
      regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
      if not (regex.search(email)):
        self.add_error('email', 'Enter a valid email address.')
    else:
      self.add_error('email', required_message)

    password = self.cleaned_data.get('password')
    confirm_password = self.cleaned_data.get('confirm_password')
    SpecialSym = ['@', '#', '$', '%', '^', '&', '*']
    
    if password:
      if len(password) < 8 or len(password) > 20 or re.search('[A-Z]', password) == None or re.search('[0-9]', password) == None or re.search("[$&+,:;=?@#|'<>.^*()%!-]", password) == None:
        self.add_error('password', 'Password must be at least 8 characters and containe 1 capital letter minium and at least 1 number')
        if re.search(r"\s", password):
          self.add_error('password', 'Password can not contain spaces.') 
    else:
      self.add_error('password', required_message)
      
    if password != confirm_password:
      self.add_error('confirm_password', 'Password does not match.')
      
    if confirm_password == "":
      self.add_error('confirm_password', required_message)
  
class UserForm(forms.ModelForm):
  class Meta:
    model = User
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['address'].required = False

    if self.instance and self.instance.pk:
      self.fields['avatar'].initial = self.instance.user.avatar
      self.fields['address'].initial = self.instance.user.address
      self.fields['first_name'].initial = self.instance.user.first_name
      self.fields['last_name'].initial = self.instance.user.last_name
      self.fields['password'].initial = False
      self.fields.pop('password')
      self.fields['confirm_password'].initial = False
      self.fields.pop('confirm_password')
    
  def clean(self):
    first_name = self.cleaned_data.get('first_name')
    if first_name == "":
      self.add_error('first_name', required_message)

    last_name = self.cleaned_data.get('last_name')
    if last_name == "":
      self.add_error('last_name', required_message)
      
    email = self.cleaned_data.get('email')
    if email:
      try:
        check_email = User.objects.filter(email__iexact=email)
        if self.instance.pk and self.instance.user and self.instance.user.email:
          check_email = check_email.exclude(email__iexact=self.instance.user.email)
        if check_email:
          self.add_error('email', 'Email was registered')
      except User.DoesNotExist:
        pass
      regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
      if not (regex.search(email)):
        self.add_error('email', 'Enter a valid email address.')
    else:
      self.add_error('email', required_message)
    
    avatar = self.cleaned_data.get('avatar')
    if avatar is None:
      pass
    else:
      if not avatar.name.endswith(".jpeg") and not avatar.name.endswith(".jpg") and not avatar.name.endswith(".png"):
        self.add_error('avatar', "Only accept '.jpeg/jpg/png' format.")
      else:
        file_size = avatar.size
        if file_size > settings.MAX_UPLOAD_IMAGE_SIZE:
          self.add_error('avatar', "You need to upload files smaller than 5MB")
    
    password = self.cleaned_data.get('password')
    confirm_password = self.cleaned_data.get('confirm_password')
    SpecialSym = ['@', '#', '$', '%', '^', '&', '*']
    
    if password:
      if len(password) < 8 or re.search('[A-Z]', password) == None or re.search('[0-9]', password) == None:
        self.add_error('password', 'Password must be at least 8 characters and containe 1 capital letter minium and at least 1 number')
        if re.search(r"\s", password):
          self.add_error('password', 'Password can not contain spaces.') 
    else: 
      self.add_error('password', required_message)
      
    if password != confirm_password:
      self.add_error('password', 'Password does not match.')
  
    if confirm_password == "":
      self.add_error('confirm_password', required_message)