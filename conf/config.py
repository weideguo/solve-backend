# -*- coding: utf-8 -*- 

exe_stats_time_gap=30               #首页的统计时常 天

prefix_log="log_"                   #日志的开头

prefix_temp="temp_"                 #临时对象 临时playbook的前缀

#redis manage
key_solve_config="solve_config"     #存储配置信息的key    
prefix_config="config_"             #单项配置key的开头
target_types="target_types"
job_types="job_types"
job_rerun="rerun"                   #用于标记重新运行的任务类型

prefix_exec="exec"                  #可执行任务key的开头
prefix_exec_tmpl="tmpl"             #任务模板key的开头


###############################以下的参数需要与solve的配置相同############################################################################
tmp_config_expire_sec=24*60*60     #复制的对象 global session过期的时间 每个job复制一次
host_check_success_time=15          #心跳时间超时间隔 超过15s即判断连接断开
spliter="@@@@@"                     #与uuid的分隔符

#redis send
key_conn_control="conn_control"     #控制主机连接与断开的队列key  建立连接 <ip> 
key_job_list="job_list"             #执行任务的队列
prefix_kill="kill_"                 #key_<cluster id>  终止执行对象的key
pre_close="close_"                  #插入key_conn_control中       关闭连接 close_<ip>  
prefix_heart_beat="heart_beat_"     #heart_beat_<host ip>  主机心跳的key
prefix_block="block_"               #block_<cluster id> 标记制定对象逐行阻塞执行 list类型，插入0正常运行被阻塞的命令然后阻塞，-1则结束阻塞之后的命令按顺序执行，其他则终止当前被阻塞的以及之后的


#redis config
prefix_realhost="realhost_"         #用于创建连接的主机的key开头

#redis_tmp
prefix_global="global"             #全局变量对应的key开头 playbook中全局变量的开头 全局变量如 global.yyy
prefix_session="session"           #输入变量对应的key开头 playbook中输入变量的开头 输入变量如 session.xxx
prefix_select="select"              #输入变量对应的key开头 playbook中全局变量的开头 全局变量如 select.yyy

#redis job
prefix_job="job_"                   #每个任务的信息 job_<job id> 插入 key_job_list 

#redis log
prefix_log_target="log_target_"   #每个执行对象执行命令的队列key
prefix_sum="sum_"                   #每次每个执行对象所执行的汇总


