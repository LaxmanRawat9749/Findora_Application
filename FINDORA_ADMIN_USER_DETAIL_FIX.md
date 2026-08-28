this kind of message is showing in https://findora-application.onrender.com/admin/api/user/ 

TypeError at /admin/api/user/
args or kwargs must be provided.
Request Method:	GET
Request URL:	https://findora-application.onrender.com/admin/api/user/
Django Version:	6.0.7
Exception Type:	TypeError
Exception Value:	
args or kwargs must be provided.
Exception Location:	/opt/render/project/src/.venv/lib/python3.14/site-packages/django/utils/html.py, line 137, in format_html
Raised during:	django.contrib.admin.options.changelist_view
Python Executable:	/opt/render/project/src/.venv/bin/python3.14
Python Version:	3.14.3
Python Path:	
['/opt/render/project/src/findora_backend',
 '/opt/render/project/src/.venv/bin',
 '/opt/render/project/python/Python-3.14.3/lib/python314.zip',
 '/opt/render/project/python/Python-3.14.3/lib/python3.14',
 '/opt/render/project/python/Python-3.14.3/lib/python3.14/lib-dynload',
 '/opt/render/project/src/.venv/lib/python3.14/site-packages']
Server time:	Fri, 28 Aug 2026 12:39:59 +0000
Error during template rendering
In template /opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templates/admin/change_list.html, error at line 87

