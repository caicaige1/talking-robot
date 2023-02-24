from flask import Flask, render_template, request, session, redirect
import os
from time import time
import pymssql
import answer
import json
import random
import requests
from flask_session import Session
import redis
import openai


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(30)
app.config['SESSION_TYPE']='redis'
app.config['SESSION_REDIS']=redis.Redis(host='8.130.33.205',port='6379',password='123456')
Session(app)
openai.api_key = "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"

client_id = "UQeBiI4cPOlFFnICUSsRSPfr"
client_secret = "ayPatGswBPO7druGCezni91aARk8ksrf"

def unit_chat(chat_input, user_id="user"):
    # 设置默认回复
    chat_reply = "系统繁忙，请重新尝试，谢谢配合"
	# 固定的url格式
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"%(client_id, client_secret)
    res = requests.get(url)
    access_token = eval(res.text)["access_token"]
    unit_chatbot_url = "https://aip.baidubce.com/rpc/2.0/unit/service/chat?access_token=" + access_token
    # 拼装聊天接口对应请求
    post_data = {
                    "log_id": str(random.random()),  #登陆的id，是什么不重要，我们用随机数生成一个id即可
                    "request": {
                        "query": chat_input,  #用户输入的内容
                        "user_id": user_id  #用户id
                    },
                    "session_id": "",
                    "service_id": "S76902",  #!!!!这个很重要，必须对应我们创建的机器人的id号，id号在百度大脑中我们创建的闲聊机器人中可见
                    "version": "2.0"
                }
    # 将聊天接口对应请求数据转为json数据
    res = requests.post(url=unit_chatbot_url, json=post_data)
    # 获取聊天接口返回数据
    unit_chat_obj = json.loads(res.content)
    # 判断聊天接口返回数据是否出错(error_code == 0则表示请求正确)
    if unit_chat_obj["error_code"] != 0:
        return chat_reply
    # 解析聊天接口返回数据，找到返回文本内容 result -> response_list -> schema -> intent_confidence(>0) -> action_list -> say
    unit_chat_obj_result = unit_chat_obj["result"]
    unit_chat_response_list = unit_chat_obj_result["response_list"]
    # 随机选取一个"意图置信度"[+response_list[].schema.intent_confidence]不为0的技能作为回答
    unit_chat_response_obj = random.choice(
        [unit_chat_response for unit_chat_response in unit_chat_response_list if
         unit_chat_response["schema"]["intent_confidence"] > 0.0])
    unit_chat_response_action_list = unit_chat_response_obj["action_list"]
    unit_chat_response_action_obj = random.choice(unit_chat_response_action_list)
    unit_chat_response_say = unit_chat_response_action_obj["say"]
    if unit_chat_response_say == '你想要问的是以下哪个？':
        unit_chat_response_say = unit_chat_response_list[0]['action_list'][0]['refine_detail']['option_list'][0]['info']['full_answer']    
    if unit_chat_response_say == '我不知道该怎样答复您。':
        # Set up the OpenAI API client
        openai.api_key = "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"

        # Set up the model and prompt
        model_engine = "text-davinci-003"
        prompt = chat_input

        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        response = completion.choices[0].text
        unit_chat_response_say = response
    
    return unit_chat_response_say

