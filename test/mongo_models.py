# -*- coding: utf-8 -*- 
from mongoengine import * 


connect(db='solve',host='127.0.0.1',port=27017,username='solve',password='solve123456')




class Job(Document):  
    pid=StringField(required=True,primary_key=True)   #job_id
    job_id=StringField(required=False)
    comment=StringField(required=False) 
    tmpl=StringField(required=False) 
    target=StringField(required=False) 
    job_type=StringField(required=False) 
    number=StringField(required=False)
    target_type=StringField(required=False)
    session=StringField(required=False)
    playbook=StringField(required=False)
    begin_time=StringField(required=False)
    user=StringField(required=False)
    begin_line=StringField(required=False)


class JobLog(Document):
    pid=StringField(required=True,primary_key=True)  
    playbook=StringField(required=False)
    log=StringField(required=False)
    begin_timestamp=StringField(required=False)
    playbook_md5=StringField(required=False)
    playbook_rownum=StringField(required=False) 


class TargetLog(Document):
    pid=StringField(required=True,primary_key=True)
    key_list=ListField(required=False)


class HostLog(Document):
    pid=StringField(required=True,primary_key=True)  #host
    key_list=ListField(required=False)


#记录的字段存在不同
class Log(Document):
    pid=StringField(required=True,primary_key=True)
    start_timestamp=StringField(required=False)
    origin_cmd=StringField(required=True)
    render_cmd=StringField(required=False)
    begin_timestamp=StringField(required=False)
    from_host=StringField(required=False)
    cmd=StringField(required=False)
    exe_host=StringField(required=False)
    cmd_type=StringField(required=False)
    end_timestamp=StringField(required=False)
    exit_code=StringField(required=False)
    stderr=StringField(required=False)
    stdout=StringField(required=False)
    stop_timestamp=StringField(required=False)


class Sum(Document):
    pid=StringField(required=True,primary_key=True)    #target_id
    end_timestamp=StringField() 
    last_stdout=StringField() 
    stop_str=StringField() 
    last_uuid=StringField() 
    target=StringField() 
    begin_timestamp=StringField() 



class Vars(DynamicDocument):
    pid=StringField(required=True)
    #var_type=StringField(required=True)     #session global
    #value=DictField()


if __name__ == "__main__":
    for x in Vars.objects:
        print(x.__pid)