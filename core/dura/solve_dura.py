#coding:utf8
import time
import redis
from threading import Thread

from libs import redis_pool
from conf import config

from .dura import dura



class SolveDura():
	'''
	根据实际情况对对应的key进行过期设置
	以及从mongodb同步到redis
	'''
	redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()

	def __init__(self, time_gap=60):

		self.time_gap=time_gap
		self.__backgroup()
		


	def get_keys(self, key):
		'''
		由log_job_XXXXXX 在redis中获取关联的key 只能用于过期设置
		'''
		job_id=key.split('_')[-1]
		#session
		#session_list=self.redis_config_client.keys('session_'+'*'+job_id)
		session_list=self.redis_config_client.keys(config.prefix_session+'*'+job_id)

		target_log_list=[]
		global_list=[]
		log_list=[]
		sum_list=[]

		log_job_info=self.redis_log_client.hgetall(key)
		if 'log' in log_job_info:
			for tl in eval(log_job_info.get('log','[]')):
				target_log=tl[1]
				target_id=target_log.split('_')[-1]
				target_log_list.append(target_log)
				global_list += self.redis_config_client.keys(config.prefix_global+target_id)
				sum_list    += self.redis_log_client.keys(config.prefix_sum+target_id)
				log_list    += self.redis_log_client.lrange(target_log, 0, self.redis_log_client.llen(target_log))

		return target_log_list, sum_list, log_list, session_list, global_list


	def is_job_finish(self,target_log_list, sum_list):
		'''
		由log_job_XXXXXX 获取关联的log_target_YYY以及sum_YYY判定任务是否执行结束
		'''
		if len(target_log_list) == len(sum_list):
			for l in sum_list:
				if not ('stop_str' in self.redis_log_client.hgetall(l)):
					#print(l)
					return False

			#所有的sum_YYY都存在'stop_str'属性时则表明任务执行完毕
			return True
		else:
			#print(len(target_log_list),len(sum_list))
			return False


	def x__expire(self):
		pass


	def __expire(self):
		'''
		监听执行日志log_job_XXXXXX，判定执行结束将对应关联key设置过期
		'''
		log_prefix=config.prefix_log+config.prefix_job
		while True:
			for k in self.redis_log_client.keys(log_prefix+'*'):
				
				if self.redis_log_client.ttl(k) <= 0:
					self.expire(k)
					#print('expire %s'  % k)
			time.sleep(self.time_gap)
	

	def expire(self, key, force=0):
		'''
		单个log_job_XXX的过期设置
		force 是否不管已经完成与否，默认需要完成才设置过期
		设置过期前要检查ttl，否则过期时间会重置，导致没有弹出redis
		'''
		target_log_list, sum_list, log_list, session_list, global_list = self.get_keys(key)

		client_key = [(self.redis_log_client, [key]+target_log_list+log_list+sum_list),\
					  (self.redis_config_client, session_list+global_list)]

		if self.is_job_finish(target_log_list, sum_list) or force:
			for ck in client_key:
				redis_client=ck[0]
				for ik in ck[1]:
					#过期的时间跟session的过期时间一致
					redis_client.expire(ik, config.session_var_expire_sec)
					#print(str(redis_client), ik, str(config.session_var_expire_sec))
			return client_key
		else:
			return None
	

	def get_key_info_from_mongo(self, key, redis_client):
		'''
		从mongodb获取key的信息
		'''
		connection_name=dura.get_collection_name(key, redis_client)
		key_info = dura.db[connection_name].find({dura.primary_key: key})
		try:
			key_info=key_info[0]
		except:
			key_info={}
		return key_info


	def get_keys_from_mongo(self, key):
		'''
		由log_job_XXXXXX 在mongodb中获取关联的key 用于从mongodb加载到redis
		'''
		target_log_list = []
		sum_list = []
		log_list = []
		session_list = []
		global_list = []

		job_id=key.split('_')[-1]

		#session_list_info=self.get_key_info_from_mongo(config.prefix_session+'.*_'+job_id, self.redis_config_client)
		session_pattern=config.prefix_session+'.*_'+job_id
		session_list_connection_name=dura.get_collection_name(session_pattern, self.redis_config_client)
		session_list_info=dura.db[session_list_connection_name].find({dura.primary_key: {'$regex': session_pattern}})
		try:
			session_list_info=session_list_info[0]
		except:
			session_list_info={}

		if dura.primary_key in session_list_info:
			session_list.append(session_list_info[dura.primary_key])

		log_job_info=self.get_key_info_from_mongo(key, self.redis_log_client)

		if 'log' in log_job_info:
			for tl in eval(log_job_info.get('log','[]')):
				target_log=tl[1]
				target_id=target_log.split('_')[-1]
				target_log_list.append(target_log)
				
				global_list.append(config.prefix_global+target_id)
				
				sum_list.append(config.prefix_sum+target_id,)

				log_list_info = self.get_key_info_from_mongo(target_log, self.redis_log_client)
				if dura.list_name in log_list_info and isinstance(log_list_info[dura.list_name],list):
					log_list += log_list_info[dura.list_name]

		return target_log_list, sum_list, log_list, session_list, global_list


	def reload(self, key, is_update=1):
		'''
		由log_job_XXXXXX 从mongodb加载相关key到redis
		
		'''
		summary=[]
		key_exist=self.redis_log_client.exists(key)
		if (not key_exist) or is_update:
			#redis中不存在，或者强制为更新，则都mongodb加载
			#dura.load(key, self.redis_log_client)
			target_log_list, sum_list, log_list, session_list, global_list = self.get_keys_from_mongo(key)
	
			client_key = [(self.redis_log_client, [key]+target_log_list+log_list+sum_list),\
						  (self.redis_config_client, session_list+global_list)]
			
			for ck in client_key:
				redis_client=ck[0]
				for ik in ck[1]:
					x=dura.load(ik, redis_client)
					summary.append(x)

			return key,summary
		else:
			return None,None


	def __backgroup(self):
		t1=Thread(target=self.__expire,args=())  
		t1.start()



def getSolveDura():
	if dura:
		return SolveDura
	else:
		return None

#单例模式
#solve_dura=getSolveDura()
solve_dura=SolveDura()

