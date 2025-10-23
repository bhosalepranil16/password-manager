from django.urls import path
from . import views

urlpatterns = [
    path('', views.password_list, name='password_list'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('add/', views.add_password, name='add_password'),
    path('edit/<int:password_id>/', views.edit_password, name='edit_password'),
    path('delete/<int:password_id>/', views.delete_password, name='delete_password'),
    path('copy/<int:password_id>/', views.copy_password, name='copy_password'),
]
