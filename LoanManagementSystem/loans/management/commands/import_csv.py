# loans/management/commands/import_csv.py
import csv
from django.core.management.base import BaseCommand
from loans.models import Transaction

class Command(BaseCommand):
    help = 'Import data from CSV file'

    def handle(self, *args, **kwargs):
        with open('transactions_data Backend.csv', 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                Transaction.objects.create(
                    aadhar_id=row['AADHAR ID'],
                    date=row['Date'],
                    amount=row['Amount'],
                    transaction_type=row['Transaction_type']
                )
