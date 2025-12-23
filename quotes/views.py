# ==========================
#   IMPORTS
# ==========================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from datetime import datetime, date
import json
from .models import IntroText, ClosingText,ProductNew

# MODELS
from .models import (
    CustomUser, Client, Quotation,
    LoginIP, Country, QuotationCounter, DraftQuotation,
    ProductNew,   # ← REPLACED Product
    IntroText, ClosingText
)

# FORMS
from .forms import SignUpForm, LoginForm

# PDF
from .pdf_generator import generate_quotation_pdf


# ==========================
#   AUTHENTICATION
# ==========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.role == "admin":
                return redirect("admin_dashboard")
            elif user.role == "salesmanager":
                return redirect("salesmanager_dashboard")
            elif user.role == "salesperson":
                return redirect("salesperson_dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "quotes/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ==========================
#   QUOTATION NUMBER GENERATOR
# ==========================
def generate_qtn_number():
    year = datetime.now().year
    try:
        record = QuotationCounter.objects.get(year=year)
        record.counter += 1
        record.save()
    except QuotationCounter.DoesNotExist:
        record = QuotationCounter.objects.create(year=year, counter=1)

    return f"QTN-{year}-{str(record.counter).zfill(3)}"


# ==========================
#   CLIENT MANAGEMENT
# ==========================
@login_required
def client_management(request):
    user = request.user

    if user.role == "salesperson":
        clients = Client.objects.filter(salesperson=user)
    else:
        clients = Client.objects.all()

    return render(request, "quotes/client_management.html", {"clients": clients})

@login_required
def client_create(request):
    if request.method == "POST":
        Client.objects.create(
            company_name=request.POST.get("company_name"),
            contact_person=request.POST.get("contact_person"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            salesperson=request.user
        )
        return redirect("client_management")

    return render(request, "quotes/client_create.html")

@login_required
def client_edit(request, id):
    client = get_object_or_404(Client, id=id)

    if request.user.role == "salesperson" and client.salesperson != request.user:
        return redirect("client_management")

    if request.method == "POST":
        client.company_name = request.POST.get("company_name")
        client.contact_person = request.POST.get("contact_person")
        client.email = request.POST.get("email")
        client.phone = request.POST.get("phone")
        client.address = request.POST.get("address")
        client.save()

        return redirect("client_management")

    return render(request, "quotes/client_edit.html", {"client": client})


@login_required
def client_view(request, id):
    client = get_object_or_404(Client, id=id)

    if request.user.role == "salesperson" and client.salesperson != request.user:
        return redirect("client_management")

    return render(request, "quotes/client_view.html", {"client": client})


@login_required
def client_delete(request, id):
    client = get_object_or_404(Client, id=id)

    if request.user.role == "salesperson" and client.salesperson != request.user:
        return redirect("client_management")

    if request.method == "POST":
        client.delete()
        return redirect("client_management")

    return render(request, "quotes/client_delete_confirm.html", {"client": client})



# AJAX — Get client details
@login_required
def get_client_details(request):
    company_name = request.GET.get("company")

    try:
        client = Client.objects.get(
            company_name=company_name,
            salesperson=request.user  # 🔥 important
        )
        return JsonResponse({
            "contact_person": client.contact_person,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
        })
    except Client.DoesNotExist:
        return JsonResponse({"error": "Client not found"}, status=404)

#=================================
# Products Section


@login_required
def product_list_view(request):
    products = ProductNew.objects.filter(
        Q(country=request.user.country) | Q(country="Global")
    )
    return render(request, "quotes/product_list.html", {
        "products": products
    })


def product_detail(request, pk):
    product = get_object_or_404(ProductNew, pk=pk)
    return render(request, "quotes/product_detail.html", {
        "product": product
    })


# ================================
#     CREATE QUOTATION
# ================================
@login_required
def create_quotation(request, id=None):
    draft = None

    # =========================
    # EDIT MODE
    # =========================
    if id:
        draft = get_object_or_404(
            Quotation,
            id=id,
            salesperson=request.user.username
        )

        # 🔒 Lock edit if not draft
        if draft.status != 'draft':
            messages.error(request, "Quotation already sent. Editing locked.")
            return redirect('my_quotations')

    # =========================
    # POST
    # =========================
    if request.method == "POST":
        action = request.POST.get("action")

        # 🔒 REQUIRED FIELD VALIDATION
        client_id = request.POST.get("client_id")
        intro_text = request.POST.get("intro_text", "").strip()
        closing_text = request.POST.get("closing_text", "").strip()
        product_ids = request.POST.getlist("product_id[]")

        if not client_id:
            messages.error(request, "Please select a client.")
            return redirect(request.path)

        if not intro_text:
            messages.error(request, "Opening text is required.")
            return redirect(request.path)

        if not closing_text:
            messages.error(request, "Closing text is required.")
            return redirect(request.path)

        # remove empty product ids
        product_ids = [pid for pid in product_ids if pid]

        if not product_ids:
            messages.error(request, "Please add at least one product.")
            return redirect(request.path)

        # ✅ SAFE TO CONTINUE
        client = get_object_or_404(Client, id=client_id)

        # Product fields
        descs = request.POST.getlist("desc")
        pack_sizes = request.POST.getlist("pack_size")
        unit_prices = request.POST.getlist("unit_price[]")
        discounts = request.POST.getlist("discount[]")
        qtys = request.POST.getlist("qty[]")
        totals = request.POST.getlist("total[]")
        validity = request.POST.get("validity", 30)
        delivery = request.POST.get("delivery", "7 Days")
        payment_terms = request.POST.get("payment_terms", "Advance Payment")

        products = []
        subtotal = 0

        for pid, desc, pack, price, disc, qty, total in zip(
            product_ids, descs, pack_sizes, unit_prices, discounts, qtys, totals
        ):
            product_obj = ProductNew.objects.get(id=pid)

            line_total = float(total or 0)
            subtotal += line_total

            products.append({
                "name": product_obj.name,
                "desc": desc,
                "pack_size": pack,
                "unit_price": float(price or 0),
                "discount": float(disc or 0),
                "qty": int(qty or 1),
                "total": line_total,
            })

        vat = round(subtotal * 0.05, 3)
        grand_total = subtotal + vat

        quotation = draft if draft else Quotation()

        quotation.client = client
        quotation.salesperson = request.user.username
        quotation.products = products
        quotation.subtotal = subtotal
        quotation.vat = vat
        quotation.total_amount = grand_total
        quotation.country = request.user.country
        quotation.currency = "OMR"
        quotation.status = "draft"   # always draft here
        quotation.valid_until = date.today()
        quotation.save()

        if action == "preview":
            pdf = generate_quotation_pdf({
                "date": date.today().strftime("%d-%m-%Y"),
                "qtn_no": f"QTN-{quotation.id}",
                "client_company": client.company_name,
                "client_email": client.email,
                "client_name": client.contact_person,
                "client_phone": client.phone,
                "products": products,
                "subtotal": subtotal,
                "vat": vat,
                "grand_total": grand_total,
                "salesperson": quotation.salesperson,
                "validity": validity,
                "delivery":delivery,
                "payment_terms": payment_terms,
                
            })
            return HttpResponse(pdf, content_type="application/pdf")

        return redirect("draft_list")

    # =========================
    # GET
    # =========================
    if request.user.role == "admin":
        products = ProductNew.objects.all()
    else:
        products = ProductNew.objects.filter(
            Q(country=request.user.country) | Q(country="Global")
        )

    return render(request, "quotes/create_quotation.html", {
        "clients": Client.objects.all(),
        "products": products,
        "draft": draft,
        "intro_texts": IntroText.objects.all(),
        "closing_texts": ClosingText.objects.all(),
    })



# ================================
#           DRAFT QUOTATIONS
# ================================
@login_required
def draft_list(request):
    drafts = Quotation.objects.filter(
        status="draft",
        salesperson=request.user.username
    ).order_by("-date_created")

    return render(request, "quotes/draft.html", {"drafts": drafts})


@login_required
def draft_delete(request, id):
    draft = get_object_or_404(Quotation, id=id, salesperson=request.user.username)
    draft.delete()
    return redirect("draft_list")


@login_required
def draft_resume(request, id):
    draft = get_object_or_404(Quotation, id=id, salesperson=request.user.username)

    return render(request, "quotes/create_quotation.html", {
        "draft": draft,
        "clients": Client.objects.filter(salesperson=request.user),
        "products": ProductNew.objects.all(),
    })


# ================================
#           DASHBOARDS
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Quotation

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Quotation

@login_required
def salesperson_dashboard(request):
    user = request.user

    # Correct field from your model
    qs = Quotation.objects.filter(salesperson=user)

    total_quotations = qs.count()
    sent_quotations = qs.filter(status='sent').count()
    approved_quotations = qs.filter(status='approved').count()
    draft_quotations = qs.filter(status='draft').count()

    # Safe conversion calculation
    conversion_rate = round(
        (approved_quotations / sent_quotations) * 100, 1
    ) if sent_quotations > 0 else 0

    # Temporary chart data (trial hosting safe)
    monthly_data = [1, 2, 3, 4, 5, 3, 6, 7, 5, 6, 8, 9]
    status_data = [approved_quotations, sent_quotations, draft_quotations]

    context = {
        'total_quotations': total_quotations,
        'sent_quotations': sent_quotations,
        'approved_quotations': approved_quotations,
        'conversion_rate': conversion_rate,
        'monthly_data': monthly_data,
        'status_data': status_data,
        'recent_quotations': qs.order_by('-date_created')[:5],
    }

    return render(request, "quotes/salesperson_dashboard.html", context)




from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from django.contrib.auth import get_user_model
from .models import Quotation

User = get_user_model()

from django.db.models import Count
@login_required
def salesmanager_dashboard(request):
    if request.user.role != 'salesmanager':
        return redirect('salesperson_dashboard')
    # KPIs
    total_quotations = Quotation.objects.count()
    pending_approval = Quotation.objects.filter(status='sent').count()
    approved_count = Quotation.objects.filter(status='approved').count()

    total_salespersons = User.objects.filter(role='salesperson').count()

    # Recent quotations
    recent_quotations = Quotation.objects.select_related('client').order_by('-date_created')[:5]

    # 🔥 Salesperson vs Quotations (GRAPH DATA)
    salesperson_data = (
        Quotation.objects
        .values('salesperson')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    salesperson_labels = [item['salesperson'] for item in salesperson_data]
    salesperson_totals = [item['total'] for item in salesperson_data]
    # 🔥 Quotation Status Distribution (GRAPH DATA)
    status_data = (
    Quotation.objects
    .values('status')
    .annotate(total=Count('id'))
    )

    status_labels = [item['status'] for item in status_data if item['status']]
    status_totals = [item['total'] for item in status_data]

    context = {
        'total_quotations': total_quotations,
        'pending_approval': pending_approval,
        'approved_count': approved_count,
        'total_salespersons': total_salespersons,
        'recent_quotations': recent_quotations,
        'salesperson_labels': salesperson_labels,
        'salesperson_totals': salesperson_totals,
        'status_labels': status_labels,
        'status_totals': status_totals,
    }

    return render(request, 'quotes/salesmanager_dashboard.html', context)


from datetime import date
from django.contrib.auth.decorators import login_required
from django.db.models import Count

@login_required
def admin_dashboard(request):
    today = date.today()

    # ---------------- Country Salespersons ----------------
    country_sales_raw = (
        CustomUser.objects.filter(role="salesperson")
        .values("country")
        .annotate(total=Count("id"))
    )

    FLAG = {"Oman": "🇴🇲", "UAE": "🇦🇪", "India": "🇮🇳"}
    CURRENCY = {"Oman": "OMR", "UAE": "AED", "India": "INR"}

    country_sales = [
        {
            "name": c["country"],
            "flag": FLAG.get(c["country"], "🌍"),
            "currency": CURRENCY.get(c["country"], "—"),
            "count": c["total"],
        }
        for c in country_sales_raw
    ]

    # ---------------- Status Distribution (GRAPH 1) ----------------
    status_data = (
        Quotation.objects
        .values("status")
        .annotate(total=Count("id"))
    )

    status_labels = [s["status"] for s in status_data]
    status_totals = [s["total"] for s in status_data]

    # ---------------- Salesperson vs Quotations (GRAPH 2) ----------------
    salesperson_data = (
        Quotation.objects
        .values("salesperson")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    salesperson_labels = [s["salesperson"] for s in salesperson_data]
    salesperson_totals = [s["total"] for s in salesperson_data]

    # ---------------- RENDER ----------------
    return render(request, "quotes/admin_dashboard.html", {
        # Cards / KPIs
        "country_sales": country_sales,
        "managers": CustomUser.objects.filter(role="salesmanager").count(),
        "admins": CustomUser.objects.filter(role="admin").count(),
        "total_clients": Client.objects.count(),
        "total_products": ProductNew.objects.count(),
        "total_quotations": Quotation.objects.count(),
        "today_quotations": Quotation.objects.filter(date_created=today).count(),
        "recent_logins": LoginIP.objects.all().order_by("-timestamp")[:10],

        # ✅ GRAPH DATA (THIS WAS MISSING)
        "status_labels": status_labels,
        "status_totals": status_totals,
        "salesperson_labels": salesperson_labels,
        "salesperson_totals": salesperson_totals,
    })



# ================================
#      MY QUOTATIONS / CLIENTS
# ================================
@login_required
def my_quotations(request):
    user = request.user

    # ADMIN → see all quotations
    if user.role == 'admin':
        quotations = Quotation.objects.all().order_by('-date_created')

    # SALES MANAGER → see all quotations
    elif user.role == 'salesmanager':
        quotations = Quotation.objects.all().order_by('-date_created')

    # SALESPERSON → only their quotations
    else:
        quotations = Quotation.objects.filter(
            salesperson=user.username
        ).order_by('-date_created')

    return render(
        request,
        "quotes/my_quotations.html",
        {"quotations": quotations}
    )



@login_required
def my_clients(request):
    client_ids = Quotation.objects.filter(
        salesperson=request.user.username
    ).values_list("client_id", flat=True).distinct()

    clients = Client.objects.filter(id__in=client_ids)

    return render(request, "quotes/my_clients.html", {"clients": clients})


# ================================
#         AJAX CLIENT APIs
# ================================
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def add_client_ajax(request):
    if request.method == "POST":
        data = json.loads(request.body)

        client = Client.objects.create(
            company_name=data["company_name"],
            contact_person=data["contact_person"],
            email=data["email"],
            phone=data["phone"],
            address=data["address"],
            salesperson=request.user
        )

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "invalid"}, status=400)


@csrf_exempt
def edit_client_ajax(request, id):
    if request.method == "POST":
        data = json.loads(request.body)

        client = Client.objects.get(id=id)
        client.company_name = data["company_name"]
        client.contact_person = data["contact_person"]
        client.email = data["email"]
        client.phone = data["phone"]
        client.address = data["address"]
        client.save()

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "invalid"}, status=400)


