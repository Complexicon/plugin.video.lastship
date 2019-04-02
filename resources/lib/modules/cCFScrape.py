# -*- coding: utf-8 -*-
from __future__ import division
import urllib, urllib2, re, sys
from time import sleep
from urlparse import urlparse
from jsunfuck import JSUnfuck


def GetItemAlone(string, separator=' '):
    l = len(string) - 1
    ret = ''
    i = -1
    p = 0
    a = 0
    b = 0
    c1 = 0
    c2 = 0
    n = False
    last_char = ''

    s = False

    while (i < l):
        i += 1
        ch = string[i]
        ret = ret + ch
        n = False

        if (ch in separator) and not p and not a and not b and not c1 and not c2 and not n and (i > 0):
            return ret[:-1]

        if (ch.isspace()):
            continue

        if ch == '"' and not GetPrevchar(string, i) == '\\' and not c2:
            c1 = 1 - c1
        if ch == "'" and not GetPrevchar(string, i) == '\\' and not c1:
            c2 = 1 - c2

        if not c1 and not c2:
            if ch == '(':
                p += 1
            elif ch == ')':
                p -= 1
            elif ch == '{':
                a += 1
            elif ch == '}':
                a -= 1
            elif ch == '[':
                b += 1
            elif ch == ']':
                b -= 1
            if ch == '.' and not ((last_char in '0123456789') or (string[i + 1] in '0123456789')):
                n = True

        if (ch in separator) and not p and not a and not b and not c1 and not c2 and not n and (i > 0):
            return ret
        last_char = ch
    return ret


def solvecharcode(chain, t):
    v = chain.find('t.charCodeAt') + 12
    if v == 11:
        return chain
    dat = GetItemAlone(chain[v:], ')')
    r = parseInt(dat)
    v = ord(t[int(r)])
    chain = chain.replace('t.charCodeAt' + dat, '+' + str(v))
    chain = chain.replace('(' + '+' + str(v) + ')', '+' + str(v))
    return chain


def checkpart(s, sens):
    number = 0
    p = 0
    if sens == 1:
        pos = 0
    else:
        pos = len(s) - 1

    try:
        while 1:
            c = s[pos]

            if ((c == '(') and (sens == 1)) or ((c == ')') and (sens == -1)):
                p = p + 1
            if ((c == ')') and (sens == 1)) or ((c == '(') and (sens == -1)):
                p = p - 1
            if (c == '+') and (p == 0) and (number > 1):
                break

            number += 1
            pos = pos + sens
    except:
        pass
    if sens == 1:
        return s[:number], number
    else:
        return s[-number:], number


def parseInt(s):
    v = JSUnfuck(s).decode(False)
    v = re.sub('([^\(\)])\++', '\\1', v)
    v = eval(v)
    return v


class cCFScrape:
    def resolve(self, url, cookie_jar, user_agent):
        Domain = re.sub(r'https*:\/\/([^/]+)(\/*.*)', '\\1', url)
        headers = {'User-agent': user_agent,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                   'Accept-Encoding': 'gzip, deflate',
                   'Connection': 'keep-alive',
                   'Upgrade-Insecure-Requests': '1',
                   'Content-Type': 'text/html; charset=utf-8'}

        try:
            cookie_jar.load(ignore_discard=True)
        except Exception as e:
            print (e)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        request = urllib2.Request(url)
        for key in headers:
            request.add_header(key, headers[key])

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e

        if response.code != 503:
            return response

        body = response.read()
        cookie_jar.extract_cookies(response, request)
        cCFScrape.__checkCookie(cookie_jar)
        parsed_url = urlparse(url)
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, parsed_url.netloc)
        params = {}

        try:
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)
            params["s"] = re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body).group(1)
            js = self._extract_js(body, parsed_url.netloc)
        except:
            return None

        params["jschl_answer"] = js
        sParameters = urllib.urlencode(params, True)
        request = urllib2.Request("%s?%s" % (submit_url, sParameters))
        for key in headers:
            request.add_header(key, headers[key])
        sleep(5)

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e
        return response

    @staticmethod
    def __checkCookie(cookieJar):
        for entry in cookieJar:
            if entry.expires > sys.maxint:
                entry.expires = sys.maxint

    @staticmethod
    def _extract_js(htmlcontent, domain):
        try:
            rq = re.search('<div style="display:none;visibility:hidden;" id="(.*?)">(.*?)<\/div>', str(htmlcontent), re.DOTALL)
            id = rq.group(1)
            val = rq.group(2)
            htmlcontent = re.sub(
                r'function\(p\){var p = eval\(eval\(atob\(".*?"\)\+\(undefined\+""\)\[1\]\+\(true\+""\)\[0\]\+\(\+\(\+!\+\[\]\+\[\+!\+\[\]\]\+\(!!\[\]\+\[\]\)\[!\+\[\]\+!\+\[\]\+!\+\[\]\]\+\[!\+\[\]\+!\+\[\]\]\+\[\+\[\]\]\)\+\[\]\)\[\+!\+\[\]\]\+\(false\+\[0\]\+String\)\[20\]\+\(true\+""\)\[3\]\+\(true\+""\)\[0\]\+"Element"\+\(\+\[\]\+Boolean\)\[10\]\+\(NaN\+\[Infinity\]\)\[10\]\+"Id\("\+\(\+\(20\)\)\["to"\+String\["name"\]\]\(21\)\+"\)."\+atob\(".*?"\)\)\); return \+\(p\)}\(\);', "{};".format(rq.group(2)), str(htmlcontent))
            http = float('0')
        except:
            http = len(domain)
            pass
        line1 = re.findall('var s,t,o,p,b,r,e,a,k,i,n,g,f, (.+?)={"(.+?)":\+*(.+?)};', str(htmlcontent))
        varname = line1[0][0] + '.' + line1[0][1]
        calc = parseInt(line1[0][2])
        js = htmlcontent
        js = re.sub(r"a\.value = ((.+).toFixed\(10\))?", r"\1", js)
        js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js).replace("t.length", str(len(domain)))
        js = js.replace('; 121', '')
        js = js.replace(
            'function(p){return eval((true+"")[0]+"."+([]["fill"]+"")[3]+(+(101))["to"+String["name"]](21)[1]+(false+"")[1]+(true+"")[1]+Function("return escape")()(("")["italics"]())[2]+(true+[]["fill"])[10]+(undefined+"")[2]+(true+"")[3]+(+[]+Array)[10]+(true+"")[0]+"("+p+")")}',
            't.charCodeAt')
        js = re.sub(r"[\n\\']", "", js)
        js = solvecharcode(js, domain)

        htmlcontent = js

        AllLines = re.findall(';' + varname + '([*\-+])=([^;]+)', (htmlcontent))

        for aEntry in AllLines:
            calc = eval(format(calc, '.17g') + (aEntry[0]) + format(parseInt(aEntry[1]), '.17g'))
        rep = calc + http
        return format(rep, '.10f')
