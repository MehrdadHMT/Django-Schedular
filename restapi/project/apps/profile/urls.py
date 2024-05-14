from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from project.apps.profile.v1.views import RegisterView, LoginView, LogoutView, ProfileView, ChangePasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api_user_register'),
    path('login/', LoginView.as_view(), name='api_user_login'),
    path('logout/', LogoutView.as_view(), name='api_user_logout'),
    path('get-profile/', ProfileView.as_view(), name='api_get_profile'),
    path('set-profile/', ProfileView.as_view(), name='api_set_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='api_change_password'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
