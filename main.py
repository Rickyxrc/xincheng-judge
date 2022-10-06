import requests
import json
import os
import shutil
import time,datetime
import subprocess
import sys
import yaml

with open('conf.yaml','r') as conf:
    # __config = json.loads(open('conf.json','r').read())
    __config = yaml.safe_load(conf)
    #print(__config)

API_HOST = __config['backend']['url']

# exit()

__allow_log = True


def log(log):
    # 编译程序
    if __allow_log:
        f = open("judge.log", 'a', encoding='utf-8')
        f.write(time.strftime('%Y/%m/%d %H:%M:%S ')+log+'\n')
        f.close()

try:
    log('评测系统初始化中......')
    
    log('================================================================')
    log('#      #   #######   ####  #     # #####    ###### #######      ')
    log(' #    #   ##             # #     # #    ## ##      #            ')
    log('  #  #    #              # #     # #     # #       #            ')
    log('   ##     #              # #     # #     # #       #######      ')
    log('  #  #    #              # #     # #     # #    ## #            ')
    log(' #    #   ##       ##    # ##   ## #    ## ##    # #            ')
    log('#      #   #######   ####   #####  #####    ###### #######      ')
    log('                         好用别忘记点个star!                       ')
    log('                             https://github.com/Rickyxrc/xcjudge')
    log('================================================================')

    #print('logging in......', end='')
    #print(__config['backend']['url'])
    logging = requests.post(API_HOST+'/users/login', params={
        "username": __config['backend']['username'],
        "password": __config['backend']['password']
    })
    #print(logging)
    logging = json.loads(logging.text)

    __session = ""

    #print(logging)
    try:
        if logging['msg'] == 'access denied.':
            log('账号密码配置错误，正在退出......')
            log('================================================================')
            exit()
    except KeyError:
        log('登录成功.')
        __session = logging['session']
    
    

    while True:
        log('抓取新的评测请求......')
        # #print('setting problems......',end='')
        # #print(__session)
        # #print('done')

        # #print("getting unjudged problems......",end='')
        res = requests.post(API_HOST+'/records/unjudged', params={
            "session": __session,
        })

        res = json.loads(res.text)
        # #print('done.')

        for t in res:
            #print('new judge request appeared.')
            log('接受到新的评测请求.')

            log('评测编号 '+str(t['id']))

            status = ''

            res = requests.post(API_HOST+'/records/get', params={
                "session": __session,
                "rid": t['id']
            })
            # #print(t['id'])
            judgedata = json.loads(res.text)
            # #print(judgedata['username'])
            # #print(judgedata['problem'])
            # #print(judgedata['code'])
            #print(judgedata['username'] +' submited new problem,pid='+str(judgedata['problem']))

            log("用户名称 "+str(judgedata['username']))
            log("题目编号 "+str(judgedata['problem']))
            log("时间限制 "+str(judgedata['timelimit']))
            log("空间限制 "+str(judgedata['memlimit']))
            

            f = open("./code/code.cpp", "w")
            f.write(judgedata['code'])
            f.close()

            os.system("rm ./code/code")

            # compile
            os.system("docker stop judge")
            #print('container killed.')

            os.system("docker rm judge")
            #print('container removed.')

            log("开始编译.")
            os.system("docker run --name judge -v /home/xjcw/xcjudge/code:/code rickyxrc/xincheng-judge")
            #print("docker run --name judge -v /home/xjcw/xcjudge/code:/code rickyxrc/xincheng-judge")
            log("编译完成.")

            os.system("docker stop judge")
            #print('container killed.')

            os.system("docker rm judge")
            #print('container removed.')

            if not os.path.exists('./code/code'):
                #print(t['id'], "CE")
                res = requests.post(API_HOST+'/records/set', params={
                    "session": __session,
                    "rid": t['id'],
                    "status": 'C'
                })
                log('编译错误.')
                log(str(t['id'])+'号评测完成!')
                log('结果: C')
                log('================================================================')
                # #print(res.text)
            else:
                log('编译成功,开始评测.')
                # #print(t)
                os.system("rm ./run/code 2>nul")
                os.system("rm ./run/code.out 2>nul")
                shutil.copy("./code/code", "./run/code")
                try:
                    # print('------------------',str(judgedata['problem']))
                    for i in os.listdir('./testdata/'+str(judgedata['problem'])):
                        # print("////////",i)
                        if i[-1] == 'n':
                            os.system("rm ./run/code.in")
                            os.system("cp ./testdata/" +
                                        str(judgedata['problem'])+'/'+i+" ./run/code.in")

                            os.system("docker stop runner")
                            #print('container killed.')

                            os.system("docker rm runner")
                            #print('container removed.')

                            #print("pre-start process......")
                            subprocess.Popen(
                                "docker run --name runner -v /home/xjcw/xcjudge/run:/code rickyxrc/xcrun", shell=True)
                            #print("start process......")

                            time.sleep(2)

                            os.system("docker kill runner")
                            #print('container killed.')

                            info = json.loads(os.popen("docker inspect runner","r").read())
                            ste = datetime.datetime.strptime(info[0]['State']['StartedAt'][:-4],'%Y-%m-%dT%H:%M:%S.%f').timestamp()
                            fin = datetime.datetime.strptime(info[0]['State']['FinishedAt'][:-4],'%Y-%m-%dT%H:%M:%S.%f').timestamp()
                            # #print(ste,fin)
                            used_ms = (fin-ste)*1000
                            log("执行用时:"+str(used_ms)+"毫秒")
                            # #print(used_ms)

                            os.system("docker rm runner")
                            #print('container removed.')

                            err = open("./run/code.err").read().strip()
                            # #print("E",err)
                            if err != '':
                                log('数据点 '+str(i)+' 运行时错误.')
                                status += 'R'

                            else:
                                if used_ms <= int(judgedata['timelimit']):
                                    f = open("./run/code.out").read().strip()
                                    
                                    # print("..............","./testdata/"+str(judgedata['problem'])+"/"+i.split('.')[0]+'.ans')
                                    a = open("./testdata/"+str(judgedata['problem'])+"/"+i.split('.')[0]+'.ans').read().strip()

                                    # #print(f)
                                    # #print(a)

                                    if f == a:
                                        log('数据点 '+str(i)+' 通过.')
                                        status += 'A'
                                    else:
                                        log('数据点 '+str(i)+' 结果错误.')
                                        status += 'W'
                                else:
                                    log('数据点 '+str(i)+' 运行超时.')
                                    status += 'T'

                    log(str(t['id'])+'号评测完成,结果 '+status)
                    log("================================================================")

                    res = requests.post(API_HOST+'/records/set', params={
                        "session": __session,
                        "rid": t['id'],
                        "status": status
                    })

                except FileNotFoundError:
                    log('ERROR:题目XC'+str(judgedata['problem'])+'暂无评测数据')
                    log("================================================================")
                    #print("NO TEST DATA!")

                    # #print(t['id'], "OK")
        # time.sleep(30)
        # #print("fetching.....")
except KeyboardInterrupt:
    log("正在停止......")
    log('================================================================')
    #print('exit')
