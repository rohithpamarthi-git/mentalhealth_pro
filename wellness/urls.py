from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('assessment/', views.assessment, name='assessment'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),
    path('counselor/', views.counselor_request, name='counselor_request'),
    path('resources/', views.resources, name='resources'),
    path('progress/', views.progress_view, name='progress'),
]
