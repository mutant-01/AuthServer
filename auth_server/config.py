"""configs outside of app context"""
import os


url_prefix = os.environ.get('URL_PREFIX', '/auth')