@csrf_exempt
def delete_client_ajax(request, id):
    if request.method == "DELETE":
        Client.objects.get(id=id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "invalid method"}, status=400)


from django.shortcuts import render
from .models import ProductNew   # adjust if model name is different

def product_list(request):
    products = ProductNew.objects.all()
    return render(request, 'quotes/product_list.html', {
        'products': products
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quotation

@login_required
def send_for_approval(request, pk):
    quotation = get_object_or_404(
        Quotation,
        pk=pk,
        salesperson=request.user.username  # ✅ STRING MATCH
    )

    if quotation.status == 'draft':
        quotation.status = 'sent'
        quotation.save()
        messages.success(request, "Quotation sent for approval.")

    return redirect('my_quotations')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quotation

@login_required
def send_for_approval(request, pk):
    quotation = get_object_or_404(
        Quotation,
        pk=pk,
        salesperson=request.user.username  # ✅ STRING MATCH
    )

    if quotation.status == 'draft':
        quotation.status = 'sent'
        quotation.save()
        messages.success(request, "Quotation sent for approval.")

    return redirect('my_quotations')

@login_required
def approve_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)

    if quotation.status == 'sent':
        quotation.status = 'approved'
        quotation.save()
        messages.success(request, "Quotation approved.")

    return redirect('salesmanager_dashboard')


from django.shortcuts import render
from .models import CustomUser   # adjust app name if different

def salesperson_list_view(request):

    selected_country = request.GET.get('country', '')

    salespersons = CustomUser.objects.filter(role='salesperson')

    # ✅ Build country list properly
    countries = (
        CustomUser.objects
        .filter(role='salesperson')
        .exclude(country__isnull=True)
        .exclude(country='')
        .values_list('country', flat=True)
        .distinct()
    )

    # ✅ Apply filter if selected
    if selected_country:
        salespersons = salespersons.filter(country=selected_country)

    context = {
        'salespersons': salespersons,
        'countries': countries,
        'selected_country': selected_country,
    }

    return render(
        request,
        'quotes/salesperson_list.html',
        context
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Quotation


@login_required
def all_quotations_view(request):
    if request.user.role != 'salesmanager':
        return redirect('salesperson_dashboard')

    quotations = Quotation.objects.all().order_by("-date_created")

    return render(
        request,
        "quotes/my_quotations.html",   # ✅ SAME TEMPLATE
        {"quotations": quotations}
    )
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Quotation


@login_required
def reject_quotation(request, id):
    if request.user.role != 'salesmanager':
        return redirect('salesperson_dashboard')

    quotation = get_object_or_404(Quotation, id=id)
    quotation.status = 'rejected'
    quotation.save()

    return redirect('all_quotations')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Country


@login_required
def salesperson_edit(request, id):

    # 🔐 ADMIN ONLY
    if request.user.role != 'admin':
        return redirect('salesperson_list')

    salesperson = get_object_or_404(CustomUser, id=id, role='salesperson')

    # ✅ THIS LINE IS CRITICAL
    countries = Country.objects.all()

    if request.method == "POST":
        salesperson.first_name = request.POST.get("first_name")
        salesperson.last_name = request.POST.get("last_name")
        salesperson.email = request.POST.get("email")
        salesperson.country = request.POST.get("country")
        salesperson.save()

        return redirect('salesperson_list')

    return render(
        request,
        "quotes/salesperson_edit.html",
        {
            "user": salesperson,     # matches {{ user.country }}
            "countries": countries   # REQUIRED for dropdown
        }
    )

@login_required
def salesperson_delete(request, id):
    if request.user.role != 'admin':
        return redirect('salesperson_list')

    salesperson = get_object_or_404(CustomUser, id=id, role='salesperson')
    salesperson.delete()

    return redirect('salesperson_list')


@login_required
def product_edit(request, id):
    if request.user.role != 'admin':
        return redirect('product_list')

    product = get_object_or_404(ProductNew, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.unit_price = request.POST.get("unit_price")
        product.unit = request.POST.get("unit")
        product.save()

        return redirect('product_list')

    return render(request, 'quotes/product_edit.html', {
        'product': product
    })

@login_required
def product_delete(request, id):
    if request.user.role != 'admin':
        return redirect('product_list')

    product = get_object_or_404(ProductNew, id=id)

    if request.method == "POST":
        product.delete()
        return redirect('product_list')

    return render(request, 'quotes/product_deleteconfirm.html', {
        'product': product
    })

@login_required
def admin_quotations(request):
    if request.user.role != 'admin':
        return redirect('salesperson_dashboard')

    quotations = Quotation.objects.select_related(
        'client'
    ).order_by('-date_created')

    return render(request, 'quotes/my_quotations.html', {
        'quotations': quotations
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import CustomUser


@login_required
def add_salesperson(request):

    # 🔒 Only admin allowed
    if request.user.role != 'admin':
        messages.error(request, "Unauthorized access")
        return redirect('salespersons_list')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        country    = request.POST.get('country')
        password   = request.POST.get('password')

        # ❌ Duplicate check
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('add_salesperson')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('add_salesperson')

        # ✅ Create salesperson
        CustomUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            country=country,
            role='salesperson',
            is_active=True,
            password=make_password(password)
        )

        messages.success(request, "Salesperson added successfully")
        return redirect('salesperson_list')

    return render(request, 'quotes/add_salesperson.html')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ProductNew

@login_required
def add_product(request):
    if request.method == "POST":
        ProductNew.objects.create(
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            unit_price=request.POST.get("unit_price"),
            unit=request.POST.get("unit"),
            pack_size=request.POST.get("pack_size"),
            country=request.POST.get("country"),
        )
        return redirect('product_list')

    return render(request, "quotes/add_product.html")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser


@login_required
def add_salesmanager(request):
    # Only admin can add sales managers
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        country    = request.POST.get('country')
        password   = request.POST.get('password')

        # 🔒 Validation
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('add_salesmanager')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('add_salesmanager')

        # ✅ Create Sales Manager
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        user.role = 'salesmanager'
        user.country = country
        user.is_active = True
        user.save()

        messages.success(request, 'Sales Manager added successfully')

        # 🔁 Redirect after success
        return redirect('admin_dashboard')  
        # OR redirect('salesmanager_list') if you create that page later

    # GET request → show form
    return render(request, 'quotes/add_salesmanager.html')


