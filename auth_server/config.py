"""configs outside of app context"""
import os


url_prefix = os.environ.get('URL_PREFIX', 'auth')
url_prefix = url_prefix if url_prefix.startswith("/") else "/" + url_prefix
