#coding:utf8


from mongoengine import * 


connect(db='solve',host='127.0.0.1',port=27017,username='solve',password='solve123456')


class Job(Document):  
    job_id=StringField(required=True,primary_key=True)
    comment=StringField() 
    tmpl=StringField() 
    target=StringField() 
    job_type=StringField() 
    number=StringField()
    target_type=StringField()
    session=StringField()
    playbook=StringField()
    begin_time=StringField()
    user=StringField()


class JobLog(Document):
    job_id=StringField(required=True,primary_key=True)
    playbook=StringField()
    log=StringField()
    begin_timestamp=StringField()
    playbook_md5=StringField()
    playbook_rownum=StringField() 


class TargetLog(Document):
    target_id=StringField(required=True,primary_key=True)
    log_list=ListField()


class HostLog(Document):
    host=StringField(required=True,primary_key=True)
    log_list=ListField()


#记录的字段存在不同
class Log(Document):
    uuid=StringField(required=True,primary_key=True)
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



