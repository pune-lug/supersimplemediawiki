#!/usr/bin/env python3
"""
License: The MIT License (http://opensource.org/licenses/MIT)
"""

import requests
import random

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
            raise SSMWError(r1.url+'\n'+r1.text)
        if not r1.json():
            raise SSMWError(r1.url+'\n'+r1.text)
        token = r1.json()['login']['token']
        data['lgtoken'] = token
        self.cookies = r1.cookies
        r1 = self.s.post(self.api_url, params=data, headers=self.headers, cookies=self.cookies)
        if not r1.ok:
            raise SSMWError(r1.url+'\n'+r1.text)
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
            raise SSMWError(r.url+'\n'+r.text)

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
            raise SSMWError(url+'\n'+r.text)
        return r

    def get_edittoken(self, page=None):
        params = {}
        params['action'] = 'query'
        params['prop'] = 'info'
        params['intoken'] = 'edit'
        if page:
            params['titles'] = page
        else:
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
        params = {}
        params['format'] = self.format
        params['action'] = 'edit'
        params['title'] = self.title
        params['text'] = text
        params['assert'] = assert_
        if appendtext:
            params['appendtext'] = appendtext
        if prependtext:
            params['prependtext'] = prependtext
        if summary:
            params['summary'] = summary
        if section:
            params['section'] = section
        if minor:
            params['minor'] = ''
        if notminor:
            params['notminor'] = ''
        if bot:
            params['bot'] = ''
        if createonly:
            params['createonly'] = ''
        if nocreate:
            params['nocreate'] = ''
        if md5:
            params['md5'] = md5
        params['token'] = self.edittoken
        d = self.request(params, headers={'Content-Type':'multipart/form-data'}, post=True)
        return(d)

    def get_recentchanges(self, **kargs):
        params = {}
        params['format'] = self.format
        params['action'] = 'query'
        params['list'] = 'recentchanges'
        params['rcprop'] = '|'.join(kargs.get('rcprop', ['title', 'ids', 'type', 'user']))
        params['rclimit'] = vars(self).get('rclimit', 5000)
        rctype = kargs.get('rctype', None)

        rcstart = kargs.get('rcstart', None)
        if rctype:
            params['rctype'] = rctype
        rcstart = kargs.get('rcstart', None)
        rcstop = kargs.get('rcstop', None)
        rccontinue = kargs.get('rccontinue', None)
        if not rccontinue:
            self.rcstart= None
            self.rcfinished = False
        if rccontinue and self.rcstart:
            params['rcstart'] = self.rcstart
        rccontinue = kargs.get('rccontinue', None)
        if rccontinue:
            params['rccontinue'] = rccontinue
        if rcstart:
            params['rcstart'] = rcstart
        if rcstop:
            params['rcstop'] = rcstop
        d = self.request(params)
        try:
            try:
                self.rcstart = d['query-continue']['recentchanges']['rcstart']
            except:
                self.rcfinished = True
            retval = []
            for x in d['query']['recentchanges']:
                tmp_retval = {}
                for y in params['rcprop'].split('|'):
                    if y == 'ids':
                        for z in ['rcid', 'pageid', 'revid', 'old_revid']:
                            tmp_retval[z] = x[z]
                    else:
                        tmp_retval[y] = x[y]
                retval.append(tmp_retval)
            return retval
        except Exception as e:
            raise(Exception('Data not found', e))

    def get_random_pages(self, rnnamespace=None, rnlimit=20):
        params = {}
        params['action'] = 'query'
        params['list'] = 'random'
        if rnnamespace:
            params['rnnamespace'] = '|'.join([str(x) for x in rnnamespace])
        params['rnlimit'] = rnlimit
        d = self.request(params)
        return [x['title'] for x in d['query']['random']]
