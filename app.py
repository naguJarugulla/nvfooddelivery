from flask import Flask,url_for,session,redirect,render_template,request,flash,send_file
from flask_session import Session 
#from flask_mysqldb import MySQL
import mysql.connector
from io import BytesIO
import io
import mysql.connector
import os
from otp import genotp
from cmail import sendmail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from token1 import token
import stripe

stripe.api_key='sk_test_51MzcVYSDVehZUuDTkwGUYe8hWu2LGN0krI8iO5QOAEqoRYXx3jgRVgkY7WzXqQmpN62oMWM59ii76NKPrRzg3Gtr005oVpiW82'
#from otp import genotp 
#from cmail import sendmail
app=Flask(__name__)
app.secret_key = '23efgbnjuytr'


app.config['SESSION_TYPE'] = 'filesystem'

db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']

mydb=mysql.connector.connect(host='host',user=user,password=password,db=db,port=port)
with mysql.connector.connect(host=host,user=user,password=password,db=db,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute("create table if not exists user(name varchar(30) primary key,email varchar(40) unique,password varchar(10),phnumber bigint unique,state varchar(20),address varchar(50),pincode int)")
    cursor.execute("create table if not exists admin(rid varchar(10) primary key,name varchar(20),place  varchar(30),email varchar(40),password varchar(20))")
    cursor.execute("create table if not exists additems(itemid varchar(9) primary key,name varchar(30),category enum('fastfoods','vegfoods','nonvegfoods','pastry','icecreams','homefood','starters','soups'),price decimal(10,0),foreign key(rid) references references students(rid))")
    cursor.execute("create table if not exists orders(ordid int primary key auto_increment),itemid varchar(9),name varchar(30),qty int,total_price int,user varchar(30),foreign key(itemid) references additems(itemid) on update cascade on delete cascade,foreign key(user) references user(name) on update cascade on delete cascade)")
    cursor.execute("create table if not exists contactus(resturant_name varchar(50),name varchar(30),email varchar(40),subject tinytext,feedback tinytext)")
 

Session(app)
mysql = MySQL(app)
@app.route('/') 
def index():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select name from admin')
    resturants=cursor.fetchall()
    return render_template('home.html',resturants=resturants)
@app.route('/signin', methods = ['GET','POST'])
def register():
    if session.get('user'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password= request.form['password']
        phno= request.form['phno']
        state=request.form['state']
        address=request.form['address']
        pincode=request.form['pincode']
        cursor=mydb.cursor(buffered=True)
        cursor.execute ('select name from user')
        data = cursor.fetchall()
        cursor.execute ('select email from user')
        edata = cursor.fetchall()
        if (name,)in data:
            flash('user already exits')
            return render_template('usersignin.html')
        if (email,)in edata:
            flash('email already exits')                                                                                                                                                                                                                                                                                                                                                                                                                                                         
            return render_template('usersignin.html')
        cursor.close()
        otp = genotp()
        subject = 'thanks for registering'
        body = f'use this otp register {otp}'
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,name=name,email=email,password=password,phno=phno,state=state,address=address,pincode=pincode)

    return render_template('usersignin.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('index'))
    if request.method=='POST':
        name=request.form['name']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where name=%s and password=%s',[name,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('invalid user name or password')
            return render_template('userlogin.html')
        else:
            session['user']=name
            if not session.get(name):
                session[name]={}
            return redirect(url_for('index'))
    return render_template('userlogin.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash('u are already logged out!')
        return redirect(url_for('login'))
        #return redirect(url_for('loginp'))
@app.route('/otp/<otp>/<name>/<email>/<password>/<phno>/<state>/<address>/<pincode>',methods = ['GET','POST'])
def otp(otp,name,email,password,phno,state,address,pincode):
    if request.method == 'POST':
        uotp=request.form['otp']
        if otp == uotp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into user values(%s,%s,%s,%s,%s,%s,%s)',(name,email,password,phno,state,address,pincode))
            mydb.commit()
            cursor.close()
            flash('Details Registered')#send mail to the user as successful registration
           
            return redirect(url_for('index'))
        else:
            flash('wrong otp')
            return render_template('otp.html',otp = otp,name = name,email=email,password= password,phno=phno,state=state,address=address,pincode=pincode)


@app.route('/forgetpassword',methods=['GET','POST'])
def forget():#after clicking the forget password
    if request.method=='POST':
        username=request.form['username']# store the id in the rollno
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select name from user')# fetch the username data in the table students
        data=cursor.fetchall()#fetching all the rollno data and store it in the "data" variable 
        if (username,) in data:# if the given rollno of the user is present in tha database->data
            cursor.execute('select email from user where name=%s',[username])#it fetches email related to the rollno 
            data=cursor.fetchone()[0]#fetch the only one email related to the rollno 
            #print(data)
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("createpassword",token=token(username,200))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            #return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('forgetpassword.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):#to create noe password and conform the password
        try:
            s=Serializer(app.config['SECRET_KEY'])
            username=s.loads(token)['user']
            if request.method=='POST':
                npass=request.form['npassword']
                cpass=request.form['cpassword']
                if npass==cpass:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('update user set password=%s where name=%s',[npass,username])
                    mydb.commit()
                    return 'Password reset Successfull'
                    return redirect(url_for('login'))
                else:
                    return 'Password mismatch'
            return render_template('createpassword.html')
        except Exception as e:
            print(e)
            return 'Link expired try again'
#----------------------------admin login---------------------------------------
@app.route('/adminsignin', methods = ['GET','POST'])
def aregister():
    if session.get('admin'):
        return redirect(url_for('admin'))
    if request.method == 'POST':
        rid=request.form['rid']
        rname = request.form['rname']
        place= request.form['place']
        email = request.form['email']
        password= request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute ('select name from admin')
        data = cursor.fetchall()
        cursor.execute ('select email from admin')
        edata = cursor.fetchall()
        if (rid,)in data:
            flash('user already exits')
            return render_template('adminregisterpage.html')
        if (email,)in edata:
            flash('email already exits')                                                                                                                                                                                                                                                                                                                                                                                                                                                         
            return render_template('adminregisterpage.html')
        cursor.close()
        otp = genotp()
        subject = 'thanks for registering'
        body = f'use this otp register {otp}'
        sendmail(email,subject,body)
        return render_template('aotp.html',otp=otp,rid=rid,rname=rname,place=place,email=email,password=password)
    return render_template('adminregisterpage.html')
@app.route('/alogin',methods=['GET','POST'])
def alogin():
    if session.get('admin'):
        return redirect(url_for('admin'))
    if request.method=='POST':
        rid=request.form['rid']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from admin where rid=%s and password=%s',[rid,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('invalid user name or password')
            return render_template('adminlogin.html')
        else:
            session['admin']=rid
            return redirect(url_for('admin'))
    return render_template('adminlogin.html')
@app.route('/alogout')
def alogout():
    if session.get('admin'):
        session.pop('admin')
        return redirect(url_for('index'))
    else:
        flash('u are already logged out!')
        return redirect(url_for('alogin'))
        #return redirect(url_for('loginp'))
@app.route('/aotp/<otp>/<rid>/<rname>/<place>/<email>/<password>',methods = ['GET','POST'])
def aotp(otp,rid,rname,place,email,password):
    if request.method == 'POST':
        uotp=request.form['otp']
        if otp == uotp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into admin values(%s,%s,%s,%s,%s)',(rid,rname,place,email,password))
            mydb.commit()
            cursor.close()
            flash('Details Registered')#send mail to the user as successful registration
            return redirect(url_for('index'))
        else:
            flash('wrong otp')
            return render_template('aotp.html',otp = otp,rid=rid,rname =rname,place=place,email=email,password= password)


@app.route('/aforgetpassword',methods=['GET','POST'])
def aforget():#after clicking the forget password
    if request.method=='POST':
        userid=request.form['rid']# store the id in the rollno
        cursor=mydb.cursor(buffered=True)#connection to mysql
        cursor.execute('select rid from admin')# fetch the username data in the table students
        data=cursor.fetchall()#fetching all the rollno data and store it in the "data" variable 
        if (userid,) in data:# if the given rollno of the user is present in tha database->data
            cursor.execute('select email from admin where rid=%s',[userid])#it fetches email related to the rollno 
            data=cursor.fetchone()[0]#fetch the only one email related to the rollno 
            #print(data)
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("acreatepassword",token=token(userid,200))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            #return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('aforgetpassword.html')
@app.route('/acreatepassword/<token>',methods=['GET','POST'])
def acreatepassword(token):#to create noe password and conform the password
        try:
            s=Serializer(app.config['SECRET_KEY'])
            username=s.loads(token)['admin']
            if request.method=='POST':
                npass=request.form['npassword']
                cpass=request.form['cpassword']
                if npass==cpass:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('update admin set password=%s where rid=%s',[npass,username])
                    mydb.commit()
                    return 'Password reset Successfull'
                    return redirect(url_for('login'))
                else:
                    return 'Password mismatch'
            return render_template('acreatepassword.html')
        except Exception as e:
            print(e)
            return 'Link expired try again'

@app.route('/admindashboard',methods=['GET','POST'])
def admindashboard():
    if request.method=="POST":
        id1=genotp()
        name=request.form['name']
        category=request.form['category']
        price=request.form['price']
        image=request.files['image']
        cursor=mydb.cursor(buffered=True)
        filename=id1+'.jpg'
        cursor.execute('insert into additems(itemid,name,category,price,rid) values(%s,%s,%s,%s,%s)',[id1,name,category,price,session.get('admin')])
        mydb.commit()
        print(filename)
        path=os.path.dirname(os.path.abspat(__file__))
        static_path=os.path.join(path,'static')
        image.save(os.path.join(static_path,filename))
        print('success')
        return redirect(url_for('available'))
    return render_template('admindashboard.html')

#-------------------only session resturant items view to the admin

@app.route('/available')
def available():
    if session.get('admin'):       
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems where rid=%s',[session.get('admin')])
        items=cursor.fetchall()
        return render_template('availableitems.html',items=items)
    else:
        return redirect(url_for('alogin'))
@app.route('/updateitem/<itemid>',methods=['GET','POST'])
def updateitem(itemid):
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select name,category,price from additems where itemid=%s',[itemid])
        items=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            name=request.form['name']
            category=request.form['category']
            price=request.form['price']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update additems set name=%s,category=%s,price=%s where itemid=%s',[name,category,price,itemid])
            mydb.commit()
            cursor.close()
            flash('item updated successfully')
            return redirect(url_for('available'))
        return render_template('updateitems.html',items=items)
    else:
        return redirect(url_for('alogin'))
@app.route('/deleteitem/<itemid>')
def deleteitem(itemid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mydb.commit()
    cursor.close()
    path=r"C:\Users\kalyanijarugulla\OneDrive\Desktop\fd\static"
    filename=f"{itemid}.jpg"
    os.remove(os.path.join(path,filename))
    flash('item deleted successfully')
    return redirect(url_for('available'))
@app.route('/admin')
def admin():
    if session.get('admin'):
        return render_template('adminpage.html')
    else:
        return redirect(url_for('alogin'))
#-----------------all resturant items view to the user
@app.route('/itemspage')
def itemspage():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    #print(name)
    #print(items)
    return render_template('itemspage.html',items=items)
@app.route('/homepage/<category>')
def homepage(category):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from additems where category=%s',[category])
    items=cursor.fetchall()
    return render_template('itemspage.html',items=items)
@app.route('/returantshome/<name>')
def resturantshome(name):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select name from admin')
    resturants=cursor.fetchall()
    cursor.execute('select rid from admin where name=%s',[name])
    rid=cursor.fetchone()[0]
    cursor.execute('select * from additems where rid=%s',[rid])
    ritems=cursor.fetchall()
    return render_template('resturantshome.html',ritems=ritems,resturants=resturants)
#--------------------------------cart card---------------------------------------------------
@app.route('/items',methods=['GET','POST'])
def items():
    return render_template('itemsPage.html')
@app.route('/cart/<itemid>/<name>/<price>')
def cart(itemid,name,price):
    if not session.get('user'):#--noor
        return redirect(url_for('login'))#--noor

    if itemid not in session.get(session.get('user')):
        session[session.get('user')][itemid]=[name,1,price]
        session.modified=True
        #print(session['session.get('user''])
        flash(f'{name} added to cart')
        return redirect(url_for('viewcart'))
    session[session.get('user')][itemid][1]+=1
    flash('Item already in cart quantity increased to +1')
    return redirect(url_for('viewcart'))
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):#--noor
        return redirect(url_for('login'))#---noor
   
    items=session.get(session.get('user')) if session.get(session.get('user')) else 'empty'
    if items=='empty':
        return 'no products in cart'
    #print(items)
    return render_template('cart.html',items=items)
@app.route('/remcart/<item>')
def rem(item):
    if session.get('user'):
        session[session.get('user')].pop(item)
        return redirect(url_for('viewcart'))
    return redirect(url_for('login'))
@app.route('/pay/<itemid>/<name>/<int:price>',methods=['POST'])
def pay(itemid,price,name):
    if session.get('user'):
        q=int(request.form['qty'])
        username=session.get('user')
        total=price*q
        checkout_session=stripe.checkout.Session.create(
            success_url=url_for('success',itemid=itemid,name=name,q=q,total=total,_external=True),
            line_items=[
                {
                    'price_data': {
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price*100,
                        'currency': 'inr',
                    },
                    'quantity': q,
                },
                ],
            mode="payment",)
        return redirect(checkout_session.url)
    else:
        return redirect(url_for('login'))
@app.route('/success/<itemid>/<name>/<q>/<total>')
def success(itemid,name,q,total):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,name,qty,total_price,user) values(%s,%s,%s,%s,%s)',[itemid,name,q,total,session.get('user')])
        mydb.commit()
        
        return 'Order Placed'
    return redirect(url_for('login'))
@app.route('/orders')
def orders():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where user=%s',(session['user'],))
       
        orders=cursor.fetchall()
        
        return render_template('orders.html',orders=orders)
@app.route('/search',methods=['GET','POST'])
def search():
    
    if request.method=="POST":
        name=request.form['search']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems where name=%s',[name])
        data=cursor.fetchall()
        return render_template('itemspage.html',items=data)
@app.route('/contactus',methods=['GET','POST'])
def contactus():
    if session.get('user'):
        if request.method=="POST":

            name=request.form['name']
            email=request.form['email']
            subject=request.form['subject']
            feedback=request.form['feedback']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('isert into contactus (name,email,subject,feedback) values (%s,%s,%s,%s)',[name,email,subject,feedback])
            mydb.commit()
    return render_template('home.html')
@app.route('/readcontact')
def readcontact():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from contactus ')
    details=cursor.fetchall()
    return render_template('readcontact.html',details=details)    
app.run(debug=True, use_reloader=True)
    
    
       
        