args or kwargs must be provided.
77	          {% block search %}{% search_form cl %}{% endblock %}
78	          {% block date_hierarchy %}{% if cl.date_hierarchy %}{% date_hierarchy cl %}{% endif %}{% endblock %}
79	
80	          <form id="changelist-form" method="post"{% if cl.formset and cl.formset.is_multipart %} enctype="multipart/form-data"{% endif %} novalidate>{% csrf_token %}
81	          {% if cl.formset %}
82	            <div>{{ cl.formset.management_form }}</div>
83	          {% endif %}
84	
85	          {% block result_list %}
86	            {% if action_form and actions_on_top and cl.show_admin_actions %}{% admin_actions %}{% endif %}
87	            {% result_list cl %}
88	            {% if action_form and actions_on_bottom and cl.show_admin_actions %}{% admin_actions %}{% endif %}
89	          {% endblock %}
90	          {% block pagination %}
91	            <div class="changelist-footer">
92	            {% pagination cl %}
93	            {% if cl.formset and cl.result_count %}<input type="submit" name="_save" class="default" value="{% translate 'Save' %}">{% endif %}
94	            </div>
95	          {% endblock %}
96	          </form>
97	        </div>
Traceback Switch to copy-and-paste view
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/models/options.py, line 684, in get_field
            return self.fields_map[field_name]
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
During handling of the above exception ('account_status'), another exception occurred:
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/utils.py, line 293, in lookup_field
        f = _get_non_gfk_field(opts, name)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/utils.py, line 333, in _get_non_gfk_field
    field = opts.get_field(name)
                 ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/db/models/options.py, line 686, in get_field
            raise FieldDoesNotExist(
                 ^ …
Local vars
During handling of the above exception (User has no field named 'account_status'), another exception occurred:
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/core/handlers/exception.py, line 55, in inner
                response = get_response(request)
                               ^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/core/handlers/base.py, line 221, in _get_response
                response = response.render()
                                ^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/response.py, line 114, in render
            self.content = self.rendered_content
                                ^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/response.py, line 92, in rendered_content
        return template.render(context, self._request)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/backends/django.py, line 107, in render
            return self.template.render(context)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 174, in render
                    return self._render(context)
                                ^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 166, in _render
        return self.nodelist.render(context)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1091, in render
        return SafeString("".join([node.render_annotated(context) for node in self]))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1052, in render_annotated
            return self.render(context)
                         ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/loader_tags.py, line 160, in render
            return compiled_parent._render(context)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 166, in _render
        return self.nodelist.render(context)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1091, in render
        return SafeString("".join([node.render_annotated(context) for node in self]))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1052, in render_annotated
            return self.render(context)
                         ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/loader_tags.py, line 160, in render
            return compiled_parent._render(context)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 166, in _render
        return self.nodelist.render(context)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1091, in render
        return SafeString("".join([node.render_annotated(context) for node in self]))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1052, in render_annotated
            return self.render(context)
                         ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/loader_tags.py, line 66, in render
                result = block.nodelist.render(context)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1091, in render
        return SafeString("".join([node.render_annotated(context) for node in self]))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1052, in render_annotated
            return self.render(context)
                         ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/loader_tags.py, line 66, in render
                result = block.nodelist.render(context)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1091, in render
        return SafeString("".join([node.render_annotated(context) for node in self]))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/base.py, line 1052, in render_annotated
            return self.render(context)
                         ^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templatetags/base.py, line 47, in render
        return super().render(context)
                   ^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/template/library.py, line 363, in render
        _dict = self.func(*resolved_args, **resolved_kwargs)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templatetags/admin_list.py, line 357, in result_list
        "results": list(results(cl)),
                        ^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templatetags/admin_list.py, line 333, in results
            yield ResultList(None, items_for_result(cl, res, None))
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templatetags/admin_list.py, line 324, in __init__
        super().__init__(*items)
             ^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/templatetags/admin_list.py, line 221, in items_for_result
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/contrib/admin/utils.py, line 302, in lookup_field
            value = attr(obj)
                         ^^^^^^^^^ …
Local vars
/opt/render/project/src/findora_backend/api/admin.py, line 118, in account_status
        return format_html('<span style="background:#DCFCE7;color:#16A34A;padding:2px 8px;border-radius:4px;font-weight:600">Active</span>')
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
/opt/render/project/src/.venv/lib/python3.14/site-packages/django/utils/html.py, line 137, in format_html
        raise TypeError("args or kwargs must be provided.")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ …
Local vars
Request information
USER
admin (admin)

GET
No GET data

POST
No POST data

FILES
No FILES data

COOKIES
Variable	Value
csrftoken	
'********************'
sessionid	
'********************'
META
Variable	Value
CSRF_COOKIE	
'71iJeApimTKMdQQEPmKxXsQdqmTraafn'
CSRF_COOKIE_NEEDS_UPDATE	
True
HTTP_ACCEPT	
'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
HTTP_ACCEPT_ENCODING	
'gzip, br'
HTTP_ACCEPT_LANGUAGE	
'en-US,en;q=0.9,ne;q=0.8'
HTTP_CDN_LOOP	
'cloudflare; loops=1'
HTTP_CF_CONNECTING_IP	
'103.129.135.171'
HTTP_CF_IPCOUNTRY	
'NP'
HTTP_CF_RAY	
'a32361bc5a5aa1b3-SIN'
HTTP_CF_VISITOR	
'{"scheme":"https"}'
HTTP_COOKIE	
'********************'
HTTP_HOST	
'findora-application.onrender.com'
HTTP_PRIORITY	
'u=0, i'
HTTP_REFERER	
'https://findora-application.onrender.com/admin/api/claim/'
HTTP_RENDER_PROXY_TTL	
'4'
HTTP_RNDR_ID	
'aa6f3a52-ab4a-4db4'
HTTP_SEC_CH_UA	
'"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"'
HTTP_SEC_CH_UA_MOBILE	
'?0'
HTTP_SEC_CH_UA_PLATFORM	
'"Windows"'
HTTP_SEC_FETCH_DEST	
'document'
HTTP_SEC_FETCH_MODE	
'navigate'
HTTP_SEC_FETCH_SITE	
'same-origin'
HTTP_SEC_FETCH_USER	
'?1'
HTTP_TRUE_CLIENT_IP	
'103.129.135.171'
HTTP_UPGRADE_INSECURE_REQUESTS	
'1'
HTTP_USER_AGENT	
('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like '
 'Gecko) Chrome/151.0.0.0 Safari/537.36')
HTTP_X_FORWARDED_FOR	
'103.129.135.171, 172.69.166.94, 10.28.245.82'
HTTP_X_FORWARDED_PROTO	
'https'
HTTP_X_REQUEST_START	
'1787920798655154'
PATH_INFO	
'/admin/api/user/'
QUERY_STRING	
''
RAW_URI	
'/admin/api/user/'
REMOTE_ADDR	
'127.0.0.1'
REMOTE_PORT	
'55380'
REQUEST_METHOD	
'GET'
SCRIPT_NAME	
''
SERVER_NAME	
'0.0.0.0'
SERVER_PORT	
'10000'
SERVER_PROTOCOL	
'HTTP/1.1'
SERVER_SOFTWARE	
'gunicorn/26.0.0'
gunicorn.socket	
<socket.socket fd=7, family=2, type=1, proto=0, laddr=('127.0.0.1', 10000), raddr=('127.0.0.1', 55380)>
wsgi.early_hints	
<function _make_early_hints_callback.<locals>.send_early_hints at 0x7c0f841a68d0>
wsgi.errors	
<gunicorn.http.wsgi.WSGIErrorsWrapper object at 0x7c0f84286260>
wsgi.file_wrapper	
<class 'gunicorn.http.wsgi.FileWrapper'>
wsgi.input	
<gunicorn.http.body.Body object at 0x7c0f8418ca70>
wsgi.input_terminated	
True
wsgi.multiprocess	
False
wsgi.multithread	
False
wsgi.run_once	
False
wsgi.url_scheme	
'https'
wsgi.version	
(1, 0)
Settings
Using settings module config.settings
Setting	Value
ABSOLUTE_URL_OVERRIDES	
{}
ADMINS	
[]
ALLOWED_HOSTS	
['*']
APPEND_SLASH	
True
AUTHENTICATION_BACKENDS	
'********************'
AUTH_PASSWORD_VALIDATORS	
'********************'
AUTH_USER_MODEL	
'********************'
BASE_DIR	
PosixPath('/opt/render/project/src/findora_backend')
BREVO_API_KEY	
'********************'
CACHES	
{'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
CACHE_MIDDLEWARE_ALIAS	
'default'
CACHE_MIDDLEWARE_KEY_PREFIX	
'********************'
CACHE_MIDDLEWARE_SECONDS	
600
CORS_ALLOW_ALL_ORIGINS	
True
CORS_ALLOW_CREDENTIALS	
True
CSRF_COOKIE_AGE	
31449600
CSRF_COOKIE_DOMAIN	
None
CSRF_COOKIE_HTTPONLY	
False
CSRF_COOKIE_NAME	
'csrftoken'
CSRF_COOKIE_PATH	
'/'
CSRF_COOKIE_SAMESITE	
'Lax'
CSRF_COOKIE_SECURE	
False
CSRF_FAILURE_VIEW	
'django.views.csrf.csrf_failure'
CSRF_HEADER_NAME	
'HTTP_X_CSRFTOKEN'
CSRF_TRUSTED_ORIGINS	
[]
CSRF_USE_SESSIONS	
False
DATABASES	
{'default': {'ATOMIC_REQUESTS': False,
             'AUTOCOMMIT': True,
             'CONN_HEALTH_CHECKS': False,
             'CONN_MAX_AGE': 600,
             'DISABLE_SERVER_SIDE_CURSORS': False,
             'ENGINE': 'django.db.backends.postgresql',
             'HOST': 'dpg-da2q3g5g1s2s73d7k2sg-a.singapore-postgres.render.com',
             'NAME': 'findora_database_1ea0',
             'OPTIONS': {},
             'PASSWORD': '********************',
             'PORT': '',
             'TEST': {'CHARSET': None,
                      'COLLATION': None,
                      'MIGRATE': True,
                      'MIRROR': None,
                      'NAME': None},
             'TIME_ZONE': None,
             'USER': 'findora_database_1ea0_user'}}
DATABASE_ROUTERS	
[]
DATA_UPLOAD_MAX_MEMORY_SIZE	
2621440
DATA_UPLOAD_MAX_NUMBER_FIELDS	
1000
DATA_UPLOAD_MAX_NUMBER_FILES	
100
DATETIME_FORMAT	
'N j, Y, P'
DATETIME_INPUT_FORMATS	
['%Y-%m-%d %H:%M:%S',
 '%Y-%m-%d %H:%M:%S.%f',
 '%Y-%m-%d %H:%M',
 '%m/%d/%Y %H:%M:%S',
 '%m/%d/%Y %H:%M:%S.%f',
 '%m/%d/%Y %H:%M',
 '%m/%d/%y %H:%M:%S',
 '%m/%d/%y %H:%M:%S.%f',
 '%m/%d/%y %H:%M']
DATE_FORMAT	
'N j, Y'
DATE_INPUT_FORMATS	
['%Y-%m-%d',
 '%m/%d/%Y',
 '%m/%d/%y',
 '%b %d %Y',
 '%b %d, %Y',
 '%d %b %Y',
 '%d %b, %Y',
 '%B %d %Y',
 '%B %d, %Y',
 '%d %B %Y',
 '%d %B, %Y']
DEBUG	
True
DEBUG_PROPAGATE_EXCEPTIONS	
False
DECIMAL_SEPARATOR	
'.'
DEFAULT_AUTO_FIELD	
'django.db.models.BigAutoField'
DEFAULT_CHARSET	
'utf-8'
DEFAULT_EXCEPTION_REPORTER	
'django.views.debug.ExceptionReporter'
DEFAULT_EXCEPTION_REPORTER_FILTER	
'django.views.debug.SafeExceptionReporterFilter'
DEFAULT_FROM_EMAIL	
'Findora <rawatlaxman089@gmail.com>'
DEFAULT_INDEX_TABLESPACE	
''
DEFAULT_TABLESPACE	
''
DISALLOWED_USER_AGENTS	
[]
EMAIL_BACKEND	
'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST	
'localhost'
EMAIL_HOST_PASSWORD	
'********************'
EMAIL_HOST_USER	
''
EMAIL_PORT	
25
EMAIL_SSL_CERTFILE	
None
EMAIL_SSL_KEYFILE	
'********************'
EMAIL_SUBJECT_PREFIX	
'[Django] '
EMAIL_TIMEOUT	
None
EMAIL_USE_LOCALTIME	
False
EMAIL_USE_SSL	
False
EMAIL_USE_TLS	
False
FILE_UPLOAD_DIRECTORY_PERMISSIONS	
None
FILE_UPLOAD_HANDLERS	
['django.core.files.uploadhandler.MemoryFileUploadHandler',
 'django.core.files.uploadhandler.TemporaryFileUploadHandler']
FILE_UPLOAD_MAX_MEMORY_SIZE	
2621440
FILE_UPLOAD_PERMISSIONS	
420
FILE_UPLOAD_TEMP_DIR	
None
FIRST_DAY_OF_WEEK	
0
FIXTURE_DIRS	
[]
FORCE_SCRIPT_NAME	
None
FORMAT_MODULE_PATH	
None
FORM_RENDERER	
'django.forms.renderers.DjangoTemplates'
IGNORABLE_404_URLS	
[]
INSTALLED_APPS	
['django.contrib.admin',
 'django.contrib.auth',
 'django.contrib.contenttypes',
 'django.contrib.sessions',
 'django.contrib.messages',
 'django.contrib.staticfiles',
 'rest_framework',
 'rest_framework_simplejwt',
 'rest_framework_simplejwt.token_blacklist',
 'corsheaders',
 'api']
INTERNAL_IPS	
[]
KHALTI_API_URL	
'********************'
KHALTI_SECRET_KEY	
'********************'
LANGUAGES	
[('af', 'Afrikaans'),
 ('ar', 'Arabic'),
 ('ar-dz', 'Algerian Arabic'),
 ('ast', 'Asturian'),
 ('az', 'Azerbaijani'),
 ('bg', 'Bulgarian'),
 ('be', 'Belarusian'),
 ('bn', 'Bengali'),
 ('br', 'Breton'),
 ('bs', 'Bosnian'),
 ('ca', 'Catalan'),
 ('ckb', 'Central Kurdish (Sorani)'),
 ('cs', 'Czech'),
 ('cy', 'Welsh'),
 ('da', 'Danish'),
 ('de', 'German'),
 ('dsb', 'Lower Sorbian'),
 ('el', 'Greek'),
 ('en', 'English'),
 ('en-au', 'Australian English'),
 ('en-gb', 'British English'),
 ('eo', 'Esperanto'),
 ('es', 'Spanish'),
 ('es-ar', 'Argentinian Spanish'),
 ('es-co', 'Colombian Spanish'),
 ('es-mx', 'Mexican Spanish'),
 ('es-ni', 'Nicaraguan Spanish'),
 ('es-ve', 'Venezuelan Spanish'),
 ('et', 'Estonian'),
 ('eu', 'Basque'),
 ('fa', 'Persian'),
 ('fi', 'Finnish'),
 ('fr', 'French'),
 ('fy', 'Frisian'),
 ('ga', 'Irish'),
 ('gd', 'Scottish Gaelic'),
 ('gl', 'Galician'),
 ('he', 'Hebrew'),
 ('hi', 'Hindi'),
 ('hr', 'Croatian'),
 ('hsb', 'Upper Sorbian'),
 ('ht', 'Haitian Creole'),
 ('hu', 'Hungarian'),
 ('hy', 'Armenian'),
 ('ia', 'Interlingua'),
 ('id', 'Indonesian'),
 ('ig', 'Igbo'),
 ('io', 'Ido'),
 ('is', 'Icelandic'),
 ('it', 'Italian'),
 ('ja', 'Japanese'),
 ('ka', 'Georgian'),
 ('kab', 'Kabyle'),
 ('kk', 'Kazakh'),
 ('km', 'Khmer'),
 ('kn', 'Kannada'),
 ('ko', 'Korean'),
 ('ky', 'Kyrgyz'),
 ('lb', 'Luxembourgish'),
 ('lt', 'Lithuanian'),
 ('lv', 'Latvian'),
 ('mk', 'Macedonian'),
 ('ml', 'Malayalam'),
 ('mn', 'Mongolian'),
 ('mr', 'Marathi'),
 ('ms', 'Malay'),
 ('my', 'Burmese'),
 ('nb', 'Norwegian Bokmål'),
 ('ne', 'Nepali'),
 ('nl', 'Dutch'),
 ('nn', 'Norwegian Nynorsk'),
 ('os', 'Ossetic'),
 ('pa', 'Punjabi'),
 ('pl', 'Polish'),
 ('pt', 'Portuguese'),
 ('pt-br', 'Brazilian Portuguese'),
 ('ro', 'Romanian'),
 ('ru', 'Russian'),
 ('sk', 'Slovak'),
 ('sl', 'Slovenian'),
 ('sq', 'Albanian'),
 ('sr', 'Serbian'),
 ('sr-latn', 'Serbian Latin'),
 ('sv', 'Swedish'),
 ('sw', 'Swahili'),
 ('ta', 'Tamil'),
 ('te', 'Telugu'),
 ('tg', 'Tajik'),
 ('th', 'Thai'),
 ('tk', 'Turkmen'),
 ('tr', 'Turkish'),
 ('tt', 'Tatar'),
 ('udm', 'Udmurt'),
 ('ug', 'Uyghur'),
 ('uk', 'Ukrainian'),
 ('ur', 'Urdu'),
 ('uz', 'Uzbek'),
 ('vi', 'Vietnamese'),
 ('zh-hans', 'Simplified Chinese'),
 ('zh-hant', 'Traditional Chinese')]
LANGUAGES_BIDI	
['he', 'ar', 'ar-dz', 'ckb', 'fa', 'ug', 'ur']
LANGUAGE_CODE	
'en-us'
LANGUAGE_COOKIE_AGE	
None
LANGUAGE_COOKIE_DOMAIN	
None
LANGUAGE_COOKIE_HTTPONLY	
False
LANGUAGE_COOKIE_NAME	
'django_language'
LANGUAGE_COOKIE_PATH	
'/'
LANGUAGE_COOKIE_SAMESITE	
None
LANGUAGE_COOKIE_SECURE	
False
LOCALE_PATHS	
[]
LOGGING	
{'disable_existing_loggers': False,
 'formatters': {'simple': {'format': '{levelname} {message}', 'style': '{'},
                'verbose': {'datefmt': '%Y-%m-%d %H:%M:%S',
                            'format': '[{asctime}] {levelname} {name}: '
                                      '{message}',
                            'style': '{'}},
 'handlers': {'console': {'class': 'logging.StreamHandler',
                          'formatter': 'verbose'}},
 'loggers': {'api': '********************',
             'django.db.backends': {'handlers': ['console'],
                                    'level': 'WARNING',
                                    'propagate': False},
             'django.request': {'handlers': ['console'],
                                'level': 'WARNING',
                                'propagate': False}},
 'root': {'handlers': ['console'], 'level': 'INFO'},
 'version': 1}
LOGGING_CONFIG	
'logging.config.dictConfig'
LOGIN_REDIRECT_URL	
'/accounts/profile/'
LOGIN_URL	
'/accounts/login/'
LOGOUT_REDIRECT_URL	
None
MANAGERS	
[]
MEDIA_ROOT	
PosixPath('/opt/render/project/src/findora_backend/media')
MEDIA_URL	
'/media/'
MESSAGE_STORAGE	
'django.contrib.messages.storage.fallback.FallbackStorage'
MIDDLEWARE	
['corsheaders.middleware.CorsMiddleware',
 'django.middleware.security.SecurityMiddleware',
 'whitenoise.middleware.WhiteNoiseMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware',
 'api.middleware.RequestTimingMiddleware']
MIGRATION_MODULES	
{}
MONTH_DAY_FORMAT	
'F j'
NUMBER_GROUPING	
0
PASSWORD_HASHERS	
'********************'
PASSWORD_RESET_TIMEOUT	
'********************'
PAYMENT_ENV	
'test'
PREPEND_WWW	
False
REST_FRAMEWORK	
{'DEFAULT_AUTHENTICATION_CLASSES': '********************',
 'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',
                            'rest_framework.parsers.MultiPartParser',
                            'rest_framework.parsers.FormParser'),
 'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
 'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',)}
