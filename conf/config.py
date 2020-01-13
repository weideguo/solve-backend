#coding:utf8

exe_stats_time_gap=30               #首页的统计时常 天

prefix_log="log_"                   #日志的开头
                                    #重新运行/继续运行需要在上一次提交时间的以下两个时间内执行 分别对session/global参数限制
#redis manage
key_solve_config="solve_config"     #存储配置信息的key    
prefix_config="config_"             #单项配置key的开头
target_types="target_types"
job_types="job_types"
job_rerun="rerun"                   #用于标记重新运行的任务类型

prefix_exec="exec"                  #可执行任务key的开头
prefix_exec_tmpl="tmpl"             #任务模板key的开头


###############################以下的参数需要与solve的配置相同############################################################################
tmp_config_expire_sec=24*60*60     #复制的session过期的时间 每个job复制一次session
#session_var_expire_sec=24*60*60     #复制的session过期的时间 每个job复制一次session
#global_var_expire_sec=24*60*60      #global_ 全局变量的保存时间  
host_check_success_time=15          #心跳时间超时间隔 超过15s即判断连接断开
cmd_spliter="@@@@@"                 #所有关键命令与uuid的分隔符

#redis send
key_conn_control="conn_control"     #控制主机连接与断开的队列key  建立连接 <ip> 
key_job_list="job_list"             #执行任务的队列
prefix_kill="kill_"                 #key_<cluster id>  终止执行对象的key
pre_close="close_"                  #插入key_conn_control中       关闭连接 close_<ip>  
prefix_heart_beat="heart_beat_"     #heart_beat_<host ip>  主机心跳的key

#redis config
prefix_realhost="realhost_"         #用于创建连接的主机的key开头
prefix_global="global_"             #全局变量对应的key开头
prefix_session="session_"           #输入变量对应的key开头
playbook_prefix_global="global"     #playbook中全局变量的开头 全局变量如 global.yyy
playbook_prefix_session="session"   #playbook中输入变量的开头 输入变量如 session.xxx

#redis job
prefix_job="job_"                   #每个任务的信息 job_<job id> 插入 key_job_list 

#redis log
prefix_log_target="log_target_"   #每个执行对象执行命令的队列key
prefix_sum="sum_"                   #每次每个执行对象所执行的汇总


