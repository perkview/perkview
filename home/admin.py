from django.contrib import admin
from home.models import Profile, Newsletter, ContactMessage, MediaUpload, Withdrawal

# Register your models here.
admin.site.register(Profile)
admin.site.register(Newsletter)
admin.site.register(ContactMessage)
admin.site.register(MediaUpload)
admin.site.register(Withdrawal)