@app.route('/')
def index():
    # 已经登录的情况下才能访问
    user_info = session.get('userinfo')

    # 从 session 里面获取不到用户信息，说明未登录
    if user_info is None:
        return redirect('/login')

    return render_template('conversation.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET 请求，展示静态页面
    if request.method == 'GET':
        return render_template('login.html')

    # POST 处理登录逻辑

    # 获取手机号码和密码
    phonenumber = request.form.get('phonenumber')
    password = request.form.get('password')
    # 拼凑 sql 语句
    sql="SELECT * FROM people WHERE phonenumber='%s' and password='%s'"%(phonenumber,password)
    print(sql)
    #数据库连接
    db = pymssql.connect(server='8.130.33.205:1433',
                         user='sa',
                         password='031118DiYi',
                         database='userdb')
    cursor = db.cursor(as_dict=True)
    #执行sql语句
    cursor.execute(sql)
    #获取查询到的单条数据
    user = cursor.fetchone()
    #释放游标
    cursor.close()
    #提交事物
    db.commit()
    #关闭数据库
    db.close()

    # 说明账号不存在，或者用户名或密码错误
    if user is None:
        return '<script>alert("账号不存在，或账号密码错误");location.href="/login"</script>'

    # 将用户信息写入 session
    session['userinfo'] = user

    # 跳转到首页
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # 1 展示注册页面 GET (获取)
    if request.method == 'GET':
        return render_template('register.html')
    else:
        # 接受表单提交过来的 账号和密码
        username = request.form.get('username')

        # 判断用户名是否已经被使用
        sql = "SELECT * FROM people WHERE username='%s'"%(username)
        #连接数据库
        db = pymssql.connect(server='8.130.33.205:1433',
                             user='sa',
                             password='031118DiYi',
                             database='userdb')
        cursor = db.cursor(as_dict=True)
        # 执行sql语句
        cursor.execute(sql)
        # 获取查询到的单条数据
        user = cursor.fetchone()


        # 如果用户不为 None 说明用户名已经被使用了。
        # 需要停止程序的运行，并告诉用户
        if user is not None:
            return '<script>alert("抱歉，用户名已被使用。请换一个");location.href="/register"</script>'

        password = request.form.get('password')
        phonenumber = request.form.get('phonenumber')
        problem = request.form.get('problem')

        # 拼凑 sql 语句
        sql = "INSERT INTO people(username,password,phonenumber,problem) VALUES ('%s','%s','%s','%s')"%(username,password,phonenumber,problem)
        # 创建数据库对象

        # 执行 sql 语句
        add_result = cursor.execute(sql)
        # 保存数据库的修改
        # 释放游标
        cursor.close()
        # 提交事物
        db.commit()
        # 关闭数据库
        db.close()

        if add_result is None:
            return '<script>alert("恭喜您注册成功");location.href="/login"</script>'
            #return '<script>alert("恭喜您注册成功")</script>'
        else:
            return '<script>alert("抱歉您注册失败了");location.href="/register"</script>'
            #return '<script>alert("抱歉您注册失败")</script>'


# @app.route('/info')
# def info():
#     user_info = session.get('userinfo')
#     if user_info is None:
#         return {'code': 401, 'message': '请先登录'}
#
#     return {'code': 200, 'data': {'time': time()}}

@app.route('/answer',methods=['GET','POST'])
def answer():
    #text = request.form.get("contest")
    text = request.get_json()['layout']
    print(text)
    reply = unit_chat(text)
    print(reply)
    return reply
    
@app.route('/forget',methods=['GET','POST'])
def forget():
    if request.method == 'GET':
        return render_template('forget.html')
    else:
        #接受表单中的用户名，手机号码和密保问题答案
        newpassword = request.form.get('newpassword')
        user_name = request.form.get('username')
        phonenumber = request.form.get('phonenumber')
        problem = request.form.get('problem')

        #拼凑sql语句，去数据库中查找用户名手机号和密保答案是否正确
        sql="SELECT * FROM people WHERE username='%s' and problem='%s' and phonenumber = '%s'"%(user_name,problem,phonenumber)
        # 连接数据库
        db = pymssql.connect(server='8.130.33.205:1433',
                             user='sa',
                             password='031118DiYi',
                             database='userdb')
        cursor = db.cursor(as_dict=True)
        # 执行sql语句
        cursor.execute(sql)
        # 获取查询到的单条数据
        user = cursor.fetchone()

        # 说明账号不存在，或者用户名或密码错误
        if True is None:
            return '<script>alert("账号不存在或用户名、手机号码、密保答案错误");location.href="/forget"</script>'
        sql1 = "UPDATE people SET password = '%s' WHERE username = '%s'"%(newpassword,user_name)
        print(sql1)
        # 执行sql语句
        cursor.execute(sql1)
        # 释放游标
        cursor.close()
        # 提交事物
        db.commit()
        # 关闭数据库
        db.close()

        # 跳转到首页
        return redirect('/login')

if __name__ == '__main__':
    app.run()
