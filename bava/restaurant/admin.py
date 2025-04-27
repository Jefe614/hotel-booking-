# restaurant/admin.py
from django.contrib import admin
from .models import MenuItem, Table, Reservation

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available')
    list_filter = ('category', 'available')
    search_fields = ('name', 'description')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('table_number',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'reservation_date', 'reservation_time', 'table', 'is_confirmed')
    list_filter = ('reservation_date', 'is_confirmed')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')