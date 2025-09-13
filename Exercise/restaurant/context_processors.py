from .models import MenuItem

def cart_context(request):
    """Add cart information to all templates"""
    cart = request.session.get('cart', {})
    
    # Calculate total items in cart
    cart_count = sum(item['quantity'] for item in cart.values())
    
    # Calculate total price
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
        'has_cart_items': cart_count > 0
    }
