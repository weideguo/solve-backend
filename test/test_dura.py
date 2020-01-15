#coding:utf8
from libs import redis_pool
from core.dura import solve_dura

redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()


if __name__ == '__main__':
    #set string_test bbbb
    solve_dura.dura.real_save('string_test',redis_manage_client,'yyy') 
    solve_dura.dura.real_save('string_test',redis_manage_client,'yyy',0) 
    #hmset hash_test a aaa b bbb
    solve_dura.dura.real_save('hash_test',redis_manage_client,'yyy') 
    #saddd set_test a b c d
    solve_dura.dura.real_save('set_test',redis_manage_client,'yyy') 
    #zadd zset_test a 10 b 20 c 100
    solve_dura.dura.real_save('zset_test',redis_manage_client,'yyy') 
    #rpush list_test a b c e f
    solve_dura.dura.real_save('lis_test',redis_manage_client,'yyy')
    solve_dura.dura.real_save('lis_test',redis_manage_client,'yyy',-1)


    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'string_test'})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'string_test',0})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'hash_test'})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'set_test'})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'zset_test'})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'lis_test'})
    solve_dura.dura.real_load(redis_manage_client,'yyy',{'__pid':'lis_test'})

    solve_dura.dura.get_collection_name('log_job_5da525ec374011ea8abd000c295dd589',redis_log_client)

    solve_dura.dura.save()

    solve_dura.dura.load()

    solve_dura.dura.reload('log_job_5da525ec374011ea8abd000c295dd589', redis_log_client)

    ########################################################################################
    solve_dura.get_keys('log_job_5da525ec374011ea8abd000c295dd589')
    solve_dura.is_job_finish(['log_target_b14c00b2374011eabd2c000c295dd589', 'log_target_b1526c0e374011eabd2c000c295dd589'], \
        ['sum_b14c00b2374011eabd2c000c295dd589', 'sum_b1526c0e374011eabd2c000c295dd589'])

    solve_dura.expire('log_job_5da525ec374011ea8abd000c295dd589')
    
    solve_dura.get_key_info_from_mongo(redis_log_client, key='log_job_5da525ec374011ea8abd000c295dd589')
    solve_dura.get_key_info_from_mongo(redis_tmp_client, pattern='session.*_5da525ec374011ea8abd000c295dd589')

    solve_dura.get_keys_from_mongo('log_job_5da525ec374011ea8abd000c295dd589')

    solve_dura.reload('log_job_5da525ec374011ea8abd000c295dd589')
    solve_dura.reload('log_job_5da525ec374011ea8abd000c295dd589',0)

