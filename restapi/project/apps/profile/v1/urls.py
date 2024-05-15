# from django.urls import path
# from project.apps.profile.v1 import views
#
# app_name = 'profile'
#
# urlpatterns = [
#     path('auth/get-user/<str:channel_name>/', views.GetUserView.as_view(), name='get_user'),
#     path('auth/list-user/', views.ListUserView.as_view(), name='list_user'),
#     path('auth/get-user-by-id/<int:pk>/', views.GetUserById.as_view(), name='get_user_by_id'),
#     path('auth/set-profile/', views.SetProfileView.as_view(), name='set_profile'),
#     path('auth/create-profile-url/', views.CreateProfileUrlView.as_view(), name='create_profile_url'),
#     path('auth/search-user/', views.SearchUser.as_view(), name='search_user'),
#     path('contact/create-contact/', views.CreateContactView.as_view(), name='create_contact'),
#     path('contact/delete-contact/', views.DeleteContactView.as_view(), name='delete_contact'),
#     path('contact/list-contact/', views.ListContactView.as_view(), name='list_contact'),
#     path('contact/sync-contact/', views.SyncContactView.as_view(), name='sync_contact'),
#     path('contact/get-contact/<int:user_id>/', views.GetContactView.as_view(), name='get_contact'),
# ]
