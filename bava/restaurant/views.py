# restaurant/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import MenuItem, Table, Reservation
from .forms import ReservationForm, MenuItemForm

def home(request):
    return render(request, 'home.html')

def menu(request):
    menu_items = MenuItem.objects.filter(available=True).order_by('category', 'name')
    categories = MenuItem.objects.values_list('category', flat=True).distinct().order_by('category')
    return render(request, 'menu.html', {
        'menu_items': menu_items,
        'categories': categories
    })

def book_table(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.is_confirmed = True
            reservation.save()
            
            # Mark the table as unavailable if needed
            # (or implement a more complex availability logic)
            # reservation.table.is_available = False
            # reservation.table.save()
            
            return redirect('booking_success', reservation_id=reservation.id)
    else:
        form = ReservationForm()
    
    # Pass form errors to template if any
    return render(request, 'book.html', {
        'form': form,
        'form_errors': form.errors if request.method == 'POST' else None
    })

def booking_success(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    return render(request, 'booking_success.html', {'reservation': reservation})

def manage(request):
    if not request.user.is_authenticated:
        return redirect('admin:login')
    
    today = timezone.now().date()
    reservations = Reservation.objects.all().order_by('reservation_date', 'reservation_time')
    today_reservations = reservations.filter(reservation_date=today)
    confirmed_reservations = reservations.filter(is_confirmed=True)
    menu_items = MenuItem.objects.all().order_by('category', 'name')
    
    if request.method == 'POST':
        menu_form = MenuItemForm(request.POST)
        if menu_form.is_valid():
            menu_form.save()
            return redirect('manage')
    else:
        menu_form = MenuItemForm()
    
    return render(request, 'manage.html', {
        'reservations': reservations,
        'today_reservations': today_reservations,
        'confirmed_reservations': confirmed_reservations,
        'menu_items': menu_items,
        'menu_form': menu_form
    })