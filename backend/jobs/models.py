import os
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, User
import datetime

from .manager import CustomUserManager

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(('first name'), max_length=30)
    last_name = models.CharField(('last name'), max_length=150)
    email = models.EmailField(('email address'), unique=True)
    username = models.CharField(blank=True, max_length=30)
    is_staff = models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.')
    is_active = models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.\
                                              Unselect this instead of deleting accounts.')
    gender = models.CharField(max_length=255, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to ='myfile/profile', default='myfile/profile/default.jpeg', null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    date_joined = models.DateTimeField(('date joined'), default=timezone.now)

    # Add new
    # country = models.ForeignKey(Country, related_name = 'country_detail', on_delete=models.SET_NULL, blank=True, null=True)
    is_email_confirmed = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
class Job(models.Model):
  name = models.CharField(max_length=255, blank=True, null=True)
  status = models.BooleanField(default=False)
  start_time = models.DateTimeField(null=True, blank=True)
  end_time = models.DateTimeField(null=True, blank=True)
  thumb = models.ImageField(upload_to='myfile/jobs/thumb', default='myfile/jobs/thumb/default.jpeg', null=True, blank=True)
  document = models.FileField(upload_to='myfile/jobs/document', null=True, blank=True)
  
  def __str__(self):
    return self.name
  
  class Meta:
    ordering = ["-id"]
  
  def filename(self):
    return os.path.basename(self.file.name)
  
  def delete(self, using=None, keep_parents=False):
    self.thumb.storage.delete(self.thumb.name)
    self.document.storage.delete(self.document.name)
    super().delete()  
    
# class UserProfile(models.Model):
#     id = models.OneToOneField(User, primary_key=True, verbose_name='user', related_name='profile', on_delete=models.CASCADE)
#     email = models.EmailField(max_length=255)
#     name = models.CharField(max_length=255, null=True, blank=True)
#     gender = models.CharField(max_length=255, null=True, blank=True)
#     birthday = models.DateField(null=True)
#     address = models.CharField(max_length=255, null=True, blank=True)
#     avatar = models.FileField(upload_to='myfile/profile', default='myfile/profile/default.jpeg', null=True, blank=True)
    
#     def __str__(self):
#         return self.email