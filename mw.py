#!/usr/bin/env python3
"""
License: The MIT License (http://opensource.org/licenses/MIT)
"""

import requests

class SSMWError(Exception):
    pass

class Wiki:
    def __init__(self, api_url, headers=None):
        self.api_url = api_url
        self.cookies = None
        self.username = None
        self.format = 'json'
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
        r1 = requests.post(self.api_url, params=data, headers=self.headers)
        if not r1.ok:
            raise SSMWError(r1.text)
        if not r1.json():
            raise SSMWError(r1.text)
        token = r1.json()['login']['token']
        data['lgtoken'] = token
        self.cookies = r1.cookies
        r1 = requests.post(self.api_url, params=data, headers=self.headers, cookies=self.cookies)
        if not r1.ok:
            raise SSMWError(r1.text)
        self.cookies = r1.cookies

    def request(self, params, post=False):
        """
        Makes an API request with the given params.
        Returns the page in a dict format
        """
        r = self.fetch(params=params, post=post)
        try:
            return r.json()
        except:
            raise SSMWError(r.text)

    def fetch(self, url=None, params=None, post=False):
        if not url:
            url = self.api_url
        if 'format' not in params:
            params['format'] = self.format
        if post:
            r = requests.post(url, params=params, cookies=self.cookies, headers=self.headers)
        else:
            r = requests.get(url, params=params, cookies=self.cookies, headers=self.headers)
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
        for k in r['query']['pages']:
            if r['query']['pages'][k].get('edittoken', None):
                self.edittoken = r['query']['pages'][k]['edittoken']

    def logout(self):
        params = {}
        params['action'] = 'logout'
        r = self.request(params=params)
        return r
