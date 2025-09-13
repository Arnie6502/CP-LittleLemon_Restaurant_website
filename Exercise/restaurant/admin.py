from django.contrib import admin
from .models import Menu, MenuItem, Booking

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'image']
    list_filter = ['price']
    search_fields = ['name']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'reservation_date', 'reservation_slot']
    list_filter = ['reservation_date']
    search_fields = ['first_name']
