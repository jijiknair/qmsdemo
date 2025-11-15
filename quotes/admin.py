from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, LoginIP

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Only show relevant columns in the list view
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']
    
    # Only relevant fields for editing/adding users
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff')}
        ),
    )

# quotes/admin.py
from django.contrib import admin
from .models import LoginIP

@admin.register(LoginIP)
class LoginIPAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'location', 'timestamp']  # include location
    list_filter = ['user', 'location', 'timestamp']  # filter by location as well
    search_fields = ['user__username', 'ip_address', 'location']  # searchable

