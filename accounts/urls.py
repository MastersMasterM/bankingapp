from django.urls import path
from . import views
from django.contrib.auth.views import LoginView,LogoutView
urlpatterns = [
    path('',views.indexView,name="home"),
    path('accounts/login/',views.login,name="login"),
    path('accounts/signup/',views.signup,name="signup"),
    path('accounts/dashboard/<str:user>',views.dashboard,name="dashboard"),
    path('dashboard/deposit/<str:user>/<str:acc_num>/<str:amount>',views.deposit,name="deposit"),
    path('dashboard/withdraw/<str:user>/<str:acc_num>/<str:amount>',views.withdraw,name="withdraw"),
    path('dashboard/transfer/<str:user>/<str:acc_num>/<str:to_acc>/<str:amount>',views.transfer,name="transfer"),
    path('dashboard/interest_payment/<str:user>',views.interest_payment,name="interest_payment"),
    path('dashboard/new_balances/<str:user>',views.new_balances,name="new_balances")
]