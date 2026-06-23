import random
import smtplib

import razorpay
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import (
    Location,
    OrderHistory,
    Payment,
    addcart,
    item,
    userDetails,
    userinfo,
    userreq,
)

razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def password_matches(stored_password, raw_password):
    if stored_password.startswith(('pbkdf2_', 'argon2', 'bcrypt')):
        return check_password(raw_password, stored_password)
    return stored_password == raw_password


def hash_password(raw_password):
    return make_password(raw_password)


def get_logged_in_user(request):
    username = request.session.get('username')
    if not username:
        return None
    try:
        return userDetails.objects.get(username=username)
    except userDetails.DoesNotExist:
        return None


def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('username'):
            return redirect('login')
        return view_func(request, *args, **kwargs)

    return wrapper


def require_category(category):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = get_logged_in_user(request)
            if not user:
                return redirect('login')
            if user.category != category:
                return redirect('seller' if category == 'Customer' else 'farmerpage')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def send_otp_email(email, otp, subject='Your OTP for Agro Assist'):
    message = (
        f'Your OTP is: {otp}\n\n'
        'This code expires in 10 minutes. Do not share it with anyone.\n\n'
        'Agro Assist Team'
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        return True
    except (smtplib.SMTPException, OSError):
        return False


def home(request):
    return render(request, 'home.html')


def user_login(request):
    msg = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        category = request.POST.get('category', '')

        try:
            user = userDetails.objects.get(username=username)
        except userDetails.DoesNotExist:
            msg = 'User not registered!'
        else:
            if not password_matches(user.password, password):
                msg = 'Wrong password!'
            elif user.category != category:
                msg = 'Category mismatch! Please select the correct category.'
            else:
                request.session['username'] = username
                request.session['category'] = user.category
                if user.category == 'Seller':
                    return redirect('farmerpage')
                return redirect('seller')

    return render(request, 'login.html', {'msg': msg})


def logout_view(request):
    request.session.flush()
    return redirect('login')


def farmerpage(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Seller':
        return redirect('seller')
    return render(request, 'farmerpage.html', {'user': user})


def seller(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Customer':
        return redirect('farmerpage')
    products = item.objects.select_related('seller').all()
    return render(request, 'seller.html', {'products': products, 'user': user})


def home2(request):
    return redirect('seller')


def admin_login(request):
    msg = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if (
            username == settings.ADMIN_PORTAL_USERNAME
            and password == settings.ADMIN_PORTAL_PASSWORD
        ):
            request.session['admin_logged_in'] = True
            return redirect('admins')
        msg = 'Invalid username or password!'
    return render(request, 'admin_login.html', {'msg': msg})


def admins(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    return render(request, 'admin.html')


def home1(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Seller':
        return redirect('seller')

    values = item.objects.filter(seller=user)
    return render(request, 'home1.html', {'values': values, 'msg': ''})


def add_item(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Seller':
        return redirect('seller')

    msg = ''
    if request.method == 'POST' and request.FILES.get('image'):
        item.objects.create(
            seller=user,
            name=request.POST.get('name', '').strip(),
            quantity=request.POST.get('quantity', ''),
            price=request.POST.get('price', ''),
            imagepath=request.FILES['image'],
        )
        msg = 'Item added successfully!'

    values = item.objects.filter(seller=user)
    return render(request, 'home1.html', {'values': values, 'msg': msg})


def delete1(request, name):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    item.objects.filter(name=name, seller=user).delete()
    return redirect('home1')


def contactus(request):
    msg = ''
    if request.method == 'POST':
        yourname = request.POST.get('yourname', '').strip()
        email = request.POST.get('email', '').strip()
        tel = request.POST.get('tel', '').strip()
        message = request.POST.get('message', '').strip()
        if yourname and email and tel and message:
            userreq.objects.update_or_create(
                yourname=yourname,
                defaults={'email': email, 'tel': tel, 'message': message},
            )
            msg = 'Your request has been recorded. We will contact you soon.'
    return render(request, 'contactus.html', {'msg': msg})


def view_requests(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    requests = userreq.objects.all().order_by('-yourname')
    return render(request, 'user_requests.html', {'requests': requests})


def aboutus(request):
    return render(request, 'aboutus.html')


def view_cart(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Customer':
        return redirect('farmerpage')

    cart_items = addcart.objects.filter(custid=user.username)
    products = [entry.name for entry in cart_items]
    amounts = [entry.price for entry in cart_items]
    total_price = sum(amounts)

    request.session['product_names'] = products
    request.session['total_price'] = total_price
    request.session.modified = True

    return render(
        request,
        'cart.html',
        {
            'Product': zip(products, amounts),
            'ProductNames': products,
            'sum': total_price,
            'disable_button': total_price <= 0,
        },
    )


def cart(request, name, price):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    if user.category != 'Customer':
        return render(request, 'login.html', {'msg': 'Only customers can add items to the cart.'})

    try:
        price_value = int(float(price))
    except (TypeError, ValueError):
        return redirect('seller')

    if name and name != 'dummy' and price_value > 0:
        addcart.objects.create(
            prid=random.randint(1, 999999),
            custid=user.username,
            name=name,
            price=price_value,
        )

    cart_items = addcart.objects.filter(custid=user.username)
    products = [entry.name for entry in cart_items]
    amounts = [entry.price for entry in cart_items]
    total_price = sum(amounts)

    request.session['product_names'] = products
    request.session['total_price'] = total_price
    request.session.modified = True

    return render(
        request,
        'cart.html',
        {
            'Product': zip(products, amounts),
            'ProductNames': products,
            'sum': total_price,
            'disable_button': total_price <= 0,
        },
    )


def delete_cart_item(request, name):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    item_to_delete = addcart.objects.filter(name=name, custid=user.username).first()
    if item_to_delete:
        item_to_delete.delete()

    cart_items = addcart.objects.filter(custid=user.username)
    product_list = [entry.name for entry in cart_items]
    amount_list = [entry.price for entry in cart_items]
    total_price = sum(amount_list)

    request.session['product_names'] = product_list
    request.session['total_price'] = total_price
    request.session.modified = True

    return render(
        request,
        'cart.html',
        {
            'Product': zip(product_list, amount_list),
            'ProductNames': product_list,
            'sum': total_price,
            'disable_button': total_price == 0,
        },
    )


def info(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    user_info, _ = userinfo.objects.get_or_create(
        yourname=user.username,
        defaults={'phoneNumber': user.phoneNumber},
    )

    products = request.GET.get('products', '')
    total_price = request.GET.get('total') or request.session.get('total_price', 0)
    product_list = request.session.get('product_names') or []
    if products:
        product_list = [p.strip() for p in products.split(',') if p.strip()]

    if request.method == 'POST':
        user_info.phoneNumber = request.POST.get('phoneNumber', user.phoneNumber)
        user_info.house_number = request.POST.get('house_number', '')
        user_info.cross_and_main = request.POST.get('cross_and_main', '')
        user_info.area = request.POST.get('area', '')
        user_info.district = request.POST.get('district', '')
        user_info.pincode = request.POST.get('pincode', '')
        user_info.payment_method = request.POST.get('payment_method', '')
        user_info.product_name = ', '.join(product_list)
        user_info.total_price = str(total_price)
        user_info.save()

        recipient_email = user.username
        message = (
            f'Hello,\n\nYour order has been placed successfully.\n\n'
            f'Products: {user_info.product_name}\n'
            f'Total: Rs {user_info.total_price}\n\n'
            f'Delivery address:\n'
            f'{user_info.house_number}, {user_info.cross_and_main}, {user_info.area},\n'
            f'{user_info.district} - {user_info.pincode}\n'
            f'Phone: {user_info.phoneNumber}\n'
            f'Payment: {user_info.payment_method.upper()}\n\n'
            f'Thank you for shopping with Agro Assist!'
        )
        try:
            send_mail(
                'Order Confirmation - Agro Assist',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )
        except (smtplib.SMTPException, OSError):
            pass

        _create_order_history(user, user_info, product_list, total_price)
        addcart.objects.filter(custid=user.username).delete()

        if user_info.payment_method == 'cod':
            return redirect('order')
        return redirect('payment')

    return render(
        request,
        'info.html',
        {
            'user_info': user_info,
            'cart_products': product_list,
            'total_price': total_price,
        },
    )


def _create_order_history(user, user_info, product_list, total_price):
    for product_name in product_list:
        try:
            product = item.objects.get(name=product_name)
        except item.DoesNotExist:
            continue
        OrderHistory.objects.create(
            customer=user,
            product=product,
            total_price=float(total_price) / max(len(product_list), 1),
            location=user_info,
        )


def save_user_info(request):
    return JsonResponse({'status': 'error', 'message': 'Use the order form on /info/'}, status=400)


def order(request):
    return render(request, 'order.html')


def search(request):
    query = ''
    products = item.objects.all()
    if request.method == 'POST':
        query = request.POST.get('searched', '').strip()
        if query:
            products = item.objects.filter(name__icontains=query)
    return render(request, 'search.html', {'products': products, 'search': query})


def admin_dashboard(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')
    farmers = userDetails.objects.filter(category='Seller')
    customers = userDetails.objects.filter(category='Customer')
    return render(request, 'admin_dashboard.html', {'farmers': farmers, 'customers': customers})


def order_history(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    orders = OrderHistory.objects.filter(customer=user).select_related('product', 'location').order_by('-order_date')
    order_rows = []
    for entry in orders:
        location = entry.location
        location_str = ''
        if location:
            location_str = (
                f'{location.house_number}, {location.cross_and_main}, '
                f'{location.area}, {location.district}, {location.pincode}'
            )
        order_rows.append(
            {
                'product_name': entry.product.name,
                'price': entry.total_price,
                'customer_email': user.username,
                'location': location_str,
                'order_date': entry.order_date,
            }
        )

    if not order_rows:
        try:
            customer_info = userinfo.objects.get(yourname=user.username)
            if customer_info.product_name:
                order_rows.append(
                    {
                        'product_name': customer_info.product_name,
                        'price': customer_info.total_price,
                        'customer_email': user.username,
                        'location': (
                            f'{customer_info.house_number}, {customer_info.cross_and_main}, '
                            f'{customer_info.area}, {customer_info.district}, {customer_info.pincode}'
                        ),
                        'order_date': None,
                    }
                )
        except userinfo.DoesNotExist:
            pass

    return render(request, 'order_history.html', {'orders': order_rows})


def upload_location(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    error = ''
    if request.method == 'POST':
        house_number = request.POST.get('house_number', '').strip()
        cross_and_main = request.POST.get('cross_and_main', '').strip()
        area = request.POST.get('area', '').strip()
        district = request.POST.get('district', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        if not all([house_number, cross_and_main, area, district, pincode]):
            error = 'All fields are required.'
        else:
            Location.objects.filter(user=user).delete()
            Location.objects.create(
                house_number=int(house_number) if house_number.isdigit() else 1,
                cross_and_main=cross_and_main,
                area=area,
                district=district,
                pincode=pincode,
                user=user,
            )
            return redirect('add_item')

    return render(request, 'upload_location.html', {'error': error})


def user_order(request):
    return redirect('order_history')


def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def reg(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        upassword = request.POST.get('password', '')
        cpassword = request.POST.get('Cpassword', '')
        uphone = request.POST.get('phoneNumber', '').strip()
        ugender = request.POST.get('gender', '')
        ucategory = request.POST.get('category', '')

        if not is_valid_email(username):
            return render(request, 'reg.html', {'msg': 'Invalid email format!'})
        if userDetails.objects.filter(username=username).exists():
            return render(request, 'reg.html', {'msg': 'User already exists!'})
        if upassword != cpassword:
            return render(request, 'reg.html', {'msg': 'Passwords do not match!'})
        if not ugender or not ucategory:
            return render(request, 'reg.html', {'msg': 'Please select gender and category.'})

        otp = str(random.randint(100000, 999999))
        request.session['pending_registration'] = {
            'username': username,
            'password': hash_password(upassword),
            'Cpassword': hash_password(cpassword),
            'phoneNumber': uphone,
            'gender': ugender,
            'category': ucategory,
        }
        request.session['registration_otp'] = otp
        request.session['registration_email'] = username

        if send_otp_email(username, otp, subject='Your OTP for Registration - Agro Assist'):
            return redirect('verify_otp')
        return render(request, 'reg.html', {'msg': 'Could not send OTP. Check email settings and try again.'})

    return render(request, 'reg.html')


def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        stored_otp = request.session.get('registration_otp')
        user_data = request.session.get('pending_registration', {})

        if stored_otp and entered_otp == stored_otp and user_data:
            userDetails.objects.create(**user_data)
            for key in ('pending_registration', 'registration_otp', 'registration_email'):
                request.session.pop(key, None)
            return redirect('login')

        return render(request, 'verify_otp.html', {'msg': 'Invalid OTP. Try again!'})

    return render(request, 'verify_otp.html')


def payment_page(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    return render(request, 'payment.html', {'total_price': request.session.get('total_price', 0)})


@require_http_methods(['POST'])
def create_order(request):
    if not razorpay_client:
        return JsonResponse({'error': 'Payment gateway not configured'}, status=503)
    total_price = request.session.get('total_price', 0)
    try:
        amount = int(float(total_price) * 100)
    except (TypeError, ValueError):
        amount = 0
    if amount <= 0:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    order_data = {'amount': amount, 'currency': 'INR', 'payment_capture': '1'}
    order = razorpay_client.order.create(order_data)
    Payment.objects.create(order_id=order['id'], amount=total_price, status='Created')
    return JsonResponse(order)


@require_http_methods(['POST'])
def verify_payment(request):
    if not razorpay_client:
        return JsonResponse({'status': 'failure', 'message': 'Payment gateway not configured'}, status=503)
    data = request.POST
    try:
        razorpay_client.utility.verify_payment_signature(data)
        payment = Payment.objects.get(order_id=data.get('razorpay_order_id'))
        payment.payment_id = data.get('razorpay_payment_id')
        payment.status = 'paid'
        payment.save()
        return JsonResponse({'status': 'success', 'redirect': '/order/'})
    except (razorpay.errors.SignatureVerificationError, Payment.DoesNotExist):
        return JsonResponse({'status': 'failure'}, status=400)


def get_cart_total(request):
    return JsonResponse({'total_amount': request.session.get('total_price', 0)})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            userDetails.objects.get(username=email)
        except ObjectDoesNotExist:
            return render(request, 'forgot_password.html', {'msg': 'User not found!'})

        otp = str(random.randint(100000, 999999))
        request.session['reset_email'] = email
        request.session['reset_otp'] = otp

        if send_otp_email(email, otp, subject='Your OTP for Password Reset - Agro Assist'):
            return redirect('verify_reset_otp')
        return render(request, 'forgot_password.html', {'msg': 'Error sending OTP. Try again!'})

    return render(request, 'forgot_password.html')


def verify_reset_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        stored_otp = request.session.get('reset_otp')
        email = request.session.get('reset_email')

        if email and stored_otp and entered_otp == stored_otp:
            request.session.pop('reset_otp', None)
            return redirect('reset_password')
        return render(request, 'verify_reset_otp.html', {'msg': 'Invalid OTP. Try again!'})

    return render(request, 'verify_reset_otp.html')


def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        email = request.session.get('reset_email')

        if new_password != confirm_password:
            return render(request, 'reset_password.html', {'msg': 'Passwords do not match!'})

        try:
            user = userDetails.objects.get(username=email)
            user.password = hash_password(new_password)
            user.Cpassword = hash_password(confirm_password)
            user.save()
            request.session.pop('reset_email', None)
            return redirect('login')
        except ObjectDoesNotExist:
            return render(request, 'reset_password.html', {'msg': 'User not found!'})

    return render(request, 'reset_password.html')


def display_tables(request):
    if not request.session.get('admin_logged_in'):
        return redirect('admin_login')

    user_data = userinfo.objects.all()
    item_list = []
    for product in item.objects.select_related('seller').all():
        seller = product.seller
        location_obj = Location.objects.filter(user=seller).first() if seller else None
        location_str = 'Unknown'
        if location_obj:
            location_str = (
                f'{location_obj.house_number}, {location_obj.cross_and_main}, '
                f'{location_obj.area}, {location_obj.district}, {location_obj.pincode}'
            )
        item_list.append(
            {
                'item_name': product.name,
                'seller_name': seller.username if seller else 'Unknown',
                'location': location_str,
            }
        )

    return render(request, 'tables.html', {'user_data': user_data, 'items_info': item_list})
