from functools import wraps
from django.conf import settings
from django.shortcuts import redirect

def login_required_without_next(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect(settings.LOGIN_URL)
    return _wrapped_view

def login_not_required_without_next(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect(settings.LOGIN_REDIRECT_URL)
    return _wrapped_view