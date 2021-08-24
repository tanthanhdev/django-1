from django.urls import path
from .views import *

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('auto-refresh/', auto_refresh, name='auto-refresh'),
    path('refresh-status/', refresh_status, name='refresh-status'),
    path('delete/<int:pk>/', delete_job, name='delete-job'),
    path('edit/<int:pk>/', edit_job, name='edit-job'),
    path('update/<int:pk>/', update_job, name='update-job'),
    path('add/', add_job, name='add-new-job'),
    path('validate/', validate_exists, name='validate-exists'),

    path('user/', user, name='user-page'),

    # email confirmation
    path('activate-user/<uidb64>/<token>', activate_user, name='activate')
]