from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings  

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('salesperson', 'Salesperson'),
        ('manager', 'Sales Manager'),
        ('admin', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesperson')

    def __str__(self):
        return f"{self.username} ({self.role})"

from django.db import models
from django.conf import settings

class LoginIP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)  # New field
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.location} - {self.timestamp}"



class Quotation(models.Model):
    client_name = models.CharField(max_length=200)
    client_company = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    date_created = models.DateField(auto_now_add=True)
    valid_until = models.DateField()
    payment_terms = models.CharField(max_length=200)
    salesperson = models.CharField(max_length=100)
    # products can be handled as JSON or a separate model
    products = models.JSONField()  
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # New fields for dynamic sections
    validity = models.CharField(max_length=50, default="30 days")
    delivery = models.CharField(max_length=50, default="Immediate")
    warranty = models.CharField(max_length=50, blank=True)
    shipping = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.client_company} - {self.client_name} - {self.date_created}"



class QuotationCounter(models.Model):
    year = models.IntegerField()
    counter = models.IntegerField()

    def __str__(self):
        return f"{self.year}-{self.counter}"
