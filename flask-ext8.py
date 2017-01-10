from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                            current_user, login_required, fresh_login_required)

app = Flask(__name__)
# 注册lgin_manager
login_manager = LoginManager(app)
# 以下内容可写可不写 这些都是默认值  @login_manager.unauthorized_handler  你可以用这个修饰器重新定义的
# 设置登录视图的名称，如果一个未登录用户请求一个只有登录用户才能访问的视图，
# 则闪现一条错误消息，并重定向到这里设置的登录视图。
# 如果未设置登录视图，则直接返回401错误。
# login_manager.login_view = 'login'
# # 设置当未登录用户请求一个只有登录用户才能访问的视图时，闪现的错误消息的内容，
# # 默认的错误消息是：Please log in to access this page.。
# # 如果写了@login_manager.unauthorized_handler 默认的类型就会被替换
# login_manager.login_message = 'Unauthorized User'
# # 设置闪现的错误消息的类别
# login_manager.login_message_category = "info"
# 以上内容可写可不写

users = [
    {'username': 'tom', 'password': '111111'},
    {'username': 'Michael', 'password': '123456'}
]
# 直接继承Usermixin 不用写三个属性一个方法 这个其实是一个models
class User(UserMixin):
    pass

# 通过用户名，获取用户记录，如果不存在，则返回None  用User.query_filter_by(username=username).first() 简便多了
def query_user(username):
    for user in users:
        if user['username'] == username:
            return user

# 什么是回调 允许了底层代码（session[""]）调用在高层定义(loaa_user)装饰器@login_manager.user_loader的子程序
# 这个装饰器的作用是 告诉底层的代码 如果你遇到一个名字叫做username的客户（一般只有登陆了才会写到session里面的 底层就是在session里面找到username的 但是它不知道数据里面有没有 所以他要回调高层的代码来验证整个事实）
#  你不知道他有没有注册  你可以来我（高层即load_user）这里找 我来告诉你（底层）它（这个session[username]）有没有登记在册
# 如果没有找到，返回None。此时的id将会自动从session中移除
@login_manager.user_loader
def load_user(username):
    # 如果找到为真 query_user是自定义的函数
    if query_user(username) is not None:
        # 那就把它存到User类里面
        curr_user = User()
        # 这个名字必须是XX.id要不然23行那里的继承的get_id找不到东西
        curr_user.id = username
        # 返回这个对象
        print('load_user被执行 你看下是不是一登陆就会触发呀')
        return curr_user
    # Must return None if username not found

# 从请求参数中获取Token，如果Token所对应的用户存在则构建一个新的用户类对象
# 并使用用户名作为ID，如果不存在，必须返回None
# @login_manager.request_loader
#     username = request.args.get('token')
#     user = query_user(username)
#     if user is not None:
#         curr_user = User()
#         curr_user.id = username
#         return curr_user
#     # Must return None if username not found

# 这代码的意思是告诉底层 如果遇到一个没有注册的用户 你告诉我（unauthorized_handler），我告诉没有注册的用户 你没有登陆
# 系统有个默认的处理办法在 login_manager.login_message = 'Unauthorized User' 定义
# 如果把下面这行注释掉的话 一打开主页就会跳转到需要登陆的界面
# 需要登陆的界面 在login_manager.login_view = 'login' 定义
@login_manager.unauthorized_handler
def unauthorized_handler():
    print('unauthorized_handler被执行')
    return '没有登陆'

@app.route('/')
# 如果需要登陆加这一句话
@login_required
def index():
    return render_template('hello.html')

@app.route('/home')
# 当用户通过账号和密码登录后，Flask-Login会将其标识为Fresh登录，即在Session中设置”_fresh”字段为True。
# 而用户通过Remember Me自动登录的话，则不标识为Fresh登录。
# 对于”@login_required”装饰器修饰的视图，是否Fresh登录都可以访问，但是有些情况下，我们会强制要求用户登录一次，比如修改登录密码，
# 这时候，我们可以用”@fresh_login_required”装饰器来修饰该视图。这样，通过Remember Me自动登录的用户，将无法访问该视图：
@fresh_login_required
def home():
    # current_user是你在@login_manager.user_loader 里面生成了User类实例 它是全局变量 所以这个你可以使用它的方法
    # get_id 方法是你直接继承来的
    return 'Logged in as: %s' % current_user.get_id()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        # query_user() 是你自己定义的 返回存在的类
        user = query_user(username)
        # 验证表单中提交的用户名和密码
        if user is not None and request.form['password'] == user['password']:
            curr_user = User()
            curr_user.id = username

            # 通过Flask-Login的login_user方法登录用户 内置的方法
            login_user(curr_user, remember=True)

            # 如果请求中有next参数，则重定向到其指定的地址，
            # 没有next参数，则重定向到"index"视图
            next = request.args.get('next')
            return redirect(next or url_for('index'))
        # 执行到这里 肯定是验证不通过了啦
        flash('Wrong username or password!')
    # 既然没有登陆成功 那就继续登陆呗
    return render_template('login.html')

@app.route('/logout')
# 再调用一次就退出了？
@login_required
def logout():
    # 直接调用了原生的方法退出的 登陆的时候用login_user 登出的时候用logout_user
    logout_user()
    return 'Logged out successfully!'

# 这个是form表单要求的
app.secret_key = '1234567'

if __name__ == '__main__':
    app.run(debug=True)
