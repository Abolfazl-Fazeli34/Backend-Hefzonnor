import sys, os

sys.path.insert(0, '/home/ytxeaprn/hefzonnor')

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
