from flask import Flask, request, render_template, redirect, url_for, flash, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = "users.json"
QUESTIONS_FILE = "question.json" # 新增

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

def is_admin(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


# 新增函数，用于加载问题
def get_questions():
    with open(QUESTIONS_FILE, "r") as file:
        return json.load(file)

# 确保用户文件存在
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as file:
        json.dump({}, file)

def get_users():
    with open(USERS_FILE, "r") as file:
        content = file.read().strip()
        if not content:  # 文件为空
            return {}  # 返回一个空字典
        return json.loads(content)


def save_user(username, password, level=1):
    users = get_users()
    users[username] = {"password": password, "level": level}
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('challenge'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    users = get_users()

    if is_admin(username, password):  # 检查是否为管理员登录
        session['username'] = username
        session['is_admin'] = True  # 添加一个 session 标记表示这是管理员
        return redirect(url_for('manage'))  # 重定向到管理员界面

    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['is_admin'] = False  # 用户不是管理员
        return redirect(url_for('challenge'))
    else:
        flash('User or password is incorrenct')
        return redirect(url_for('home'))


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    users = get_users()

    if username in users:
        flash('The user name already exists')
        return redirect(url_for('home'))

    save_user(username, password)
    flash('Registration successful, please login')
    return redirect(url_for('home'))


@app.route('/challenge')
def challenge():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    username = session['username']
    users = get_users()
    user_level = users[username]['level']
    questions = get_questions()  # 修改
    question_data = questions.get(str(user_level), None)  # 确保使用字符串作为键
    
    if question_data is None:
        return render_template('congratulations.html')
    
    return render_template('challenge.html', question_data=question_data, level=user_level)

@app.route('/answer', methods=['POST'])
def answer():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    username = session['username']
    users = get_users()
    user_level = users[username]['level']
    user_answer = request.form['answer']
    questions = get_questions()  # 修改
    
    if questions[str(user_level)]['answer'] == user_answer:  # 确保使用字符串作为键
        users[username]['level'] += 1
        save_user(username, users[username]['password'], users[username]['level'])
        flash('Correct! To the next level')
    else:
        flash('Wrong answer, please try again')
    
    return redirect(url_for('challenge'))

@app.route('/manage')
def manage():
    if not session.get('is_admin'):  # 如果不是管理员，重定向到主页
        return redirect(url_for('home'))
    users = get_users()
    return render_template('manager.html', users=users)

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if not session.get('is_admin'):
        flash("You don't have permission to do that!")
        return redirect(url_for('home'))
    users = get_users()
    users.pop(username, None)  # 删除用户
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)
    flash('User deleted successfully')
    return redirect(url_for('manage'))

@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('is_admin'):
        flash("You don't have permission to do that!")
        return redirect(url_for('home'))
    username = request.form['username']
    password = request.form['password']
    level = request.form['level']
    save_user(username, password, level)  # 保存新用户
    flash('User added successfully')
    return redirect(url_for('manage'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
