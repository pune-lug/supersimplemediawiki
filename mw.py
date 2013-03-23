#!/usr/bin/env python3
"""
License: The MIT License (http://opensource.org/licenses/MIT)
"""

import requests

class SSMWError(Exception):
    pass

class Wiki:
    def __init__(self, api_url, headers=None):
        self.s = requests.Session()
        self.api_url = api_url
        self.cookies = None
        self.username = None
        self.format = 'json'
        self.inprop = [
            'protection',
            'talkid',
            'watched',
            'subjectid',
            'url',
            'readable',
            'preload',
            'displaytitle'
        ]
        self.intoken = [
            'edit',
            'delete',
            'protect',
            'move',
            'block',
            'unblock',
            'email',
            'import',
            'watch'
        ]
        if headers:
            self.headers = headers
        else:
            self.headers = {'User-agent':'supersimplemediawiki'}

    def login(self, username, passwd):
        """
        Logs the user in.
        @param username Account's username
        @type username str
        @param passwd Account's password
        @type passwd str
        """
        self.username = username
        data = {'action':'login',
                'lgname':username,
                'lgpassword':passwd,
                'format':self.format
        }
        r1 = self.s.post(self.api_url, params=data, headers=self.headers)
        if not r1.ok:
            raise SSMWError(r1.text)
        if not r1.json():
            raise SSMWError(r1.text)
        token = r1.json()['login']['token']
        data['lgtoken'] = token
        self.cookies = r1.cookies
        r1 = self.s.post(self.api_url, params=data, headers=self.headers, cookies=self.cookies)
        if not r1.ok:
            raise SSMWError(r1.text)
        self.cookies = r1.cookies

    def request(self, params, post=False, headers=None):
        """
        Makes an API request with the given params.
        Returns the page in a dict format
        """
        r = self.fetch(params=params, post=post, headers=headers)
        try:
            return r.json()
        except:
            raise SSMWError(r.text)

    def fetch(self, url=None, params=None, post=False, headers=None):
        if not url:
            url = self.api_url
        if 'format' not in params:
            params['format'] = self.format
        hdrs = self.headers
        if headers:
            hdrs.update(headers)
        if post:
            r = self.s.post(url, params=params, cookies=self.cookies, headers=hdrs)
        else:
            r = self.s.get(url, params=params, cookies=self.cookies, headers=hdrs)
        if not r.ok:
            raise SSMWError(r.text)
        return r

    def get_edittoken(self):
        params = {}
        params['action'] = 'query'
        params['prop'] = 'info'
        params['intoken'] = 'edit'
        params['titles'] = 'a'
        r = self.request(params)
        for x in r['query']['pages']:
            if r['query']['pages'][x].get('edittoken', None):
                self.edittoken = r['query']['pages'][x]['edittoken']
        print(self.edittoken)

    def logout(self):
        params = {}
        params['action'] = 'logout'
        r = self.request(params=params)
        return r

    def get_page(self, title, inprop=None, intoken=None):
        if not inprop:
            inprop = self.inprop
        if not intoken:
            intoken = self.intoken
        params = {
            'action': 'query',
            'prop': 'info|revisions',
            'titles': title,
            'inprop': inprop,
            'intoken': intoken,
            'rvlimit': 1,
            'rvprop': 'content'
        }
        data = self.request(params)
        x = data['query']['pages']
        for i in x:
            if x[i].get('revisions', None):
                text = x[i]['revisions'][0]['*']
                break
        self.title = title
        self.text = text
        return(text)

    def edit_page(self,
                  text=None,
                  minor=True,
                  bot=True,
                  force_edit=False,
                  createonly=False,
                  nocreate=False,
                  md5=None,
                  assert_='user',
                  notminor=False,
                  section=None,
                  summary=None,
                  appendtext=None,
                  prependtext=None):
        if not vars(self).get('text', None):
            self.text = None
        if not force_edit and text == self.text:
            print('Ignoring edit...')
            return
        t = {}
        t['format'] = self.format
        t['action'] = 'edit'
        t['title'] = self.title
        t['text'] = text
        t['assert'] = assert_
        if appendtext:
            t['appendtext'] = appendtext
        if prependtext:
            t['prependtext'] = prependtext
        if summary:
            t['summary'] = summary
        if section:
            t['section'] = section
        if minor:
            t['minor'] = ''
        if notminor:
            t['notminor'] = ''
        if bot:
            t['bot'] = ''
        if createonly:
            t['createonly'] = ''
        if nocreate:
            t['nocreate'] = ''
        if md5:
            t['md5'] = md5
        t['token'] = self.edittoken
        print(t)
        d = self.request(t, headers={'Content-Type':'multipart/form-data'}, post=True)
        return(d)
