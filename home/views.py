from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from datetime import datetime
from .models import Profile, Newsletter, ContactMessage, MediaUpload, Withdrawal
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import F
from django.contrib.auth.decorators import login_required
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Withdrawal  # make sure these models exist


# Create your views here.
def index(request):
    return render(request, 'index.html')


def videos(request):
    """Display a random video with user's points (if logged in)"""
    
    # 1️⃣ Get user points if logged in
    if request.user.is_authenticated:
        profile = request.user.profile
        points_balance = profile.points_balance or 0
    else:
        profile = None
        points_balance = 0

    # 2️⃣ List of your static video files
    video_files = [
        'videos/1.mp4',
        'videos/2.mp4',
        'videos/3.mp4',
        'videos/4.mp4',
        'videos/5.mp4',
    ]
    
    # 3️⃣ Choose one random static video
    random_video = random.choice(video_files)

    # 4️⃣ Choose one uploaded video (or None if no videos exist)
    uploaded_video = MediaUpload.objects.first()  # only one video

    context = {
        "video": uploaded_video,        # single video object
        "random_video": random_video,   # static video path
        "points_balance": points_balance,
        "profile": profile,
    }
    
    return render(request, 'videos.html', context)


@csrf_exempt
def video_completed(request, video_id):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "❌ You must log in to earn points"}, status=403)

    if request.method != "POST":
        return JsonResponse({"message": "❌ Invalid request"}, status=400)

    video = get_object_or_404(MediaUpload, id=video_id)

    # 1️⃣ Award points to viewer
    viewer_profile, _ = Profile.objects.get_or_create(
        user=request.user, defaults={'points_balance': 0}
    )
    viewer_profile.points_balance = F('points_balance') + 2
    viewer_profile.save()
    viewer_profile.refresh_from_db()
    viewer_profile.add_notification(
        f"✅ You earned 2 points for watching '{video.title}' uploaded by {video.username}."
    )

    # 2️⃣ Award points to video creator
    try:
        creator_user = User.objects.get(username=video.username)
        creator_profile, _ = Profile.objects.get_or_create(
            user=creator_user, defaults={'points_balance': 0}
        )
        creator_profile.points_balance = F('points_balance') + 1
        creator_profile.save()
        creator_profile.refresh_from_db()
        creator_profile.add_notification(
            f"🎉 You earned 1 point because your video '{video.title}' was watched by {request.user.username}."
        )
    except User.DoesNotExist:
        pass

    return JsonResponse({
        "message": f"✅ You earned 2 points! Your new balance: {viewer_profile.points_balance}"
    })



