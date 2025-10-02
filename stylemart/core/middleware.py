from importlib import import_module
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse, NoReverseMatch

class PerPathSessionMiddleware(SessionMiddleware):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        try:
            admin_prefix = reverse('admin:index')
        except (NoReverseMatch, Exception):
            admin_prefix = '/admin/'
        if not admin_prefix.endswith('/'):
            admin_prefix += '/'
        self._admin_prefix = getattr(settings, 'ADMIN_SESSION_PATH', admin_prefix)
        if not self._admin_prefix.endswith('/'):
            self._admin_prefix += '/'
    def _cookie_name_for_request(self, request):
        if request.path.startswith(self._admin_prefix):
            return getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        return getattr(settings, 'USER_SESSION_COOKIE_NAME', settings.SESSION_COOKIE_NAME)

    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        cookie_name = self._cookie_name_for_request(request)
        session_key = request.COOKIES.get(cookie_name)
        request.session = engine.SessionStore(session_key)
        request._session_cookie_name = cookie_name

    def process_response(self, request, response):
        response = super().process_response(request, response)

        chosen_name = getattr(request, '_session_cookie_name', None) or self._cookie_name_for_request(request)
        default_name = settings.SESSION_COOKIE_NAME

        if chosen_name != default_name and default_name in response.cookies:
            morsel = response.cookies.pop(default_name)

            # Build kwargs preserving important attributes
            kwargs = {}
            if morsel.get('max-age'):
                try:
                    kwargs['max_age'] = int(morsel['max-age'])
                except Exception:
                    kwargs['max_age'] = None
            if morsel.get('expires'):
                kwargs['expires'] = morsel['expires']

            # ✅ Ensure cookie path is always correct
            if chosen_name == getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid'):
                kwargs['path'] = '/admin/'
            else:
                kwargs['path'] = '/'

            if morsel.get('domain'):
                kwargs['domain'] = morsel['domain']
            kwargs['secure'] = bool(morsel.get('secure'))
            kwargs['httponly'] = bool(morsel.get('httponly'))
            if morsel.get('samesite'):
                kwargs['samesite'] = morsel['samesite']

            final_kwargs = {k: v for k, v in kwargs.items() if v is not None}


            if chosen_name in response.cookies:
                existing_cookie = response.cookies[chosen_name]
                if chosen_name == getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid') and existing_cookie.get('path') != '/admin/':
                    response.cookies.pop(chosen_name)

            response.set_cookie(chosen_name, morsel.value, **final_kwargs)

        return response
