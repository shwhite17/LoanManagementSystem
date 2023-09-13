import math
from datetime import date
from django.contrib.auth.models import User
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.shortcuts import render
from .models import generics
from .models import Response
from .models import status, Loan, UserProfile, serializers
from .tasks import calculate_credit_score
from .models import UserProfile, Loan, EMI
from .serializers import UserProfileSerializer, LoanSerializer, EMISerializer
from .serializers import UserSerializer

class UserProfileCreateView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def post(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
       
        UserProfile.objects.create(user=user, annual_income=request.data.get('annual_income'))
        calculate_credit_score.delay(user.id)
        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)      

class LoanCreateView(generics.CreateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    
    def create(self, request, *args, **kwargs):
        user_profile_id = request.data.get('unique_user_id')
        user_profile = UserProfile.objects.get(id=user_profile_id)
        
        if (
            user_profile.credit_score >= 450 and
            user_profile.annual_income >= 150000 and
            self.validate_loan_amount(request.data)
        ):
            loan = Loan.objects.create(
                user=user_profile,
                loan_type=request.data['loan_type'],
                loan_amount=request.data['loan_amount'],
                interest_rate=request.data['interest_rate'],
                term_period=request.data['term_period'],
                disbursement_date=request.data['disbursement_date']
            )
            
            emi_schedule = self.calculate_emi_schedule(
                loan.loan_amount, loan.interest_rate, loan.term_period
            )
            for due_date, amount_due in emi_schedule:
                EMI.objects.create(
                    loan=loan,
                    due_date=due_date,
                    amount_due=amount_due
                )
                
            return Response({'Loan_id': loan.id}, status=status.HTTP_201_CREATED)
        else:
            return Response({'Error': 'Loan application not approved'}, status=status.HTTP_400_BAD_REQUEST)
        
    def calculate_emi_schedule(self, principal, interest_rate, term_period):
        monthly_interest_rate = (interest_rate / 12) / 100.0
        
        n = term_period
        
        emi = (
            principal * monthly_interest_rate * math.pow(1 + monthly_interest_rate, n)
        ) / (math.pow(1 + monthly_interest_rate, n) - 1)
        
        emi_schedule = []
        current_date = self.get_disbursement_date()
        for _ in range(n):
            emi_schedule.append((current_date, emi))
            current_date = self.increment_month(current_date)
        
        return emi_schedule
    
    def get_disbursement_date(self):
        disbursement_date = self.request.data.get('disbursement_date')
        if disbursement_date:
            return date.fromisoformat(disbursement_date)
        else:
            return date.today()
    
    def increment_month(self, date_obj):
        # Implement logic to increment the date by one month
        # return date_obj + relativedelta(months=1)
        pass

    def validate_loan_amount(self, data):
        loan_type = data.get('loan_type')
        loan_amount = data.get('loan_amount')

        if loan_type == 'Car' and loan_amount <= 750000:
            return True
        elif loan_type == 'Home' and loan_amount <= 8500000:
            return True
        elif loan_type == 'Education' and loan_amount <= 5000000:
            return True
        elif loan_type == 'Personal' and loan_amount <= 1000000:
            return True
        else:
            return False

class EMICreateView(generics.CreateAPIView):
    queryset = EMI.objects.all()
    serializer_class = EMISerializer
    
    def create(self, request, *args, **kwargs):
        loan_id = request.data.get('loan_id')
        amount_paid = request.data.get('amount_paid')
        
        try:
            emi = EMI.objects.get(loan_id=loan_id, is_paid=False)
        except EMI.DoesNotExist:
            return Response({'Error': 'EMI not found or already paid'}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount_paid >= emi.amount_due:
            emi.is_paid = True
            emi.save()
            
            remaining_principal = self.calculate_remaining_principal(emi)
            
            if remaining_principal == 0:
                pass
            
            return Response({'Message': 'Payment successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'Error': 'Insufficient payment amount'}, status=status.HTTP_400_BAD_REQUEST)
    
    def calculate_remaining_principal(self, emi):
        loan = emi.loan
        paid_emi_amounts = loan.emi_set.filter(is_paid=True).aggregate(
            total_paid=Sum('amount_due', output_field=DecimalField())
        )['total_paid'] or 0
        
        remaining_principal = loan.loan_amount - paid_emi_amounts
        return remaining_principal

class LoanStatementView(generics.RetrieveAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    lookup_field = 'pk'
    
    def retrieve(self, request, *args, **kwargs):
        loan_id = kwargs.get('pk')
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response({'Error': 'Loan not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        statements = EMI.objects.filter(loan=loan)
        total_paid = statements.filter(is_paid=True).aggregate(
            total_paid=Sum(F('amount_due'), output_field=DecimalField())
        )['total_paid']
        total_due = statements.filter(is_paid=False, due_date__gte=timezone.now()).aggregate(
            total_due=Sum(F('amount_due'), output_field=DecimalField())
        )['total_due']
        
        past_transactions = statements.filter(is_paid=True)
        upcoming_transactions = statements.filter(is_paid=False, due_date__gte=timezone.now())
        
        response_data = {
            'Past_transactions': [{
                'Date': transaction.due_date,
                'Principal': transaction.amount_due,  
                'Interest': transaction.amount_due - transaction.amount_due,  
                'Amount_paid': transaction.amount_due
            } for transaction in past_transactions],
            'Upcoming_transactions': [{
                'Date': transaction.due_date,
                'Amount_due': transaction.amount_due
            } for transaction in upcoming_transactions],
            'Total_paid': total_paid,
            'Total_due': total_due,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)