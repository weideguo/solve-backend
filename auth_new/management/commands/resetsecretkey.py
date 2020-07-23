# -*- coding: utf-8 -*- 
import os
import re
import sys

from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

class Command(BaseCommand):
    help = "reset `SECRET_KEY` at settings.py"
    
    
    def add_arguments(self, parser):
        parser.add_argument("--key", type=str, required=False, help='set secret key manually, length must be 50 (optional)')
        

    def handle(self, *args, **options):
        key = options['key']
        if (not key) or len(key) != 50 :
            print("will generate `SECRET_KEY`")
            key=get_random_secret_key()
            
        settings_model_name=os.environ.get("DJANGO_SETTINGS_MODULE")
        settings_file=settings_model_name.replace(".","/")+".py"
        #print(settings_file)
        #print(key,len(key))
        with open(settings_file) as f:
            l=f.readline()
            new_c=""   
            while l:
                if re.match("^#.*",l.strip()):
                    new_c=new_c+l
                elif re.match("^SECRET_KEY.*",l.strip()):
                    new_l="SECRET_KEY = '%s'\n" % key
                    if sys.version_info<(3,0):
                        #for python2, unicode -> byte
                        new_l=new_l.encode("utf8")
                    new_c=new_c+new_l
                else:
                    new_c=new_c+l
                
                l=f.readline()
        
        with open(settings_file,"w") as f:
            f.write(new_c)
        
        print("reset `SECRET_KEY = '%s'` \033[1;32m done \033[0m" % key)

