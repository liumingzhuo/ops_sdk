#!/usr/bin/env python
# -*-coding:utf-8-*-
'''
role   : 集中化管理工具的使用
'''

import requests
import json
import time

try:
    import cookielib
except:
    import http.cookiejar as cookielib

import ssl

context = ssl._create_unverified_context()
import urllib3

urllib3.disable_warnings()


class SaltApi:
    """
    定义salt api接口的类
    初始化获得token
    """

    def __init__(self, url='https://127.0.0.1:8001/', username="saltapi", password="123456"):
        self.__url = url
        self.__username = username
        self.__password = password
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
            "Content-type": "application/json"
            # "Content-type": "application/x-yaml"
        }
        self.params = {'client': 'local', 'fun': '', 'tgt': ''}
        self.login_url = self.__url + "login"
        self.login_params = {'username': self.__username, 'password': self.__password, 'eauth': 'pam'}
        self.token = self.post_data(self.login_url, self.login_params)['token']
        self.headers['X-Auth-Token'] = self.token

    def get_data(self, url):
        request = requests.get(url, headers=self.headers, verify=False)
        response = request.json()
        result = dict(response)
        return result['return'][0]

    def post_data(self, url, params):
        send_data = json.dumps(params)
        request = requests.post(url, data=send_data, headers=self.headers, verify=False)
        response = request.json()
        result = dict(response)
        return result['return'][0]

    def salt_command(self, tgt, method, arg=None):
        """远程执行命令，相当于salt 'client1' cmd.run 'free -m'"""
        if arg:
            params = {'client': 'local', 'fun': method, 'tgt': tgt, 'arg': arg}
        else:
            params = {'client': 'local', 'fun': method, 'tgt': tgt}
        result = self.post_data(self.__url, params)
        return result

    def salt_async_command(self, tgt, method, arg=None):  # 异步执行salt命令，根据jid查看执行结果

        """远程异步执行命令"""
        if arg:
            params = {'client': 'local_async', 'fun': method, 'tgt': tgt, 'arg': arg}
        else:
            params = {'client': 'local_async', 'fun': method, 'tgt': tgt}
        jid = self.post_data(self.__url, params).get('jid', None)
        return jid

    def look_jid(self, jid):  # 根据异步执行命令返回的jid查看事件结果
        params = {'client': 'runner', 'fun': 'jobs.lookup_jid', 'jid': jid}
        result = self.post_data(self.__url, params)
        return result

    def run(self, salt_client='*', salt_method='cmd.run_all', salt_params='w', timeout=1800):
        try:
            if not self.salt_command(salt_client, 'test.ping')[salt_client]:
                return -98, 'test.ping error 98', '', salt_client
        except Exception as e:
            return -99, 'test.ping error 99', str(e), salt_client

        t = 0
        jid = self.salt_async_command(salt_client, salt_method, salt_params)
        if not jid:
            return -100, '连接失败', '连接失败或主机不存在', salt_client

        while True:
            time.sleep(5)
            if t == timeout:
                print('exec timeout!')
                break
            else:
                t += 5
            result = self.look_jid(jid)
            for i in result.keys():
                return result[i]['retcode'], result[i]['stdout'], result[i]['stderr'], i

    def salt_alive(self, tgt):
        '''
        salt主机存活检测
        '''
        params = [{'client': 'local', 'tgt': tgt, 'fun': 'test.ping'}]
        ret = self.post_data(self.__url, params)
        return ret

    def detail_monions(self, monions_id):
        '''
        获取monion信息
        :return:
        '''
        ret = self.get_data(self.__url + 'minions/' + monions_id)
        return ret


if __name__ == '__main__':
    pass
    # salt1 = SaltApi()
    # req = salt1.run('*', 'cmd.run_all', 'w')
    # status, stdout, stderr = req[0], req[1], req[2]
    # print(status, stdout, stderr)
