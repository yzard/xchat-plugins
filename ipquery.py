#!/bin/env python
# -*- coding: UTF-8 -*-
# Desc: Find the IP address
# Author: AutumnCat
# Merger: YZard
__module_name__ = "IPQuery"
__module_version__ = "0.3"
__module_description__ = "Replace the join and quit message with place name."
import xchat
import re
 
FilePath = '/home/yzard/.xchat2/QQWry.Dat'
 
# ====================================================================
# Powered by AutumnCat
# ====================================================================
from struct import unpack, pack
import sys, _socket, mmap
 
def _ip2ulong(ip):
    '''点分十进制 -> unsigned long
    '''
    return unpack('>L', _socket.inet_aton(ip))[0]
 
def _ulong2ip(ip):
    '''unsigned long -> 点分十进制
    '''
    return _socket.inet_ntoa(pack('>L', ip))
 
class QQWryBase:
    '''QQWryBase 类, 提供基本查找功能.
 
    注意返回的国家和地区信息都是未解码的字符串, 对于简体版数据库应为GB编码, 对于繁体版则应为BIG5编码.
    '''
    class ipInfo(tuple):
        '''方便输出 ip 信息的类.
 
        ipInfo((sip, eip, country, area)) -> ipInfo object
        '''
        def __str__(self):
            '''str(x)
            '''
            return str(self[0]).ljust(16) + ' - ' + str(self[1]).rjust(16) + '    ' + self[2] + self[3]
 
        def normalize(self):
            '''转化ip地址成点分十进制.
            '''
            return QQWryBase.ipInfo((_ulong2ip(self[0]), _ulong2ip(self[1]), self[2], self[3]))
 
    def __init__(self, dbfile):
        '''QQWryBase(dbfile) -> QQWryBase object
 
        dbfile 是数据库文件的 file 对象.
        '''
        self.f = dbfile
        self.f.seek(0)
        self.indexBaseOffset = unpack('<L', self.f.read(4))[0] #索引区基址
        self.Count = (unpack('<L', self.f.read(4))[0] - self.indexBaseOffset) / 7 # 索引数-1
 
    def Lookup(self, ip):
        '''x.Lookup(ip) -> (sip, eip, country, area) 查找 ip 所对应的位置.
 
        ip, sip, eip 是点分十进制记录的 ip 字符串.
        sip, eip 分别是 ip 所在 ip 段的起始 ip 与结束 ip.
        '''
        return self.nLookup(_ip2ulong(ip))
 
    def nLookup(self, ip):
        '''x.nLookup(ip) -> (sip, eip, country, area) 查找 ip 所对应的位置.
 
        ip 是 unsigned long 型 ip 地址.
        其它同 x.Lookup(ip).
        '''
        si = 0
        ei = self.Count
        if ip < self._readIndex(si)[0]:
            raise StandardError('IP NOT Found.')
        elif ip >= self._readIndex(ei)[0]:
            si = ei
        else: # keep si <= ip < ei
            while (si + 1) < ei:
                mi = (si + ei) // 2
                if self._readIndex(mi)[0] <= ip:
                    si = mi
                else:
                    ei = mi
        ipinfo = self[si]
        if ip > ipinfo[1]:
            raise StandardError('IP NOT Found.')
        else:
            return ipinfo
 
    def __str__(self):
        '''str(x)
        '''
        tmp = []
        tmp.append('RecCount:')
        tmp.append(str(len(self)))
        tmp.append('\nVersion:')
        tmp.extend(self[self.Count].normalize()[2:])
        return ''.join(tmp)
 
    def __len__(self):
        '''len(x)
        '''
        return self.Count + 1
 
    def __getitem__(self, key):
        '''x[key]
 
        若 key 为整数, 则返回第key条记录(从0算起, 注意与 x.nLookup(ip) 不一样).
        若 key 为点分十进制的 ip 描述串, 同 x.Lookup(key).
        '''
        if type(key) == type(0):
            if (key >=0) and (key <= self.Count):
                index = self._readIndex(key)
                sip = index[0]
                self.f.seek(index[1])
                eip = unpack('<L', self.f.read(4))[0]
                (country,area) = self._readRec()
                return QQWryBase.ipInfo((sip, eip, country, area))
            else:
                raise KeyError('INDEX OUT OF RANGE.')
        elif type(key) == type(''):
            try:
                return self.Lookup(key).normalize()
            except StandardError, e:
                if e.message == 'IP NOT Found.':
                    raise KeyError('IP NOT Found.')
                else:
                    raise e
        else:
            raise TypeError('WRONG KEY TYPE.')
 
    def __iter__(self):
        '''返回迭代器(生成器).
        '''
        for i in range(0, len(self)):
            yield self[i]
 
    def _read3ByteOffset(self):
        '''_read3ByteOffset() -> unsigned long 从文件 f 读入长度为3字节的偏移.
        '''
        return unpack('<L', self.f.read(3) + '\x00')[0]
 
    def _readCStr(self):
        '''x._readCStr() -> string 读 '\0' 结尾的字符串.
        '''
        if self.f.tell() == 0:
            return 'Unknown'
        tmp = []
        ch = self.f.read(1)
        while ch != '\x00':
            tmp.append(ch)
            ch = self.f.read(1)
        return ''.join(tmp)
 
    def _readIndex(self, n):
        '''x._readIndex(n) -> (ip ,offset) 读取第n条索引.
        '''
        self.f.seek(self.indexBaseOffset + 7 * n)
        return unpack('<LL', self.f.read(7) + '\x00')
 
    def _readRec(self, onlyOne=False):
        '''x._readRec() -> (country, area) 读取记录的信息.
        '''
        mode = unpack('B', self.f.read(1))[0]
        if mode == 0x01:
            rp = self._read3ByteOffset()
            bp = self.f.tell()
            self.f.seek(rp)
            result = self._readRec(onlyOne)
            self.f.seek(bp)
            return result
        elif mode == 0x02:
            rp = self._read3ByteOffset()
            bp = self.f.tell()
            self.f.seek(rp)
            result = self._readRec(True)
            self.f.seek(bp)
            if not onlyOne:
                result.append(self._readRec(True)[0])
            return result
        else: # string
            self.f.seek(-1,1)
            result = [self._readCStr()]
            if not onlyOne:
                result.append(self._readRec(True)[0])
            return result
    pass # End of class QQWryBase
 
