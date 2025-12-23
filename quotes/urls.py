from django.urls import path
from . import views
from .views import admin_dashboard

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('salesperson/dashboard/', views.salesperson_dashboard, name='salesperson_dashboard'),
    path('salesmanager/dashboard/', views.salesmanager_dashboard, name='salesmanager_dashboard'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),

    # Client Management
    path('clients/', views.client_management, name='client_management'),
    path('clients/add/', views.client_create, name='create_client'),
    path('clients/<int:id>/edit/', views.client_edit, name='edit_client'),
    path('clients/<int:id>/view/', views.client_view, name='view_client'),
    path('clients/<int:id>/delete/', views.client_delete, name='delete_client'),

    # Products
    path('products/', views.product_list, name='product_list'),
    

    # Quotation
    path('create/', views.create_quotation, name='create_quotation'),
    path('drafts/', views.draft_list, name='draft_list'),
    path('drafts/delete/<int:id>/', views.draft_delete, name='draft_delete'),
    path('drafts/resume/<int:id>/', views.draft_resume, name='resume_draft'),

    # My Quotations / Clients
    path('my_quotations/', views.my_quotations, name='my_quotations'),
    path('my_clients/', views.my_clients, name='my_clients'),

    # AJAX
    path("get-client-details/", views.get_client_details, name="get-client-details"),
    path("clients/add/ajax/", views.add_client_ajax, name="add_client_ajax"),
    path("clients/<int:id>/edit/ajax/", views.edit_client_ajax, name="edit_client_ajax"),
    path("clients/<int:id>/delete/ajax/", views.delete_client_ajax, name="delete_client_ajax"),
    path('quotation/send/<int:pk>/', views.send_for_approval, name='send_for_approval'),
    path('quotation/approve/<int:pk>/', views.approve_quotation, name='approve_quotation'),
    path("products/", views.product_list_view, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path('salesmanager/sales-team/', views.salesperson_list_view, name='salesperson_list'),
    path('my_quotations/', views.my_quotations, name='my_quotations'),
    path('salesmanager/quotations/', views.all_quotations_view, name='all_quotations'),
    path('salesmanager/quotation/<int:id>/reject/',views.reject_quotation,name='reject_quotation'),
    path('salespersons/edit/<int:id>/', views.salesperson_edit, name='salesperson_edit'),
    path('salespersons/delete/<int:id>/', views.salesperson_delete, name='salesperson_delete'),
    path('products/edit/<int:id>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:id>/', views.product_delete, name='product_delete'),
    path('admin/quotations/', views.admin_quotations, name='admin_quotations'),
    path('salesmanager/add-salesperson/', views.add_salesperson, name='add_salesperson'),
    path('products/add/', views.add_product, name='add_product'),
    path('sales-managers/add/',views.add_salesmanager,name='add_salesmanager'),
]




