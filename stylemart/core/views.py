import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Product, Category, Cart, Order, OrderItem
from .forms import SignupForm, LoginForm
from .jazzcash_utils import build_payment_payload


# ==================== HOME & CORE PAGES ====================

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(badge__isnull=False).order_by("?")[:8]
    all_products = Product.objects.order_by("?")[:20]
    return render(request, "home.html", {
        "categories": categories,
        "featured_products": featured_products,
        "all_products": all_products,
    })


def help_center(request):
    """Displays the Help Center or FAQ page."""
    return render(request, "help_center.html")


# ==================== AUTHENTICATION ====================

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created and logged in.")
            return redirect("home")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignupForm()
    return render(request, "auth/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, "auth/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out.")
    return redirect("home")


# ==================== PRODUCTS & CATEGORIES ====================

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    category_slug = request.GET.get("category")
    sort = request.GET.get("sort")
    price_range = request.GET.get("price")

    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Price filter
    if price_range == "under25000":
        products = products.filter(price__lt=25000)
    elif price_range == "25000_100000":
        products = products.filter(price__gte=25000, price__lte=100000)
    elif price_range == "100000_200000":
        products = products.filter(price__gte=100000, price__lte=200000)
    elif price_range == "over200000":
        products = products.filter(price__gt=200000)

    # Sorting logic
    if sort == "price_low":
        products = products.order_by("price")
    elif sort == "price_high":
        products = products.order_by("-price")
    else:
        # Changed from '-is_featured' to '-created_at' to prevent FieldError
        # This will show the newest products first by default
        products = products.order_by("-created_at")

    return render(request, "products/product_list.html", {
        "products": products,
        "categories": categories,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_to_cart":
            return add_to_cart(request, product_id=product.id)
        elif action == "order_now":
            if request.user.is_authenticated:
                cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                return redirect("place_order")
            else:
                messages.info(request, "Please login to order.")
                return redirect("login")

    return render(request, "product_detail.html", {"product": product})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, "category_detail.html", {
        "category": category,
        "products": products,
    })


def summer_sale(request):
    products = Product.objects.filter(badge__iexact="SALE")
    return render(request, "summer_sale.html", {"products": products})


# ==================== CART ====================
@login_required
@require_POST
def add_to_cart(request, product_id=None):
    pid = product_id or request.POST.get('product_id')
    product = get_object_or_404(Product, id=pid)

    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()

    messages.success(request, f"{product.name} added to your cart.")
    # FIX: Redirect strictly to the cart instead of HTTP_REFERER which was dropping and defaulting to home
    return redirect("view_cart")


@login_required
def place_order(request):
    # FIX: Check if a specific product is being ordered (via Single Order button)
    product_id = request.GET.get('product_id') or request.POST.get('product_id')

    if product_id:
        # SINGLE ITEM CHECKOUT LOGIC
        product = get_object_or_404(Product, id=product_id)

        # Create a mock item so the template renders normally without crashing
        class SingleItem:
            def __init__(self, p):
                self.product = p
                self.quantity = 1
                self.total_price = p.price

        cart_items = [SingleItem(product)]
        total_amt = product.price
        is_single_item = True
    else:
        # FULL CART CHECKOUT LOGIC
        db_cart_items = Cart.objects.filter(user=request.user).select_related('product')
        if not db_cart_items.exists():
            messages.info(request, "Your cart is empty. Please add items to proceed.")
            return redirect("home")

        cart_items = list(db_cart_items)
        total_amt = sum(item.product.price * item.quantity for item in cart_items)
        is_single_item = False

    if request.method == "POST" and 'full_name' in request.POST:
        full_name = request.POST.get("full_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        payment_method = request.POST.get("payment_method", "COD")

        # Create order
        order = Order.objects.create(
            user=request.user,
            phone=phone,
            address=address,
            total_amount=total_amt,
            payment_method=payment_method,
            status="Pending",
            is_paid=(payment_method == "COD"),
        )

        # Process the single item vs cart items into OrderItem database
        if is_single_item:
            OrderItem.objects.create(order=order, product=product, quantity=1)
            # Remove from cart if it happens to be in there
            Cart.objects.filter(user=request.user, product=product).delete()
        else:
            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            # Clear full cart
            Cart.objects.filter(user=request.user).delete()

        # Handle Payment Gateway
        if payment_method == "JazzCash":
            payload = build_payment_payload(order.id, order.total_amount)
            request.session["order_id"] = order.id
            return render(request, "payment/jazzcash_checkout.html", {
                "payload": payload,
                "action_url": getattr(settings, 'JAZZCASH_BASE_URL',
                                      "https://sandbox.jazzcash.com.pk/CustomerPortal/TransactionManagement/MerchantForm/")
            })
        else:
            messages.success(request, "Order placed successfully with Cash on Delivery!")
            return redirect("order_confirmation", order_id=order.id)

    profile = getattr(request.user, "userprofile", None)

    # Render Template
    return render(request, "place_order.html", {
        "cart_items": cart_items,
        "profile": profile,
        "total_amt": total_amt,
        "product_id": product_id  # Pass this to retain standard flow
    })
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    total = sum(item.total_price for item in cart_items)
    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


@login_required
@require_POST
def update_cart_item(request):
    item_id = request.POST.get("item_id")
    action = request.POST.get("action")
    try:
        item = Cart.objects.get(id=item_id, user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Cart item not found.")
        return redirect("view_cart")

    if action == "remove":
        item.delete()
        messages.success(request, "Item removed from cart.")
    elif action == "set_quantity":
        qty = int(request.POST.get("quantity", 1))
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save()
            messages.success(request, "Quantity updated.")
    return redirect("view_cart")


# ==================== WISHLIST ====================

@login_required
def view_wishlist(request):
    wishlist_ids = request.session.get('wishlist', [])
    wishlist_products = Product.objects.filter(id__in=wishlist_ids)
    return render(request, "wishlist.html", {"wishlist_products": wishlist_products})


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = request.session.get('wishlist', [])
    if product_id not in wishlist:
        wishlist.append(product_id)
        request.session['wishlist'] = wishlist
        messages.success(request, f"{product.name} added to your wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    wishlist = request.session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        request.session['wishlist'] = wishlist
        messages.success(request, "Item removed from wishlist.")
    return redirect(request.META.get("HTTP_REFERER", "view_wishlist"))


# ==================== ORDERS & CHECKOUT ====================


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total = order.total_amount if hasattr(order, 'total_amount') else order.total_price
    return render(request, "order_confirmation.html", {"order": order, "total": total})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})


@csrf_exempt
def jazzcash_return(request):
    if request.method == "POST":
        response = request.POST.dict()
        pp_ResponseCode = response.get("pp_ResponseCode")

        if pp_ResponseCode == "000":
            order_ref = response.get("pp_BillReference", "")
            order_id = order_ref.replace("Order", "") if order_ref else request.session.get("order_id")

            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.is_paid = True
                    order.status = "paid"
                    order.save()
                    messages.success(request, "Payment successful via JazzCash!")
                    return redirect("order_confirmation", order_id=order.id)
                except Order.DoesNotExist:
                    messages.error(request, "Order not found after payment.")
            return redirect("order_history")
        else:
            messages.error(request, f"Payment failed! Code: {pp_ResponseCode}")
            return render(request, "payment/payment_failed.html", {"response": response})

    messages.error(request, "Invalid payment response.")
    return redirect("home")


# ==================== CHATBOT API ====================

@csrf_exempt
def chatbot_api(request):
    """
    Handles incoming chat requests from the frontend chatbot widget.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").lower()

            # Placeholder Logic - Replace with your actual AI/Chatbot logic
            bot_response = "I am a simple bot. You said: " + user_message

            if "hello" in user_message:
                bot_response = "Hi there! How can I help you with your StyleMart shopping today?"
            elif "order" in user_message or "track" in user_message:
                bot_response = "You can view and track your orders in your Order History profile tab."

            return JsonResponse({"response": bot_response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)