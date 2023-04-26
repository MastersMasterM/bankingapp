from django.shortcuts import render, redirect,HttpResponse
from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect
from django.urls import reverse
import psycopg2

# Connect to your postgres DB
conn = psycopg2.connect(dbname="test", user="postgres", password="ma1379?")


# Create your views here.
def indexView(request):
    return render(request,'accounts/index.html')

def login(request):
    if request.method == "POST":
        username = request.POST['uname']
        password = request.POST['psw']
        with conn.cursor() as curs:
            curs.execute(f"call login('{password}','{username}');")
            notice = conn.notices[0]
            if notice == 'NOTICE:  Successful\n':
                curs.execute('commit')
                return HttpResponseRedirect(reverse("dashboard",args=[username]))
            elif notice == 'NOTICE:  Password is wrong\n':
                return HttpResponseRedirect(reverse('login'))
            else:
                return HttpResponseRedirect(reverse('login'))
    else:
        return render(request,'accounts/login.html')


def signup(request):
    if request.method == "POST":
        password = request.POST['psw']
        f_name = request.POST['f_name']
        l_name = request.POST['l_name']
        national_ID = request.POST['national_ID']
        dof = request.POST['dof']
        type = request.POST['contact']
        ir = request.POST['ir']
        with conn.cursor() as curs:
            curs.execute(f"call register('{password}','{f_name}','{l_name}','{national_ID}','{dof}','{type}','{ir}');")
            notice = conn.notices[0]
            if notice == 'NOTICE:  Your Age is less than 13\n':
                return HttpResponse(notice)
            else:
                curs.execute("commit")
                notice = notice.replace('NOTICE:  ',"")
                notice = notice.replace('\n',"")
                return render(request,'accounts/info.html',{
                    'username' : notice,
                    'pass': password
                })
    else:
        return render(request,'accounts/register.html')
 
def dashboard(request,user):
    with conn.cursor() as curs:
        curs.execute(f"SELECT accountnumber,first_name,last_name FROM account WHERE username = '{user}';")
        res = curs.fetchone()
    with conn.cursor() as curs:
        curs.execute(f"SELECT accountnumber,first_name,last_name FROM account WHERE username = '{user}';")
        res = curs.fetchone()
    account_num = res[0]
    f_name = res[1]
    l_name = res[2]
    with conn.cursor() as curs:
        curs.execute(f"""SELECT amount FROM latest_balances 
                 WHERE accountnumber = '{account_num}' """)
        balance = curs.fetchone()[0]
    return render(request,'accounts/dashboard.html',{
        'user' : user,
        'f_name': f_name,
        'l_name': l_name,
        'acc_num': account_num,
        'balance': balance
    })

def deposit(request,user,acc_num,amount):
    with conn.cursor() as curs:
        curs.execute(f"call deposit('{acc_num}','{amount}');")
        curs.execute('commit')
    return HttpResponseRedirect(reverse('dashboard',args=[user]))

def withdraw(request,user,acc_num,amount):
    with conn.cursor() as curs:
        curs.execute(f"call withdraw('{acc_num}','{amount}');")
        curs.execute('commit')
    return HttpResponseRedirect(reverse('dashboard',args=[user]))

def transfer(request,user,acc_num,to_acc,amount):
    with conn.cursor() as curs:
        curs.execute(f"call transfer('{acc_num}','{to_acc}','{amount}');")
        curs.execute('commit')
    return HttpResponseRedirect(reverse('dashboard',args=[user]))

def interest_payment(request,user):
    with conn.cursor() as curs:
        curs.execute(f"call payment_interest();")
        curs.execute('commit')
    return HttpResponseRedirect(reverse('dashboard',args=[user]))

def new_balances(request,user):
    with conn.cursor() as curs:
        curs.execute(f"call balances_update();")
        curs.execute('commit')
    return HttpResponseRedirect(reverse('dashboard',args=[user]))