from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('videos/', views.videos, name='videos'),
    path('upload/', views.upload, name='upload'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faqs/', views.faqs, name='faqs'),
    path('policy/', views.policy, name='policy'),
    path('terms/', views.terms, name='terms'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('wallet/', views.wallet, name='wallet'),
    path('logout/', views.logout, name='logout'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('video_completed/<int:video_id>/', views.video_completed, name='video_completed'),
    path('convert_points/', views.convert_points, name='convert_points'),
]   

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
