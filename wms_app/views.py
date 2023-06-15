from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.db.models import Count
from .models import *
import datetime

def get_greeting():
    current_hour = datetime.datetime.now().hour

    if 0 <= current_hour < 12:
        return "Good morning "
    elif 12 <= current_hour < 18:
        return "Good afternoon "
    else:
        return "Good evening "


# project landing page
def landing_view(request):
    return render(request, 'landing/index.html', {})

# login view
def login_view(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        user = authenticate(request, username=mobile, password=password)
        if user is not None:
            login(request, user)
            # get user status
            if user.is_superuser:
                return redirect('/dashboard')
            else:
                # get customer with user_id
                customer = Customer.objects.get(user=user)
                if int(customer.role) == 1:
                    # waste producer
                    return redirect('/producer_dashboard')
                else:
                    # waste collector
                    return redirect('/collector_dashboard')
                      
        else:
            # Invalid login credentials
            error_message = "Invalid mobile number or password"
            return render(request, 'dashboard/login.html', {'error_message': error_message})
    

    return render(request, 'dashboard/login.html')

#logout view
def logout_view(request):
    logout(request)
    return redirect('/') 

# Register View
def register_view(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        
        password = request.POST['pwd1']
        role = request.POST['role']
        address = request.POST['address']
        contact_number = request.POST['mobile']
        username = contact_number

        # Create User
        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        
        # Create Customer
        customer = Customer(user=user, role=role, address=address, contact_number=contact_number)
        customer.save()

        # create account
        account = Account(user=user)
        account.save()

        # Redirect to success page or home page
        return redirect('/login') 

    areas = Area.objects.all()

    return render(request, 'dashboard/register.html', {'areas': areas}) 

# function to get customers in an area
def get_customers_per_area(area_id):
    adr = str(area_id)
    customers = Customer.objects.filter(address=adr)
    return customers

# Dashboard View
def dashboard_view(request):
    context = {}
    areas = Area.objects.all()
    context['areas'] = areas
    area_data_list = []
    for area in areas:
        area_data = {}

        area_name = area.name
        area_requests = 1
        customers_in_area = len (get_customers_per_area(area.id))
        progress = 0
        if customers_in_area != 0:
            progress = (area_requests/customers_in_area) * 100
            progress = int(progress)
        f_progress = f"{progress} %"

        color = 'success'
        if progress > 25 and progress <= 50:
            color = 'info'
        elif progress > 50 and progress <= 75:
            color = 'warning'
        elif progress > 75:
            color = 'danger'

        area_data['name'] = area_name
        area_data['customers'] = customers_in_area
        area_data['requests'] = area_requests
        area_data['progress'] = f_progress
        area_data['counter'] = progress
        area_data['color'] = color

        area_data_list.append(area_data)
    context['area_data'] = area_data_list

    return render(request, 'dashboard/admin.html', context)


def address_view(request):
    areas = Area.objects.all()
    area_data = []
    for area in areas:
        customers_count = Customer.objects.filter(address=area.id).count()
        area_data.append({'area': area, 'customer_count': customers_count})

    return render(request, 'dashboard/address.html', {'area_data': area_data})
    

# Customer View
def customer_view(request):
    customers = Customer.objects.filter(role=1)
    customer_data = []
    for customer in customers:
        address_id = customer.address
        try:
            address = Area.objects.get(pk=address_id)
            address_name = address.name
        except Area.DoesNotExist:
            address_name = ''

        data = {
            'first_name': customer.user.first_name,
            'mobile': customer.contact_number,
            'role': customer.role,
            'address_name': address_name,
        }
        customer_data.append(data)

    context = {'customer_data': customer_data}
    return render(request, 'dashboard/customer.html', context)

# collectors View
def collector_view(request):
    customers = Customer.objects.filter(role=2)
    customer_data = []
    for customer in customers:
        address_id = customer.address
        try:
            address = Area.objects.get(pk=address_id)
            address_name = address.name
        except Area.DoesNotExist:
            address_name = ''

        data = {
            'first_name': customer.user.first_name,
            'mobile': customer.contact_number,
            'role': customer.role,
            'address_name': address_name,
        }
        customer_data.append(data)

    context = {'customer_data': customer_data}
    return render(request, 'dashboard/collector.html', context)


# Producer Dashboard View
def producer_dashboard_view(request):
    greetings = get_greeting() + request.user.first_name
    payments = Payment.objects.filter(waste_producer=request.user)
    if len(payments) == 0:
        payments = False

    context = {'greetings': greetings, 'payments': payments}
    return render(request, 'dashboard/producer.html', context)


def request_pickup_view(request):
    customer = Customer.objects.get(user = request.user)
    account = Account.objects.get(user = request.user)

    context = {'customer': customer, 'account': account}
    return render(request, 'dashboard/request.html', context)


# make payment view
def make_payment_view(request):
    customer = Customer.objects.get(user = request.user)
    account = Account.objects.get(user = request.user)
    context = {
        'customer': customer,
        'account': account
    }

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_type = request.POST.get('payment_type')


        payment = Payment(
            waste_producer=request.user,
            payment_date=datetime.date.today(),
            amount=float(amount),
            status=False,
            phone_number=phone_number,
            payment_method=payment_method,
            payment_type=payment_type
        )
        payment.save()

        # add balance in account to associated customer
        acc = Account.objects.get(user=request.user)
        acc.balance += int(amount)
        if int(payment_type) == 1:
            acc.montly = True
        else:
            acc.montly = False
            counts = int(acc.balance/5000)
            acc.request_count = counts
        acc.save()

        return redirect('/producer_dashboard')



    return render(request, 'dashboard/payment.html', context)




