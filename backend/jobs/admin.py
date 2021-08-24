from django.contrib import admin
from .models import Job, User

# Register your models here.
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'thumb', 'document', 'start_time', 'end_time', ]
    list_filter = ['id']
    search_fields = ['name']
admin.site.register(Job, JobAdmin)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_staff', 'date_joined']
    list_filter = ['id']
    search_fields = ['email']
admin.site.register(User, UserAdmin)