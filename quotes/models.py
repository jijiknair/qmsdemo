from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -----------------------------------------------------
# COUNTRY
# -----------------------------------------------------
class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    currency = models.CharField(max_length=20)
    letterhead = models.FileField(upload_to="letterheads/", blank=True, null=True)

    def __str__(self):
        return self.name


# -----------------------------------------------------
# CUSTOM USER
# -----------------------------------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('salesmanager', 'Sales Manager'),
        ('salesperson', 'Salesperson'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesperson')
    country = models.CharField(max_length=100, blank=True, null=True)   # Oman, UAE etc.

    def __str__(self):
        return self.username


# -----------------------------------------------------
# LOGIN IP LOG
# -----------------------------------------------------
class LoginIP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.location}"


# -----------------------------------------------------
# CLIENT
# -----------------------------------------------------
class Client(models.Model):
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.company_name


# -----------------------------------------------------
# PRODUCT
# -----------------------------------------------------
class ProductNew(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    unit_price = models.DecimalField(max_digits=10, decimal_places=3)

    unit = models.CharField(max_length=50, default="Litre")   # Example: Litre, KG, Gallon
    pack_size = models.CharField(max_length=50, blank=True, null=True)  # Example: 5L, 20L, 200L

    country = models.CharField(max_length=50, default="Global")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.pack_size:
            return f"{self.name} - {self.pack_size}"
        return self.name



# -----------------------------------------------------
# INTRO TEXT
# -----------------------------------------------------
class IntroText(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# -----------------------------------------------------
# CLOSING TEXT (if client needs it)
# -----------------------------------------------------
class ClosingText(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# -----------------------------------------------------
# TERMS TEXT (for dropdown terms – requested by you)
# -----------------------------------------------------
class TermsText(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()

    def __str__(self):
        return self.title


# -----------------------------------------------------
# QUOTATION
# -----------------------------------------------------
class Quotation(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)

    # ⚠️ Stored as username (string) – matches your current system
    salesperson = models.CharField(max_length=255)

    intro_text = models.TextField(blank=True)
    closing_text = models.TextField(blank=True)
    terms_text = models.TextField(blank=True)

    products = models.JSONField(default=list)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Country & currency stored as text
    country = models.CharField(max_length=50, default="Oman")
    currency = models.CharField(max_length=10, default="OMR")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    date_created = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Quotation #{self.id} ({self.status})"

# -----------------------------------------------------
# COUNTER FOR QUOTATION NUMBERING
# -----------------------------------------------------
class QuotationCounter(models.Model):
    year = models.IntegerField()
    counter = models.IntegerField()

    def __str__(self):
        return f"{self.year}-{self.counter}"


# -----------------------------------------------------
# DRAFT QUOTATION STORAGE
# -----------------------------------------------------
import json
class DraftQuotation(models.Model):
    client_name = models.CharField(max_length=255)
    products_json = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)

    def products_list(self):
        try:
            return json.loads(self.products_json)
        except Exception:
            return []

    def __str__(self):
        return f"Draft #{self.id} - {self.client_name}"
