from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    credit_score = models.IntegerField(null=True, blank=True)

class Transaction(models.Model):
    aadhar_id = models.CharField(max_length=12, unique=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    TRANSACTION_TYPE_CHOICES = [('DEBIT', 'DEBIT'), ('CREDIT', 'CREDIT')]
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_TYPE_CHOICES)

class Loan(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=20, choices=[('Car', 'Car'), ('Home', 'Home'), ('Education', 'Education'), ('Personal', 'Personal')])
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField()
    disbursement_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending') # Status can be Pending, Approved, Rejected

class EMI(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
