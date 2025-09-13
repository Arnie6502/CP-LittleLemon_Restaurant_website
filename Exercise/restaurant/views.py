from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .forms import BookingForm
from django.contrib import messages
from .models import Menu
from django.core import serializers
from .models import Booking, Menu
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def cart (request):
    return render(request, 'cart.html')

def reservations(request):
    all_bookings = Booking.objects.all().order_by('-reservation_date', 'reservation_slot')
    return render(request, 'reservations.html', {'bookings': all_bookings})

def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request, 'book.html', context)


@csrf_exempt
def bookings(request):
    print(f"DEBUG: Bookings view called with method: {request.method}")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"DEBUG: Received POST data: {data}")

            # Check if booking already exists
            exist = Booking.objects.filter(
                reservation_date=data['reservation_date'],
                reservation_slot=data['reservation_slot']
            ).exists()

            if not exist:
                booking = Booking(
                    first_name=data['first_name'],
                    reservation_date=data['reservation_date'],
                    reservation_slot=data['reservation_slot'],
                )
                booking.save()
                print(f"DEBUG: Booking saved: {booking}")
                return HttpResponse('{"success": 1}', content_type='application/json')
            else:
                print("DEBUG: Booking already exists")
                return HttpResponse('{"error": 1, "message": "Booking already exists"}', content_type='application/json')

        except Exception as e:
            print(f"DEBUG: Error in POST: {e}")
            return HttpResponse(f'{{"error": 1, "message": "{str(e)}"}}', content_type='application/json')

    # GET request - return bookings for a specific date
    try:
        date_str = request.GET.get('date', str(datetime.today().date()))
        print(f"DEBUG: Getting bookings for date: {date_str}")

        # Parse the date properly
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_obj = date_str

        bookings = Booking.objects.filter(reservation_date=date_obj)
        print(f"DEBUG: Found {bookings.count()} bookings")

        # Use Django's serializer to match JavaScript expectations
        booking_json = serializers.serialize('json', bookings)
        print(f"DEBUG: Returning serialized JSON: {booking_json}")
        
        return HttpResponse(booking_json, content_type='application/json')

    except Exception as e:
        print(f"DEBUG: Error in GET: {e}")
        return HttpResponse('[]', content_type='application/json')


def booking(request):
    return render(request, 'book.html')

def menu(request):
    menu_data = Menu.objects.all()
    print(f"DEBUG: Found {menu_data.count()} menu items")
    main_data = {"menu": menu_data}
    return render(request, 'menu.html', main_data)

def display_menu_item(request, pk=None): 
    if pk: 
        menu_item = Menu.objects.get(pk=pk) 
    else: 
        menu_item = "" 
    return render(request, 'menu_item.html', {"menu_item": menu_item}) 

@csrf_exempt
def some_view(request):
    return HttpResponse("Hello")

def add_to_cart(request, item_id):
    """Add item to cart"""
    if request.method == 'POST':
        menu_item = get_object_or_404(Menu, id=item_id)
        
        # Get quantity from form, default to 1
        quantity = int(request.POST.get('quantity', 1))
        
        # Check if enough inventory
        if quantity > menu_item.inventory:
            messages.error(request, f'Sorry, only {menu_item.inventory} items available.')
            return redirect('menu')
        
        # Get or create cart in session
        cart = request.session.get('cart', {})
        
        # Use the correct field name - check if your model has 'name' or 'title'
        item_name = getattr(menu_item, 'name', None) or getattr(menu_item, 'title', f'Item {menu_item.id}')
        
        # Add item to cart
        if str(item_id) in cart:
            cart[str(item_id)]['quantity'] += quantity
        else:
            cart[str(item_id)] = {
                'name': item_name,  # Use name instead of title
                'price': float(menu_item.price),
                'quantity': quantity,
                'image': menu_item.image.url if menu_item.image else None
            }
        
        # Save cart to session
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f'{item_name} added to cart!')
        return redirect('menu')
    
    return redirect('menu')


def view_cart(request):
    """Display cart contents"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for item_id, item_data in cart.items():
        subtotal = item_data['price'] * item_data['quantity']
        cart_items.append({
            'id': item_id,
            'name': item_data.get('name', item_data.get('title', 'Unknown Item')),  # Handle both name and title
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'subtotal': subtotal,
            'image': item_data.get('image')
        })
        total += subtotal
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(item['quantity'] for item in cart_items)
    }
    return render(request, 'cart.html', context)


def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart = request.session.get('cart', {})
    
    if str(item_id) in cart:
        removed_item = cart[str(item_id)]['title']
        del cart[str(item_id)]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f'{removed_item} removed from cart!')
    
    return redirect('view_cart')

def update_cart(request, item_id):
    """Update item quantity in cart"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        
        if str(item_id) in cart and quantity > 0:
            cart[str(item_id)]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, 'Cart updated!')
        elif quantity <= 0:
            return remove_from_cart(request, item_id)
    
    return redirect('view_cart')

def clear_cart(request):
    """Clear entire cart"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, 'Cart cleared!')
    return redirect('view_cart')