ROOT_URLCONF	
'config.urls'
SECRET_KEY	
'********************'
SECRET_KEY_FALLBACKS	
'********************'
SECURE_CONTENT_TYPE_NOSNIFF	
True
SECURE_CROSS_ORIGIN_OPENER_POLICY	
'same-origin'
SECURE_CSP	
{}
SECURE_CSP_REPORT_ONLY	
{}
SECURE_HSTS_INCLUDE_SUBDOMAINS	
False
SECURE_HSTS_PRELOAD	
False
SECURE_HSTS_SECONDS	
0
SECURE_PROXY_SSL_HEADER	
None
SECURE_REDIRECT_EXEMPT	
[]
SECURE_REFERRER_POLICY	
'same-origin'
SECURE_SSL_HOST	
None
SECURE_SSL_REDIRECT	
False
SERVER_EMAIL	
'root@localhost'
SESSION_CACHE_ALIAS	
'default'
SESSION_COOKIE_AGE	
1209600
SESSION_COOKIE_DOMAIN	
None
SESSION_COOKIE_HTTPONLY	
True
SESSION_COOKIE_NAME	
'sessionid'
SESSION_COOKIE_PATH	
'/'
SESSION_COOKIE_SAMESITE	
'Lax'
SESSION_COOKIE_SECURE	
False
SESSION_ENGINE	
'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE	
False
SESSION_FILE_PATH	
None
SESSION_SAVE_EVERY_REQUEST	
False
SESSION_SERIALIZER	
'django.contrib.sessions.serializers.JSONSerializer'
SETTINGS_MODULE	
'config.settings'
SHORT_DATETIME_FORMAT	
'm/d/Y P'
SHORT_DATE_FORMAT	
'm/d/Y'
SIGNED_COOKIE_LEGACY_SALT_FALLBACK	
True
SIGNING_BACKEND	
'django.core.signing.TimestampSigner'
SILENCED_SYSTEM_CHECKS	
[]
SIMPLE_JWT	
{'ACCESS_TOKEN_LIFETIME': '********************',
 'ALGORITHM': 'HS256',
 'AUTH_HEADER_NAME': '********************',
 'AUTH_HEADER_TYPES': '********************',
 'BLACKLIST_AFTER_ROTATION': True,
 'REFRESH_TOKEN_LIFETIME': '********************',
 'ROTATE_REFRESH_TOKENS': '********************',
 'UPDATE_LAST_LOGIN': True,
 'USER_ID_CLAIM': 'user_id',
 'USER_ID_FIELD': 'id'}