class QQWry(QQWryBase):
    '''QQWry 类.
    '''
    def __init__(self, filename='QQWry.Dat'):
        '''QQWry(filename) -> QQWry object
        filename 是数据库文件名.
        '''
        f = open(filename, 'rb')
        QQWryBase.__init__(self, f)
 
class MQQWry(QQWryBase):
    '''MQQWry 类.
    将数据库放到内存的 QQWry 类.
    查询速度大约快两倍.
    '''
    def __init__(self, filename='QQWry.Dat', dbfile=None):
        '''MQQWry(filename[,dbfile]) -> MQQWry object
 
        filename 是数据库文件名.
        也可以直接提供 dbfile 文件对象. 此时 filename 被忽略.
        '''
        if dbfile == None:
            dbf = open(filename, 'rb')
        else:
            dbf = dbfile
        bp = dbf.tell()
        dbf.seek(0)
        QQWryBase.__init__(self, mmap.mmap(dbf.fileno(), 0, access = 1))
        dbf.seek(bp)
 
    def _readCStr(self):
        '''x._readCStr() -> string 读 '\0' 结尾的字符串.
        '''
        pstart = self.f.tell()
        if pstart == 0:
            return 'Unknown'
        else:
            pend = self.f.find('\x00', pstart)
            if pend < 0:
                raise StandardError('Fail To Read CStr.')
            else:
                self.f.seek(pend + 1)
                return self.f[pstart:pend]
 
    def _readIndex(self, n):
        '''x._readIndex(n) -> (ip ,offset) 读取第n条索引.
        '''
        startp = self.indexBaseOffset + 7 * n
        return unpack('<LL', self.f[startp:startp + 7] + '\x00')
 
# =====================================================================
def GetAddress(IP):
	regex = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
	if not re.search(regex,IP): return 'Wrong IP address!'
	if not IP: return 'Wrong IP address!'
	try:
		Q = MQQWry(FilePath)
		ad = Q[IP][2]+' '+Q[IP][3]
	except StandardError, e:
		if e.message != '':
			print e.message
		else:
			raise e
	finally:
		pass
		return ad.decode('GB18030').encode('UTF-8')
 
def GetHost(name):
	import socket
	regex = '.*@(.*)'
	name = re.sub(regex,'\\1',name)
	regipc = '[^0-9]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.).*'
	regipd = '[^0-9]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*'
 
	regencrpt = '[0-9A-F]+\.[0-9A-F]+\.[0-9A-F]+\.'
	ip = 'Wrong Address!'
	if re.search(regipd,name): ip = re.sub(regipd,'\\1',name)
	if re.search(regipc,name): ip = re.sub(regipc,'\\1',name)+'0'
	elif re.search(regencrpt,name): pass
	else:
		try:
			ip = socket.gethostbyname(name)
		except socket.gaierror:
			ip = 'Name or Server not known'
	return ip
 
IpRegex = '.*@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*'
 
def ReplacePart(word, word_eol, userdata):
	ip = GetHost(word[1])
	print '\00323'+'*','\002'+word[0]+'\002','('+word[1]+')','['+GetAddress(ip)+']'+' has left', word[2],'\003'
	return xchat.EAT_XCHAT
 
def ReplacePartWithReason(word, word_eol, userdata):
	ip = GetHost(word[1])
	print '\00323'+'*','\002'+word[0]+'\002','('+word[1]+')','['+GetAddress(ip)+']'+' has left', word[2],'('+word[3]+')','\003'
	return xchat.EAT_XCHAT
 
def ReplaceQuit(word, word_eol, userdata):
	if not word[1]: 
		print word[0]
		return
	ip = GetHost(word[2])
	print '\00323'+'*','\002'+word[0]+'\002','('+word[2]+')','['+GetAddress(ip)+']'+' has quit','(Quit: '+word[1]+')','\003'
	return xchat.EAT_XCHAT
 
def ReplaceJoin(word, word_eol, userdata):
	ip = GetHost(word[2])
	print '\00319'+'*','\002'+word[0]+'\002','('+word[2]+')','['+GetAddress(ip)+']'+' has joined', word[1],'\003'
	return xchat.EAT_XCHAT
 
def GetAdd(word, word_eol, userdata):
	nicks = [i.nick for i in xchat.get_list("users")]	
	regex = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
	Host = ''
	if re.search(regex,word[1]): print word[1],':',GetAddress(GetHost(word[1]))
	elif word[1] in nicks:
		for i in xchat.get_list('users'):
			if i.nick == word[1]:
				Host = i.host
				break
		ip = GetHost(Host)
		print '\00320'+word[1],'('+Host+')',':',GetAddress(ip)+'\003'
	else:
		print 'This nick is not exist!'
	return xchat.EAT_ALL
 
xchat.hook_print("Part",ReplacePart)
xchat.hook_print("Part with Reason",ReplacePartWithReason)
xchat.hook_print("Quit",ReplaceQuit)
xchat.hook_print("Join",ReplaceJoin)
xchat.hook_command("IP",GetAdd)
