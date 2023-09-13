from django.urls import path
from .views import UserProfileCreateView, LoanCreateView, EMICreateView, LoanStatementView

urlpatterns = [
    path('api/register-user/', UserProfileCreateView.as_view(), name='register-user'),
    path('api/apply-loan/', LoanCreateView.as_view(), name='apply-loan'),
    path('api/make-payment/', EMICreateView.as_view(), name='make-payment'),
    path('api/get-statement/<int:pk>/', LoanStatementView.as_view(), name='get-statement'),
]
