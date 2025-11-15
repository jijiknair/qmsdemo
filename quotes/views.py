from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
import fitz 
# Create your views here.
# quotes/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import SignUpForm, LoginForm

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm, LoginForm

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.save()
            login(request, user)
            return redirect('login')
        else:
            print(form.errors)  # 👈 this will show you the reason in the terminal
            return render(request, 'quotes/signup.html', {'form': form})
    else:
        form = SignUpForm()
    return render(request, 'quotes/signup.html', {'form': form})

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")  # Role selected in the form

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check user's role (assuming it's stored in user.profile.role or user.role)
            # Replace 'profile.role' with your actual role field
            actual_role = getattr(user, 'role', None)  # if role is in User model
            # actual_role = user.profile.role  # if role is in a Profile model

            if actual_role == selected_role:
                login(request, user)

                # Redirect based on role
                if actual_role == "salesperson":
                    return redirect("salesperson_dashboard")
                elif actual_role == "admin":
                    return redirect("admin_dashboard")
                elif actual_role == "manager":
                    return redirect("manager_dashboard")
                else:
                    return redirect("salesperson_dashboard")
            else:
                messages.error(request, "Selected role does not match your account role.")
                return render(request, "quotes/login.html", {"error": "Role mismatch"})
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "quotes/login.html", {"error": "Invalid credentials"})

    return render(request, "quotes/login.html", {"error": error})




def logout_view(request):
    logout(request)
    return redirect("login")


def salesperson_dashboard(request):
    return render(request, "quotes/salesperson_dashboard.html")    

def dashboard_view(request):
    return render(request, 'quotes/dashboard.html')


def forgot_password(request):
    return render(request, "forgot_password.html")


# views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import fitz  # PyMuPDF
import io
from datetime import datetime


from datetime import datetime
from .models import QuotationCounter
def generate_qtn_number():
    year = datetime.now().year
    try:
        record = QuotationCounter.objects.get(year=year)
        record.counter += 1
        record.save()
    except QuotationCounter.DoesNotExist:
        record = QuotationCounter.objects.create(year=year, counter=1)

    number = str(record.counter).zfill(3)
    return f"QTN-{year}-{number}"



from .pdf_generator import generate_quotation_pdf
def create_quotation(request):
    if request.method == "POST":
        
        qtn_no = generate_qtn_number()   # you already completed this step

        data = {
            "qtn_no": qtn_no,
            "date": datetime.today().strftime("%d-%m-%Y"),
            "client_name": request.POST.get("client_name"),
            "client_company": request.POST.get("client_company"),
            "client_email": request.POST.get("client_email"),
            "client_phone": request.POST.get("client_phone"),
            "salesperson": request.user.username,
            "validity": request.POST.get("validity"),
            "delivery": request.POST.get("delivery"),
            "payment_terms": request.POST.get("payment_terms"),
            "warranty": request.POST.get("warranty"),
            "product_name": request.POST.getlist("product_name[]"),
            "pack_size": request.POST.getlist("pack_size[]"),
            "unit_price": request.POST.getlist("unit_price[]"),
        }

        pdf_file = generate_quotation_pdf(data)

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{qtn_no}.pdf"'
        return response

    return render(request, "quotes/create_quotation.html")


