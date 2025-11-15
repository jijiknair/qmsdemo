# quotes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'), 
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('salesperson/dashboard/', views.salesperson_dashboard, name='salesperson_dashboard'),
    path('create-quotation/', views.create_quotation, name='create_quotation'),
]