STATICFILES_DIRS	
[]
STATICFILES_FINDERS	
['django.contrib.staticfiles.finders.FileSystemFinder',
 'django.contrib.staticfiles.finders.AppDirectoriesFinder']
STATIC_ROOT	
PosixPath('/opt/render/project/src/findora_backend/staticfiles')
STATIC_URL	
'/static/'
STORAGES	
{'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
TASKS	
{'default': {'BACKEND': 'django.tasks.backends.immediate.ImmediateBackend'}}
TEMPLATES	
[{'APP_DIRS': True,
  'BACKEND': 'django.template.backends.django.DjangoTemplates',
  'DIRS': [],
  'OPTIONS': {'context_processors': ['django.template.context_processors.request',
                                     'django.contrib.auth.context_processors.auth',
                                     'django.contrib.messages.context_processors.messages']}}]
TEST_NON_SERIALIZED_APPS	
[]
TEST_RUNNER	
'django.test.runner.DiscoverRunner'
THOUSAND_SEPARATOR	
','
TIME_FORMAT	
'P'
TIME_INPUT_FORMATS	
['%H:%M:%S', '%H:%M:%S.%f', '%H:%M']
TIME_ZONE	
'UTC'
URLIZE_ASSUME_HTTPS	
False
USE_I18N	
True
USE_THOUSAND_SEPARATOR	
False
USE_TZ	
True
USE_X_FORWARDED_HOST	
False
USE_X_FORWARDED_PORT	
False
WSGI_APPLICATION	
'config.wsgi.application'
X_FRAME_OPTIONS	
'DENY'
YEAR_MONTH_FORMAT	
'F Y'
You’re seeing this error because you have DEBUG = True in your Django settings file. Change that to False, and Django will display a standard page generated by the handler for this status code.