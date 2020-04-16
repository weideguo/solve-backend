#coding:utf8

from libs import redis_pool

if __name__ == "__main__":
    redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client=redis_pool.redis_init()

    redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = \
        redis_pool.refresh(redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client)



