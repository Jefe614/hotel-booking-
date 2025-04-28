# restaurant/views.py
import json
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import MenuItem, Table, Reservation
from .forms import ReservationForm, MenuItemForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import datetime
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests



def home(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def menu(request):
    menu_items = MenuItem.objects.filter(available=True).order_by('category', 'name')
    categories = MenuItem.objects.values_list('category', flat=True).distinct().order_by('category')
    return render(request, 'menu.html', {
        'menu_items': menu_items,
        'categories': categories
    })
@login_required(login_url='login')
def book_table(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            # Set confirmed to false until payment is made
            reservation.is_confirmed = False
            reservation.save()
            
            # Store the reservation ID in session for the payment process
            request.session['pending_reservation_id'] = reservation.id
            
            if request.POST.get('payment_method') == 'mpesa':
                # Redirect to payment page or process M-Pesa payment
                return redirect('payment_page', reservation_id=reservation.id)
            else:
                # Cash payment option (handled at the restaurant)
                reservation.payment_method = 'cash'
                reservation.save()
                return redirect('booking_success', reservation_id=reservation.id)
    else:
        form = ReservationForm()
    
    return render(request, 'book.html', {
        'form': form,
        'form_errors': form.errors if request.method == 'POST' else None,
        'deposit_amount': settings.TABLE_RESERVATION_DEPOSIT  # Set this in settings.py
    })

@login_required(login_url='login')
def booking_success(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    if reservation.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this reservation.")
        return redirect('home')
    return render(request, 'booking_success.html', {'reservation': reservation})

@login_required(login_url='login')
def manage(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the management page.")
        return redirect('home')
    
    today = timezone.now().date()
    reservations = Reservation.objects.all().order_by('reservation_date', 'reservation_time')
    today_reservations = reservations.filter(reservation_date=today)
    confirmed_reservations = reservations.filter(is_confirmed=True)
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    
    if request.method == 'POST':
        menu_form = MenuItemForm(request.POST, request.FILES)
        if menu_form.is_valid():
            menu_item = menu_form.save()
            messages.success(request, f"Menu item '{menu_item.name}' added successfully!")
            return redirect('manage')
        else:
            # Print form errors to console for debugging
            print("Form errors:", menu_form.errors)
            for field, errors in menu_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        menu_form = MenuItemForm()
    
    return render(request, 'manage.html', {
        'reservations': reservations,
        'today_reservations': today_reservations,
        'confirmed_reservations': confirmed_reservations,
        'menu_items': menu_items,
        'menu_form': menu_form
    })

# User authentication views
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Get the next parameter value or default to home
                next_page = request.GET.get('next', 'home')
                messages.success(request, f"Welcome back, {username}!")
                return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    # Style form inputs (not needed with custom inputs in template)
    # form.fields['username'].widget.attrs.update({'class': 'form-control'})
    # form.fields['password'].widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Bava Restaurant, {user.username}! Your account has been created successfully.")
            return redirect('login')
    else:
        form = UserCreationForm()
    
    # Style form inputs (not needed with custom inputs in template)
    # form.fields['username'].widget.attrs.update({'class': 'form-control'})
    # form.fields['password1'].widget.attrs.update({'class': 'form-control'})
    # form.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'signup.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@csrf_exempt
def mpesa_stk_push(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        phone = data.get('phone')
        amount = data.get('amount')
        reservation_id = data.get('reservation_id')

        if not phone or not amount:
            return JsonResponse({'success': False, 'error': 'Missing phone or amount'})

        # --- Start Mpesa logic here ---
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        shortcode = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        callback_url = settings.MPESA_CALLBACK_URL

        # Get access token
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(auth_url, auth=(consumer_key, consumer_secret))
        access_token = auth_response.json().get('access_token')

        # Timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

        stk_push_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "Bava Restaurant",
            "TransactionDesc": "Table Reservation Deposit"
        }

        response = requests.post(stk_push_url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            # Store reservation ID and amount for callback verification
            if reservation_id:
                try:
                    reservation = Reservation.objects.get(id=reservation_id)
                    reservation.deposit_amount = amount
                    reservation.payment_method = 'mpesa'
                    reservation.payment_status = 'pending'
                    # You might want to store CheckoutRequestID for verification
                    if 'CheckoutRequestID' in response_data:
                        reservation.transaction_id = response_data['CheckoutRequestID']
                    reservation.save()
                except Reservation.DoesNotExist:
                    pass
                
            return JsonResponse({'success': True, 'response': response_data})
        else:
            return JsonResponse({'success': False, 'error': response_data})
        
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        # Parse the callback data
        try:
            data = json.loads(request.body)
            # Get the relevant payment details
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            
            # Find the reservation with this checkout request ID
            try:
                reservation = Reservation.objects.get(transaction_id=checkout_request_id)
                
                if result_code == 0:  # Success
                    reservation.payment_status = 'paid'
                    reservation.is_confirmed = True
                    reservation.save()
                    # You could send a confirmation email here
                else:
                    reservation.payment_status = 'failed'
                    reservation.save()
                    
                return JsonResponse({'status': 'success'})
                
            except Reservation.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Reservation not found'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'failure', 'message': 'Invalid request method'})


@login_required(login_url='login')
def payment_page(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        
        # Set the deposit amount (you can calculate this based on table size, etc.)
        deposit_amount = settings.TABLE_RESERVATION_DEPOSIT
        
        return render(request, 'payment.html', {
            'reservation': reservation,
            'deposit_amount': deposit_amount
        })
    except Reservation.DoesNotExist:
        messages.error(request, "Reservation not found or you don't have permission to access it.")
        return redirect('home')
    

@login_required(login_url='login')
def payment_status(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        return render(request, 'payment_status.html', {
            'reservation': reservation
        })
    except Reservation.DoesNotExist:
        messages.error(request, "Reservation not found or you don't have permission to access it.")
        return redirect('home')