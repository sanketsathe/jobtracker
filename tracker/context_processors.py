from .models import UserProfile


def user_profile(request):
    profile = None
    initials = ""
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        full_name = (profile.full_name or "").strip()
        if full_name:
            parts = full_name.split()
            initials = "".join(part[0] for part in parts[:2]).upper()
        else:
            username = request.user.get_username() or ""
            initials = username[:2].upper()
    return {"user_profile": profile, "user_initials": initials}
