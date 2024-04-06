from flask import flash,Flask,render_template,redirect,url_for,jsonify,request,session,abort
from flask_mysqldb import MySQL
from datetime import datetime,timedelta
from datetime import date
from flask_session import Session
from key import * 
from sdmail import sendmail
from itsdangerous import URLSafeTimedSerializer
from tokenreset import token

app=Flask(__name__)
app.secret_key='A@Bullela@_3'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='calorie'
app.config["SESSION_TYPE"]="filesystem"
mysql=MySQL(app)
Session(app)
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/homepage/<id1>',methods=['GET','POST'])
def homepage(id1):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select target from users where id=%s',[id1])
        target=cursor.fetchone()[0]
        print(target)
        cursor.execute('select  consumed  from users where id=%s',[id1])
        consumed=cursor.fetchone()[0]
        cursor.execute('select workouttarget from users where id=%s',[id1])
        worktarget=cursor.fetchone()[0]
        cursor.execute('select workoutconsumed from users where id=%s',[id1])
        workconsumed=cursor.fetchone()[0]
        current_date=date.today()
        current_date=f"{current_date.year}-{current_date.month}-{current_date.day}"
        today_date=datetime.strptime(current_date,'%Y-%m-%d')
        date_today=datetime.strftime(today_date,'%Y-%m-%d')
        seven_back=date.today()-timedelta(days=7)
        seven_days_back=datetime.strftime(seven_back,'%Y-%m-%d')
        # print(f'SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id={id1} AND date={date_today} GROUP BY item, category ORDER BY category ASC')
        cursor.execute('SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id=%s AND date=%s GROUP BY item, category ORDER BY category ASC', [id1, date_today])
        day_report=cursor.fetchall()
        print(f"SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id={id1} AND date>={date_today} GROUP BY item ORDER BY category ASC")
        cursor.execute('SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id=%s AND date >= %s GROUP BY item, category ORDER BY category ASC', [id1, seven_days_back])
        sevendays_report=cursor.fetchall()
        cursor.execute('select workout,sum(time),sum(callories) from workout_track where id=%s and date=%s group by workout',[session.get('user'),date_today])
        day_report_w=cursor.fetchall()
        cursor.execute('select workout,sum(time),sum(callories) from workout_track where id=%s and date>=%s group by workout',[session.get('user'),seven_days_back])
        sevendays_report_w=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            if 'target' in [i for i in request.form]:
                target=request.form['target']
                cursor=mysql.connection.cursor()
                cursor.execute('update users set target=%s where id=%s',[target,id1])
                mysql.connection.commit()
                cursor.close()
            if 'worktarget' in [i for i in request.form]:
                worktarget=request.form['worktarget']
                cursor=mysql.connection.cursor()
                cursor.execute('update users set workouttarget=%s where id=%s',[worktarget,id1])
                mysql.connection.commit()
                cursor.close()
            return render_template('profile.html',target=target,id1=id1,consumed=consumed,worktarget=worktarget,workconsumed=workconsumed,day_report=day_report,sevendays_report=sevendays_report,day_report_w=day_report_w,sevendays_report_w=sevendays_report_w)
        return render_template('profile.html',target=target,id1=id1,consumed=consumed,worktarget=worktarget,workconsumed=workconsumed,day_report=day_report,sevendays_report=sevendays_report,day_report_w=day_report_w,sevendays_report_w=sevendays_report_w)
    return redirect(url_for('login'))
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        id1=request.form['id']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT ID from users')
        users=cursor.fetchall()
        cursor.close()
        if (id1,) in users:
            flash('User Id already Exists')
            return render_template('registration.html')
        name=request.form['name']
        email=request.form['email']
        number=request.form['number']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from users where name=%s',[name])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'id':id1,'name':name,'password':password,'email':email,'number':number}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=300)
    except Exception as e:
        print(e)
        return 'Link Expired register again'
    else:
        cursor=mysql.connection.cursor()
        name=data['name']
        cursor.execute('select count(*) from users where name=%s',[name])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users (id,name,email,mobile_no,password) values(%s,%s,%s,%s,%s)',[data['id'],data['name'],data['email'],data['number'],data['password']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))

'''@app.route('/forgotpassword',methods=('GET', 'POST'))
def forgotpassword():
    if request.method=='POST':
        id1 = request.form['id']
        cursor=mysql.connection.cursor() 
        cursor.execute('select id from users') 
        deta=cursor.fetchall()
        if (id1,) in deta:
            cursor.execute('select email from users where id=%s',[id1])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using-\{request.host+url_for("resetpwd",token=token(id1,300))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your registered mail id')
            return redirect(url_for('login'))
        else:
            flash('user does not exits')
    return render_template('forgot.html')



@app.route('/resetpwd/<token>',methods=('GET', 'POST'))
def resetpwd(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        id1=s.loads(token)['user']
        if request.method=='POST':
            npwd = request.form['npassword']
            cpwd = request.form['cpassword']
            if npwd == cpwd:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where id=%s',[npwd,id1])
                mysql.connection.commit()
                cursor.close()
                return 'Password reset Successfull'
            else:
                return 'Password does not matched try again'
        return render_template('newpassword.html')
    except Exception as e:
        abort(410,description='reset link expired')'''

