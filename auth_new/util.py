#coding:utf8
import re

def safe_decode(string):
    '''
    由其他编码转换成unicode
    '''
    try:
        #字符以utf8存储 转换成unicode
        return string.decode('utf8')
    except:
        #python3是字符都是以unicode存储 不能再转换
        return string

################################CAS相关函数#########################################################################

def cas_info_parser(cas_info,attrib):
    """
    解析从cas获取的信息
    """
    flag, user, msg = '','',cas_info
    from xml.etree import ElementTree as ET
    try:
        root=ET.XML(cas_info)
        # xml时的解析
        # <tag attrib>text<child/>...</tag>tail
        try:
            auth_info={}
            m = re.match('\{.*\}', root.tag)
            xmlns=m.group(0) if m else ''
            for a in root:
                #if a.tag.split(xmlns)[-1] == 'authenticationSuccess':
                if a.tag.split(xmlns)[-1] == attrib:
                    for u in a:
                        auth_info[u.tag.split(xmlns)[-1]] = u.text if u.text else ''
                else:
                    msg = "%s %s" % (a.text, str(a.attrib))
                    return flag, user, msg
            if 'user' in auth_info:
                user=auth_info['user']
                flag=True
            else:
                user=''
                flag=False
            msg=auth_info
        except:
            pass
    
    except:
        # text时的解析
        try:
            flag, user, x=cas_info.split('\n')
            flag=(flag.lower()=='yes')
        except:
            pass

    return flag, user, msg
