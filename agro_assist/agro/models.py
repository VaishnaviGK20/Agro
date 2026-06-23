from django.db import models
from django.utils import timezone


class usercred(models.Model):
    username = models.CharField(max_length=40, primary_key=True)
    password = models.CharField(max_length=128)


class userDetails(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=128)
    Cpassword = models.CharField(max_length=128)
    phoneNumber = models.CharField(max_length=12)
    gender = models.CharField(max_length=20)
    category = models.CharField(max_length=20)

    def __str__(self):
        return self.username


class item(models.Model):
    seller = models.ForeignKey(
        userDetails,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    iname = models.CharField(max_length=20, null=True, blank=True)
    imagepath = models.ImageField(null=True, blank=True, upload_to='images/')
    name = models.CharField(max_length=40, primary_key=True)
    quantity = models.CharField(max_length=40)
    price = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class addcart(models.Model):
    prid = models.IntegerField(primary_key=True)
    custid = models.CharField(max_length=25)
    name = models.CharField(max_length=30)
    price = models.IntegerField()


class userreq(models.Model):
    yourname = models.CharField(max_length=100, primary_key=True)
    email = models.CharField(max_length=100)
    tel = models.CharField(max_length=12)
    message = models.CharField(max_length=500)


class userinfo(models.Model):
    yourname = models.CharField(max_length=100, primary_key=True)
    phoneNumber = models.CharField(max_length=12)
    house_number = models.CharField(max_length=10, blank=True, null=True)
    cross_and_main = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    product_name = models.TextField(blank=True, null=True)
    total_price = models.CharField(max_length=10, blank=True, null=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.yourname


class OrderHistory(models.Model):
    customer = models.ForeignKey(userDetails, on_delete=models.CASCADE)
    product = models.ForeignKey(item, on_delete=models.CASCADE)
    total_price = models.FloatField()
    location = models.ForeignKey(userinfo, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(default=timezone.now)


class Location(models.Model):
    house_number = models.PositiveIntegerField(default=1)
    cross_and_main = models.CharField(max_length=255, default='Unknown')
    area = models.CharField(max_length=255, default='Unknown')
    district = models.CharField(max_length=255, default='Unknown')
    pincode = models.CharField(max_length=6)
    user = models.ForeignKey('userDetails', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.house_number} - {self.pincode}'


class Payment(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=50, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id
