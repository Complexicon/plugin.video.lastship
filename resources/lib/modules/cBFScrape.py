# -*- coding: utf-8 -*-
import re, urllib2, cookie_helper
from urlparse import urlparse


class cBFScrape:
    def resolve(self, url, cookie_jar, user_agent):
        Domain = re.sub(r'https*:\/\/([^/]+)(\/*.*)', '\\1', url)
        headers = {'User-agent': user_agent,
                   'Referer': url, 'Host': Domain,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Connection': 'keep-alive',
                   'Upgrade-Insecure-Requests': '1',
                   'Content-Type': 'text/html; charset=utf-8'}

        try:
            cookie_jar.load(ignore_discard=True)
        except Exception as e:
            print e

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        request = urllib2.Request(url)
        for key in headers:
            request.add_header(key, headers[key])

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e

        body = response.read()
        cookie_jar.extract_cookies(response, request)
        cookie_helper.check_cookies(cookie_jar)
        parsed_url = urlparse(url)
        blazing_answer = self._extract_js(body)
        submit_url = '%s://%s/blzgfst-shark/?bfu=/&blazing_answer=%s' % (parsed_url.scheme, parsed_url.netloc, blazing_answer)
        request = urllib2.Request(submit_url)
        for key in headers:
            request.add_header(key, headers[key])
        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e
        return response

    def _extract_js(self, body):
        blazing = []
        blazing_answer = re.findall(r'r.value(.*?);\n', body)[0]
        blazing_answer = re.sub(r'(.*)=', '', blazing_answer)
        blazing_answer = re.split(r'([\*\-\+\\])+', blazing_answer)
        for x in range(0, len(blazing_answer)):
            try:
                blazing.append(str(int(blazing_answer[x], 0)))
            except:
                blazing.append(blazing_answer[x])
        blazing_answer = ''  
        for x in range(0, len(blazing)):
            blazing_answer = blazing_answer + blazing[x]
        blazing_answer = eval(blazing_answer)
        return blazing_answer