@app.route('/forget',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from users where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mysql.connection.cursor()
            cursor.execute('SELECT email from users where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('homepage',id1=session['user']))
    if request.method=="POST":
        user=request.form['user']
        password=request.form['password']
        cursor=mysql.connection.cursor() 
        cursor.execute('select password from users where id=%s',[user])
        data=cursor.fetchone()
        print(data)
        cursor.close() 
        if data:
            if password==data[0]:
                session['user']=user
                return redirect(url_for('homepage',id1=user))
            else:
                flash('Invalid Password')
                return render_template('login.html')
        else:
            flash('Invalid user id')
            return render_template('login.html')      
    return render_template('login.html')
@app.route('/addfood',methods=['GET','POST'])
def addfood():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        today=date.today()
        current_date=datetime.strptime(f'{str(today.year)}-{str(today.month)}-{str(today.day)}','%Y-%m-%d')
        cursor.execute('SELECT item from items order by category asc')
        items=cursor.fetchall()
        cursor.execute('SELECT target from users where id=%s',[session.get('user')])
        target=int(cursor.fetchone()[0])
        current_date=date.today()
        current_date=f"{current_date.year}-{current_date.month}-{current_date.day}"
        today_date=datetime.strptime(current_date,'%Y-%m-%d')
        date_today=datetime.strftime(today_date,'%Y-%m-%d')
        cursor.execute('SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id=%s AND date=%s GROUP BY item, category',[session.get('user'),date_today])
        day_report=cursor.fetchall()
        cursor.close()
        if target==0:
            flash('Set the target first!')
            return render_template('addfood.html',id1=session['user'],items=items)
        if request.method=="POST":
            cursor=mysql.connection.cursor()
            item=request.form['item']
            category=request.form['category']
            quantity=int(request.form['quantity'])
            cursor.execute('SELECT carbohydrates,fats,protein,fiber,calorie from items where item=%s',[item])
            cal_data=cursor.fetchone()
            carbohydrates=round(quantity*(cal_data[0]/100),2)
            fats=round(quantity*(cal_data[1]/100),2)
            protein=round(quantity*(cal_data[2]/100),2)
            fiber=round(quantity*(cal_data[3]/100),2)
            calories=round(quantity*(cal_data[4]/100),2)
            cursor.execute('SELECT consumed from users where id=%s',[session.get('user')])
            consumed=round(float(cursor.fetchone()[0]),2)+calories
            cursor.execute('update users set consumed=%s where id=%s',[consumed,session.get('user')])
            cursor.execute('insert into callorie_track (id,item,category,quantity,carbohydrates,fats,protein,fiber,callories,date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',[session.get('user'),item,category,quantity,carbohydrates,fats,protein,fiber,calories,current_date])
            mysql.connection.commit()
            cursor.execute('SELECT item, category, SUM(quantity), SUM(carbohydrates), SUM(fats), SUM(protein), SUM(fiber), SUM(callories) FROM callorie_track WHERE id=%s AND date=%s GROUP BY item, category',[session.get('user'),date_today])
            day_report=cursor.fetchall()
            cursor.close()
            return render_template('addfood.html',id1=session['user'],items=items,day_report=day_report)
        return render_template('addfood.html',id1=session['user'],items=items,day_report=day_report)
    return redirect(url_for('login'))
@app.route('/addworkout',methods=['GET','POST'])
def addwork():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        today=date.today()
        current_date=datetime.strptime(f'{str(today.year)}-{str(today.month)}-{str(today.day)}','%Y-%m-%d')
        cursor.execute('SELECT workout from workout')
        workouts=cursor.fetchall()
        cursor.execute('SELECT workouttarget from users where id=%s',[session.get('user')])
        workouttarget=int(cursor.fetchone()[0])
        current_date=date.today()
        current_date=f"{current_date.year}-{current_date.month}-{current_date.day}"
        today_date=datetime.strptime(current_date,'%Y-%m-%d')
        date_today=datetime.strftime(today_date,'%Y-%m-%d')
        cursor.execute('select workout,sum(time),sum(callories) from workout_track where id=%s and date=%s group by workout',[session.get('user'),date_today])
        day_report=cursor.fetchall()
        cursor.close()
        if workouttarget==0:
            flash('Set the target first!')
            return render_template('addworkout.html',id1=session['user'],workouts=workouts)
        if request.method=="POST":
            cursor=mysql.connection.cursor()
            time=float(request.form['time'])
            category=request.form['category']
            cursor.execute('SELECT time,callories from workout where workout=%s',[category])
            cal_data=cursor.fetchone()
            calories=round(time*(cal_data[1]/cal_data[0]),2)
            cursor.execute('SELECT workoutconsumed from users where id=%s',[session.get('user')])
            consumed=round(float(cursor.fetchone()[0]),2)+calories
            cursor.execute('update users set workoutconsumed=%s where id=%s',[consumed,session.get('user')])
            cursor.execute('insert into workout_track (workout,time,id,callories,date) values(%s,%s,%s,%s,%s)',[category,time,session.get('user'),calories,current_date])
            mysql.connection.commit()
            cursor.execute('select workout,sum(time),sum(callories) from workout_track where id=%s and date=%s group by workout',[session.get('user'),date_today])
            day_report=cursor.fetchall()
            cursor.close()
            return render_template('addworkout.html',id1=session['user'],workouts=workouts,day_report=day_report)
        return render_template('addworkout.html',id1=session['user'],workouts=workouts,day_report=day_report)
    return redirect(url_for('login'))
@app.route('/logout')
def logout():
    session['user']=None
    return redirect(url_for('home'))
@app.route('/view')
def view():
    return render_template('details.html')
app.run(debug=True,use_reloader=True)
