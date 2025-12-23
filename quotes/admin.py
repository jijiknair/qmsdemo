from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser,
    LoginIP,
    Client,
    Quotation,
    Country,
    IntroText,
    ClosingText,
    TermsText,
    QuotationCounter,
    DraftQuotation,
    ProductNew,     # ← NEW MODEL ADDED HERE
)


# ============================
# Custom User Admin
# ============================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ["username", "email", "role", "country", "is_active"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "country")}),
        ("Role & Status", {"fields": ("role", "is_active", "is_staff")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "first_name", "last_name",
                "email", "country", "role",
                "password1", "password2",
                "is_staff", "is_active",
            ),
        }),
    )

    search_fields = ("username", "email")
    ordering = ("username",)


# ============================
# LoginIP
# ============================
@admin.register(LoginIP)
class LoginIPAdmin(admin.ModelAdmin):
    list_display = ["user", "ip_address", "location", "timestamp"]
    list_filter = ["user", "location", "timestamp"]
    search_fields = ["user__username", "ip_address", "location"]


# ============================
# Client & Quotation
# ============================
admin.site.register(Client)
admin.site.register(Quotation)


# ============================
# Custom Admin Dashboard
# ============================
class CustomAdminSite(admin.AdminSite):
    site_header = "QMS Admin"
    site_title = "QMS Admin Panel"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        User = get_user_model()
        extra_context = extra_context or {}

        extra_context.update({
            "user_count": User.objects.count(),
            "manager_count": User.objects.filter(role="salesmanager").count(),
            "salesperson_count": User.objects.filter(role="salesperson").count(),
            "client_count": Client.objects.count(),
            "quotation_count": Quotation.objects.count(),
            "pending_quotations": Quotation.objects.filter(status="pending").count(),
            "sent_quotations": Quotation.objects.filter(status="sent").count(),
        })

        return super().index(request, extra_context=extra_context)


admin_site = CustomAdminSite(name="custom_admin")


# ============================
# Text Templates
# ============================
@admin.register(IntroText)
class IntroTextAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_approved")
    list_filter = ("is_approved",)
    search_fields = ("title", "text")


@admin.register(ClosingText)
class ClosingTextAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_approved")
    list_filter = ("is_approved",)
    search_fields = ("title", "text")


# ============================
# PRODUCTNEW ADMIN
# ============================
@admin.register(ProductNew)
class ProductNewAdmin(admin.ModelAdmin):
    list_display = ("name", "pack_size", "unit_price", "unit", "country", "created_at")
    search_fields = ("name", "pack_size", "country")
    list_filter = ("country", "unit")

from django.contrib import admin
from .models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "letterhead")
    search_fields = ("name", "currency")
    ordering = ("name",)