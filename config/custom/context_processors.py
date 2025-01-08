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

def settings_values(request):
    import config.settings
    context_processors = {
        "DEMO": config.settings.DEMO, 
        "PROD": config.settings.PROD,
        #"DEBUG": config.settings.DEBUG, # django provided
        "USE_SENTRY": config.settings.USE_SENTRY,
        "USE_SASS": config.settings.USE_SASS,
        "SENTRY_REPLAY_URL": config.settings.SENTRY_REPLAY_URL,
        "RELEASE_VERSION": config.settings.RELEASE_VERSION, # usually the git commit hash
    }

    OPTIONAL_GIT_VAR_NAMES = [
        "SHOW_GH_DEPLOYMENT_TO_ALL",
        "GITHUB_LATEST_PUSHED_COMMIT_HASH", 
        "GITHUB_LATEST_PUSHED_COMMIT_HASH_SHORT",
        "GITHUB_LATEST_COMMIT_URL",
        "GITHUB_CURRENT_BRANCH_NAME", 
        "GITHUB_CURRENT_BRANCH_URL",
        "GIT_URL",
    ]

    for git_var_name in OPTIONAL_GIT_VAR_NAMES:
        attr_value = getattr(config.settings, git_var_name, None)

        #if attr_value:
        context_processors[git_var_name] = attr_value

    return context_processors
