from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# Create your models here.


class Profile(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    points_balance = models.IntegerField(default=0)
    usd_balance = models.FloatField(default=0.0)
    join_date = models.DateTimeField(default=timezone.now)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.CharField(max_length=10, blank=True, null=True)

    # NEW: store notifications as a simple text list (JSON or comma separated)
    notifications = models.TextField(blank=True, default="")  

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super(Profile, self).save(*args, **kwargs)

    def add_notification(self, message):
        if self.notifications:
            self.notifications += f"\n{message}"
        else:
            self.notifications = message
        self.save()

    
    def convert_points_to_usd(self):
        if self.points_balance >= 100:
            # 100 points = 1 PKR
            pkr_amount = self.points_balance // 100
            points_to_deduct = pkr_amount * 100

            # PKR to USD rate (example: 1 PKR = 0.0036 USD)
            usd_rate = 0.0036
            usd_amount = pkr_amount * usd_rate

            # Update balances
            self.points_balance -= points_to_deduct
            self.usd_balance += usd_amount
            self.save()
            return {"success": True, "usd_added": usd_amount, "pkr_used": pkr_amount}
        return {"success": False, "message": "Insufficient points (minimum 100 required)."}

    

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=100, default='General Inquiry')
    message = models.TextField()
    attached_file = models.FileField(upload_to='contact_files/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class MediaUpload(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=50)
    caption = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=150)
    media_file = models.FileField(upload_to='uploads/videos/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} by {self.username}"
    
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Withdrawal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # e.g., EasyPaisa, JazzCash, Bank Transfer
    account_details = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ],
        default="Pending",
    )
    requested_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.status}"
