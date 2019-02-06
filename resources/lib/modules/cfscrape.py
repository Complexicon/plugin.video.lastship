import logging
import random
import re
import subprocess
from copy import deepcopy
from time import sleep
import requests
from resources.lib.modules import cfdecoder

from requests.sessions import Session

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

__version__ = "1.9.5"

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; Moto G (5) Build/NPPS25.137-93-8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"
]
DEFAULT_USER_AGENT = random.choice(DEFAULT_USER_AGENTS)

ANSWER_ACCEPT_ERROR = """\
The challenge answer was not properly accepted by Cloudflare. This can occur if \
the target website is under heavy load, or if Cloudflare is experiencing issues. You can
potentially resolve this by increasing the challenge answer delay (default: 5 seconds). \
For example: cfscrape.create_scraper(delay=10)
If increasing the delay does not help, please open a GitHub issue at \
https://github.com/Anorov/cloudflare-scrape/issues\
"""

class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
        self.delay = kwargs.pop("delay", 0)
        super(CloudflareScraper, self).__init__(*args, **kwargs)

        if "requests" in self.headers["User-Agent"]:
            self.headers["User-Agent"] = DEFAULT_USER_AGENT

    def is_cloudflare_challenge(self, resp):
        return (
            resp.status_code == 503
            and resp.headers.get("Server", "").startswith("cloudflare")
            and b"jschl_vc" in resp.content
            and b"jschl_answer" in resp.content
        )

    def request(self, method, url, *args, **kwargs):
        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        # Check if Cloudflare anti-bot is on
        if self.is_cloudflare_challenge(resp):
            resp = self.solve_cf_challenge(resp, **kwargs)
            if self.is_cloudflare_challenge(resp):
                raise ValueError(ANSWER_ACCEPT_ERROR)

        return resp

    def solve_cf_challenge(self, resp, **original_kwargs):
        sleep(self.delay)
		
        domain = urlparse(resp.url).netloc
        cloudflare_kwargs = deepcopy(original_kwargs)
        params = cloudflare_kwargs.setdefault("params", {})
        headers = cloudflare_kwargs.setdefault("headers", {})
		
        headers["Host"] = domain
        headers["Referer"] = resp.url
        headers["Accept"]= 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers["Content-Type"]= 'text/html; charset=utf-8'

        request = {}
        request['url'] = resp.url
        request['data'] = resp.content
        request['headers'] = resp.headers
        submit_url = cfdecoder.Cloudflare(request).get_url()

        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False
        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        return self.request(method, redirect.headers["Location"], **original_kwargs)

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudflareScraper object.
        """
        scraper = cls(**kwargs)

        if sess:
            attrs = ["auth", "cert", "cookies", "headers", "hooks", "params", "proxies", "data"]
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    ## Functions for integrating cloudflare-scrape with other applications and scripts
    @classmethod
    def get_tokens(cls, url, user_agent=None, **kwargs):
        scraper = cls.create_scraper()
        if user_agent:
            scraper.headers["User-Agent"] = user_agent

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            logging.error("'%s' returned an error. Could not collect tokens." % url)
            raise

        domain = urlparse(resp.url).netloc
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith(".") and d in ("." + domain):
                cookie_domain = d
                break
        else:
            raise ValueError("Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return ({
                    "__cfduid": scraper.cookies.get("__cfduid", "", domain=cookie_domain),
                    "cf_clearance": scraper.cookies.get("cf_clearance", "", domain=cookie_domain)
                },
                scraper.headers["User-Agent"]
               )

    @classmethod
    def get_cookie_string(cls, url, user_agent=None, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, user_agent=user_agent, **kwargs)
        return "; ".join("=".join(pair) for pair in tokens.items()), user_agent

create_scraper = CloudflareScraper.create_scraper
get_tokens = CloudflareScraper.get_tokens
get_cookie_string = CloudflareScraper.get_cookie_string

scraper = create_scraper()