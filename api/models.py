from django.db import models
from hashids import Hashids
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField


class UserProfile(models.Model):
    name = models.CharField(max_length=100, null= True)
    surname = models.CharField(max_length=100, null= True)
    storename = models.CharField(max_length=100, null= True)
    wallet_address = models.CharField(verbose_name="Ethereum Wallet Address",
        max_length=42,
        validators=[RegexValidator(regex=r'^0x[a-fA-F0-9]{40}$')],)

    def __str__(self):
        return self.name + " " + self.surname + " " + self.wallet_address

class Order(models.Model):
    email = models.EmailField(max_length=100)
    name = models.CharField(max_length=100, null= True)
    surname = models.CharField(max_length=100, null= True)
    buyer = models.CharField(verbose_name="Ethereum Buyer Wallet Address",
        max_length=42,
        validators=[RegexValidator(regex=r'^0x[a-fA-F0-9]{40}$')],)
    seller = models.CharField(verbose_name="Ethereum Seller Wallet Address",
        max_length=42,
        validators=[RegexValidator(regex=r'^0x[a-fA-F0-9]{40}$')],)
    tokenId = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postalCode = models.CharField(max_length=100)
    unit = models.CharField(max_length=100, null= True)  # apartment, suite, unit, building, floor, etc.
    delivery = models.CharField(max_length=100)
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name="Phone Number")
    productCost = models.CharField(max_length=100)
    total = models.CharField(max_length=100)
    order_number = models.CharField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            hashids = Hashids(min_length=8, salt="thesis_salt")
            self.order_number = hashids.encode(int(self.tokenId)+int(self.buyer, 16))
        super(Order, self).save(*args, **kwargs)