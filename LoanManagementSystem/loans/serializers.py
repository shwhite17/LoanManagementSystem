from django.core.exceptions import ValidationError
from django import serializers
from .models import UserProfile, Loan, EMI

def validate_principal(value):
    if value < 10000:
        raise ValidationError('Principal Amount Cannot be less than 10000')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('username', 'password', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = Loan.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('annual_income', 'credit_score')

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('unique_user_id', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date')

class EMISerializer(serializers.ModelSerializer):
    class Meta:
        model = EMI
        fields = ('due_date', 'amount_due', 'is_paid')

class ApproveOrRejectLoanSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=12)

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

class EditLoanSerializer(serializers.Serializer):
    principal = serializers.FloatField(default=10000, validators=[validate_principal])
    interest_rate = serializers.FloatField(default=14)
    term_period = serializers.IntegerField(default=12)
    loan_amount = serializers.FloatField(default=0)
    disbursement_date = serializers.DateTimeField()
    status = serializers.CharField(max_length=12)

    def update(self, instance, validated_data):
        instance.principal = validated_data.get('principal', instance.principal)
        instance.interest_rate = validated_data.get('interest_rate', instance.interest_rate)
        instance.term_period = validated_data.get('term_period', instance.term_period)
        instance.loan_amount = validated_data.get('loan_amount', instance.loan_amount)
        instance.disbursement_date = validated_data.get('disbursement_date', instance.disbursement_date)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
