import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class CORSLoggingMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        logger.info(f"CORS Headers: {response.get('Access-Control-Allow-Origin')}")
        return response
