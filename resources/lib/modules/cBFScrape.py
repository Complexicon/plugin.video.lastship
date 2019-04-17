# -*- coding: utf-8 -*-
import re, sys, urllib2
from binascii import hexlify, unhexlify
from urlparse import urlparse
from resources.lib.modules import log_utils, pyaes, cookie_helper

class cBFScrape:
    COOKIE_NAME = 'BLAZINGFAST-WEB-PROTECT'

    def resolve(self, url, cookie_jar, user_agent):
        web_pdb.set_trace()
        headers = {'User-agent': user_agent, 'Referer': url}

        try:
            cookie_jar.load(ignore_discard=True)
        except Exception as e:
            log_utils.log(e)

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
        script_url = '%s://%s/blzgfst-shark/?bfu=/&blazing_answer=%s' % (parsed_url.scheme, parsed_url.netloc, blazing_answer)
        request = urllib2.Request(script_url)
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

    def checkBFCookie(self, content):
        """
        returns True if there seems to be a protection
        """
        return cBFScrape.COOKIE_NAME in content

    # not very robust but lazieness...
    def getCookieString(self, content):
        vars = re.findall('toNumbers\("([^"]+)"', content)
        if not vars:
            log_utils.log('vars not found')
            return False
        value = self._decrypt(vars[2], vars[0], vars[1])
        if not value:
            log_utils.log('value decryption failed')
            return False
        pattern = '"%s=".*?";([^"]+)"' % cBFScrape.COOKIE_NAME
        cookieMeta = re.findall(pattern, content)
        if not cookieMeta:
            log_utils.log('cookie meta not found')
        cookie = "%s=%s;%s" % (cBFScrape.COOKIE_NAME, value, cookieMeta[0])
        return cookie
        # + toHex(BFCrypt.decrypt(c, 2, a, b)) +

    def _decrypt(self, msg, key, iv):
        msg = unhexlify(msg)
        key = unhexlify(key)
        iv = unhexlify(iv)
        if len(iv) != 16:
            log_utils.log("iv length is" + str(len(iv)) + " must be 16.")
            return False
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        plain_text = decrypter.feed(msg)
        plain_text += decrypter.feed()
        f = hexlify(plain_text)
        return f