def upload(request):
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        tags = request.POST.get('tags')
        category = request.POST.get('category')
        caption = request.POST.get('caption')
        username = request.POST.get('username')
        media_file = request.FILES.get('mediaFile')

        if not media_file:
            messages.error(request, "Please select a video to upload.")
            return redirect('/upload')

        MediaUpload.objects.create(
            title=title,
            description=description,
            tags=tags,
            category=category,
            caption=caption,
            username=username,
            media_file=media_file
        )

        messages.success(request, "Video uploaded successfully!")
        return redirect('/upload')

    return render(request, 'upload.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message_text = request.POST.get("message")
        captcha = request.POST.get("captcha")
        attached_file = request.FILES.get("file")  # Handle file uploads

        # Simple validation
        if not all([name, email, message_text, captcha]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("contact")

        if captcha.strip() != "4":
            messages.error(request, "Incorrect answer to CAPTCHA.")
            return redirect("contact")

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message_text,
            attached_file=attached_file
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, "contact.html")


def faqs(request):
    return render(request, 'faqs.html')

def policy(request):
    return render(request, 'policy.html')

def terms(request):
    return render(request, 'terms.html')

def login(request):
    if request.method == "POST":
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')

        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=email_or_username)
        except User.DoesNotExist:
            # Fallback to username
            try:
                user_obj = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password.")
                return render(request, 'login.html')

        user = authenticate(username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/profile')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'login.html')

    return render(request, 'login.html')
def signup(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        username = request.POST.get("username")
        referral_code_entered = request.POST.get("referral_code")  # optional

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already in use.")
            return redirect("signup")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("signup")
        
        # Check referral code
        if referral_code_entered:
            try:
                referrer_profile = Profile.objects.get(referral_code=referral_code_entered.upper())
                # Add 10 points
                referrer_profile.points_balance += 10
                # Add notification
                message = f"You have been rewarded 10 points because someone used your referral code!"
                if referrer_profile.notifications:
                    referrer_profile.notifications += f"\n{message}"
                else:
                    referrer_profile.notifications = message
                referrer_profile.save()
            except Profile.DoesNotExist:
                messages.error(request, "Invalid referral code.")
                return redirect("signup")

            
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname
        )

        # Create profile
        profile = Profile.objects.create(
            user=user,
            full_name=fullname,
            referred_by=referral_code_entered if referral_code_entered else ""
        )

        auth_login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("/profile")

    return render(request, "signup.html")



def profile(request):
    # Redirect anonymous users to login
    if request.user.is_anonymous:
        return redirect('/login')

    # Get the user's profile
    user_profile = request.user.profile

    # Get user's uploaded videos
    user_videos = MediaUpload.objects.filter(username=request.user.username).order_by('-uploaded_at')

    # Split notifications into a list
    notifications = user_profile.notifications.splitlines() if user_profile.notifications else []

    # Clear notifications after reading
    user_profile.notifications = ""
    user_profile.save()

    # Prepare context
    context = {
        "notifications": notifications,
        "user_videos": user_videos,
        "username": request.user.username,
        "email": request.user.email,
        "full_name": user_profile.full_name,
        "points_balance": user_profile.points_balance,
        "usd_balance": user_profile.usd_balance,
        "join_date": user_profile.join_date,
        "referral_code": user_profile.referral_code,
        "referred_by": user_profile.referred_by,
    }

    return render(request, "profile.html", context)






def wallet(request):
    if request.user.is_anonymous:
        return redirect('/login')

    profile = request.user.profile

    # ================== HANDLE NOTIFICATIONS ==================
    notifications = profile.notifications.splitlines() if profile.notifications else []
    profile.notifications = ""  # clear after loading
    profile.save()

    context = {
        "notifications": notifications,
        "username": request.user.username,
        "email": request.user.email,
        "full_name": profile.full_name,
        "points_balance": profile.points_balance,
        "usd_balance": profile.usd_balance,
        "join_date": profile.join_date,
        "referral_code": profile.referral_code,
        "referred_by": profile.referred_by,
    }

    # ================== HANDLE POST ==================
    if request.method == "POST":

        # ---------- WITHDRAW ----------
        if "withdraw" in request.POST:
            try:
                amount = float(request.POST.get('amount'))
            except (TypeError, ValueError):
                messages.error(request, "❌ Please enter a valid withdrawal amount.")
                return redirect('wallet')

            method = request.POST.get('method')
            account_details = request.POST.get('account_details')

            # ✅ Minimum withdrawal
            if amount < 25:
                messages.warning(request, "⚠️ Minimum withdrawal amount is $25.")
                return redirect('wallet')

            # ✅ Check balance
            if amount > profile.usd_balance:
                messages.error(
                    request,
                    f"❌ Withdrawal failed! You only have ${profile.usd_balance:.2f} available."
                )
                return redirect('wallet')

            # ✅ Must upload at least 5 videos in last 7 days
            one_week_ago = timezone.now() - timezone.timedelta(days=7)
            recent_uploads = MediaUpload.objects.filter(
                uploaded_by=request.user,
                uploaded_at__gte=one_week_ago
            ).count()


            # ✅ Create withdrawal request (do not deduct yet)
            Withdrawal.objects.create(
                user=request.user,
                amount=amount,
                method=method,
                account_details=account_details,
                status="Pending"  # always pending
            )

            messages.success(
                request,
                f"🎉 Withdrawal request of ${amount:.2f} submitted successfully! It will be reviewed by admin."
            )
            return redirect('wallet')

        # ---------- CONVERT POINTS ----------
        elif "convert" in request.POST:
            try:
                points = int(request.POST.get('points'))
            except (TypeError, ValueError):
                messages.error(request, "❌ Please enter a valid number of points.")
                return redirect('wallet')

            conversion_rate = 0.01  # 100 points = $1
            usd_amount = points * conversion_rate

            if points > profile.points_balance:
                messages.error(request, "⚠️ You don’t have enough points to convert.")
                return redirect('wallet')

            # ✅ Deduct points, add USD
            profile.points_balance -= points
            profile.usd_balance += usd_amount
            profile.save()

            messages.success(
                request,
                f"💰 Successfully converted {points} points into ${usd_amount:.2f}"
            )
            return redirect('wallet')

    return render(request, 'wallet.html', context)




@login_required
def convert_points(request):
    if request.method == "POST":
        profile = request.user.profile
        if profile.points_balance >= 100:
            pkrs = profile.points_balance // 100
            profile.points_balance -= pkrs * 100
            profile.usd_balance += pkrs
            profile.save()
            return JsonResponse({
                "success": True,
                "points_balance": profile.points_balance,
                "usd_balance": profile.usd_balance,
                "message": f"Successfully converted {pkrs*100} points to {pkrs} PKR!"
            })
        else:
            return JsonResponse({"success": False, "message": "Insufficient funds."})
    return JsonResponse({"success": False, "message": "Invalid request."})

def logout(request):
    auth_logout(request)
    return redirect("/login")

def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if Newsletter.objects.filter(email=email).exists():
            messages.info(request, "You are already subscribed!")
        else:
            Newsletter.objects.create(email=email)
            messages.success(request, "Subscribed successfully!")
    return redirect(request.META.get('HTTP_REFERER', '/'))