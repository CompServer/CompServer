
def tz(request):
    from django.utils import timezone

    tz = request.session.get('timezone',None) or timezone.get_current_timezone_name()
    
    return {"TIME_ZONE": tz}

def user(request):
    return {"user": request.user}
