from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
import ssl
import certifi

class CustomSSLMiddleware(HttpProxyMiddleware):
    def process_request(self, request, spider):
        request.meta['verify'] = False