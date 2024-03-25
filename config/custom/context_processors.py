"""
All custom context processors written by John Mulligan.
"""
def tz(request):
    from django.utils import timezone

    tz = request.session.get('timezone',None) or timezone.get_current_timezone_name()
    
    return {"TIME_ZONE": tz}

def user(request):
    """
    Passes in the request and request_user of the request as a variable "request" and "user" respectively.
    """
    return {"request": request, "user": request.user}

def current_time(request):
    from django.utils import timezone

    timezone.activate(timezone.get_current_timezone())

    return {
        "NOW": timezone.now(), 
        "CURRENT_TIME": timezone.now().time(),
        "CURRENT_DATE": timezone.now().date(),
    }
