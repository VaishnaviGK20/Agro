from django.conf import settings


def site_settings(request):
    return {
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,
        'SITE_NAME': 'Agro Assist',
    }
