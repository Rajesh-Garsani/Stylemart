from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Cart, Order, OrderItem
from .forms import SignupForm, LoginForm
from .jazzcash_utils import build_payment_payload
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.db.models.functions import Random

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(badge__isnull=False).order_by("?")[:8]  # e.g. featured
    all_products = Product.objects.order_by("?")[:20]  # random mix for homepage
    return render(request, "home.html", {
        "categories": categories,
        "featured_products": featured_products,
        "all_products": all_products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # If user submits "order now" (from product page), forward to place_order with one item.
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_to_cart":
            # Redirect to add_to_cart view (POST)
            return add_to_cart(request, product_id=product.id)
        elif action == "order_now":
            # Create a quick one-item order OR redirect to checkout page prefilling the product
            # We'll add product to cart (for simplicity) then redirect to place_order
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

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    return render(request, "category_products.html", {"category": category, "products": products})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, "category_detail.html", {
        "category": category,
        "products": products,
    })

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


@login_required
def add_to_cart(request, product_id=None):
    if request.method == "POST" or product_id is not None:
        pid = product_id or int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=pid)

        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            # Increase quantity if already in cart
            cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"{product.name} added to your cart.")
        # If AJAX call, return a minimal response (not implemented). For now redirect back.
        return redirect(request.META.get("HTTP_REFERER", "home"))
    else:
        # Non-POST to this URL: redirect to product page
        messages.error(request, "Invalid request method.")
        return redirect("home")


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
def update_cart_item(request):
    if request.method == "POST":
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

@login_required
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("home")

    if request.method == "POST" and 'full_name' in request.POST:
        full_name = request.POST.get("full_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        payment_method = request.POST.get("payment_method", "COD")

        # Create order
        order = Order.objects.create(
            user=request.user,
            phone=phone or "",
            address=address or "",
            total_amount=sum(item.product.price * item.quantity for item in cart_items),
            payment_method=payment_method,
            status="Pending",
            is_paid=(payment_method == "COD"),   # ✅ COD is paid on delivery, so keep False if you prefer
        )

        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
        cart_items.delete()

        if payment_method == "JazzCash":
            # Redirect to JazzCash checkout
            payload = build_payment_payload(order.id, order.total_amount)
            request.session["order_id"] = order.id
            return render(request, "payment/jazzcash_checkout.html", {
                "payload": payload,
                "action_url": settings.JAZZCASH_BASE_URL
            })
        else:
            # ✅ COD: Confirm order immediately
            messages.success(request, "Order placed successfully with Cash on Delivery!")
            return redirect("order_confirmation", order_id=order.id)

    profile = getattr(request.user, "userprofile", None)
    return render(request, "place_order.html", {"cart_items": cart_items, "profile": profile})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total = order.total_price  # property
    return render(request, "order_confirmation.html", {"order": order, "total": total})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})


def jazzcash_payment(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    payload = build_payment_payload(order.id, order.total_price)
    return render(request, "payment/jazzcash_checkout.html", {"payload": payload, "action_url": settings.JAZZCASH_BASE_URL})

@csrf_exempt
def jazzcash_return(request):
    response = request.POST.dict()
    if response.get("pp_ResponseCode") == "000":
        # Payment success
        order_id = response.get("pp_BillReference", "").replace("Order", "")
        Order.objects.filter(id=order_id).update(is_paid=True, status="paid")
        return redirect("order_confirmation", order_id=order_id)
    else:
        return render(request, "payment/payment_failed.html", {"response": response})

@csrf_exempt
def jazzcash_return(request):
    """
    Handle JazzCash POST response (success or failure).
    """
    if request.method == "POST":
        pp_ResponseCode = request.POST.get("pp_ResponseCode")
        pp_TxnRefNo = request.POST.get("pp_TxnRefNo")
        pp_Amount = request.POST.get("pp_Amount")

        # ✅ JazzCash sends "000" on success
        if pp_ResponseCode == "000":
            # Mark last order as paid
            order_id = request.session.get("order_id")
            if order_id:
                try:
                    order = Order.objects.get(id=order_id, user=request.user)
                    order.is_paid = True
                    order.status = Order.STATUS_PROCESSING
                    order.save()
                except Order.DoesNotExist:
                    pass
            messages.success(request, "Payment successful via JazzCash!")
            return redirect("order_history")
        else:
            messages.error(request, f"Payment failed! Code: {pp_ResponseCode}")
            return redirect("view_cart")

    messages.error(request, "Invalid payment response.")
    return redirect("home")


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})


# views.py
@login_required
def summer_sale(request):
    products = Product.objects.filter(badge__iexact="SALE")
    return render(request, "summer_sale.html", {"products": products})





def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()


    category_slug = request.GET.get("category")
    sort = request.GET.get("sort")
    price_range = request.GET.get("price")


    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Price filter
    if price_range == "under25":
        products = products.filter(price__lt=25)
    elif price_range == "25_50":
        products = products.filter(price__gte=25, price__lte=50)
    elif price_range == "50_100":
        products = products.filter(price__gte=50, price__lte=100)
    elif price_range == "over100":
        products = products.filter(price__gt=100)


    if sort == "price_low":
        products = products.order_by("price")
    elif sort == "price_high":
        products = products.order_by("-price")
    elif sort == "rating":
        products = products.order_by("-rating")
    else:
        products = products.order_by("-is_featured")

    return render(request, "products/product_list.html", {
        "products": products,
        "categories": categories,
    })
