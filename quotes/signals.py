# quotes/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginIP
import requests

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_ip_location(ip):
    # Handle local IP for development
    if ip in ('127.0.0.1', '::1'):
        return "Localhost, Development"

    # Query external API for real IPs
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data['status'] == 'success':
            country = data.get('country', '')
            city = data.get('city', '')
            return f"{city}, {country}" if city else country
        return "Unknown"
    except requests.RequestException:
        return "Unknown"

@receiver(user_logged_in)
def save_login_ip(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    location = get_ip_location(ip)
    LoginIP.objects.create(user=user, ip_address=ip, location=location)
