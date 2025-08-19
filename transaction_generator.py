#!/usr/bin/env python3
"""
Dynamic transaction generator for AML testing
Creates realistic transaction patterns with embedded risks
"""

import random
import datetime
from faker import Faker
from typing import Dict, List
import uuid
from database import AMLDatabase

class TransactionGenerator:
    def __init__(self, db: AMLDatabase):
        self.db = db
        self.fake = Faker()
        
        # High-risk countries and corridors
        self.high_risk_countries = ['IR', 'RU', 'KP', 'SY', 'AF', 'IQ', 'LY', 'SO', 'YE']
        self.offshore_countries = ['KY', 'BVI', 'CH', 'LU', 'LI', 'MC', 'AD']
        self.high_risk_corridors = {
            ('US', 'IR'): 0.85,
            ('US', 'RU'): 0.80,
            ('US', 'KP'): 0.95,
            ('DE', 'RU'): 0.75,
            ('GB', 'RU'): 0.70,
            ('US', 'KY'): 0.60,
            ('US', 'BVI'): 0.65
        }
        
        # Transaction types and purposes
        self.transaction_types = ['WIRE', 'ACH', 'SWIFT', 'CASH_DEPOSIT', 'CHECK_DEPOSIT']
        self.purposes = [
            'Trade finance', 'Investment', 'Property purchase', 'Business payment',
            'Consulting fees', 'Equipment purchase', 'Service payment', 'Loan repayment',
            'Family support', 'Salary', 'Dividend payment', 'Insurance claim',
            'Legal fees', 'Medical expenses', 'Education fees', 'Charitable donation'
        ]
        
        # Banks by country
        self.banks = {
            'US': ['CHASE_NYC', 'WELLS_FARGO', 'BOA_NY', 'CITI_NYC'],
            'GB': ['HSBC_LONDON', 'BARCLAYS_UK', 'LLOYDS_LONDON'],
            'DE': ['DEUTSCHE_BANK', 'COMMERZBANK', 'DZ_BANK'],
            'IR': ['BANK_TEHRAN', 'IRAN_EXPORT_BANK', 'PARSIAN_BANK'],
            'RU': ['SBERBANK_MOSCOW', 'VTB_BANK', 'GAZPROMBANK'],
            'KY': ['CAYMAN_TRUST', 'CAYMAN_NATIONAL'],
            'BVI': ['OFFSHORE_TRUST', 'BVI_INTERNATIONAL']
        }
    
    def generate_account_id(self) -> str:
        """Generate realistic account ID"""
        return f"ACC-{random.randint(10000, 99999)}"
    
    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN-{str(uuid.uuid4())[:8].upper()}"
    
    def generate_normal_transaction(self) -> Dict:
        """Generate a normal, low-risk transaction"""
        origin_country = random.choice(['US', 'GB', 'DE', 'FR', 'CA'])
        dest_country = random.choice(['US', 'GB', 'DE', 'FR', 'CA', 'AU', 'JP'])
        
        return {
            'transaction_id': self.generate_transaction_id(),
            'account_id': self.generate_account_id(),
            'amount': round(random.uniform(1000, 50000), 2),
            'currency': 'USD',
            'transaction_type': random.choice(['WIRE', 'ACH']),
            'transaction_date': self.fake.date_between(start_date='-30d', end_date='today'),
            'beneficiary_account': self.generate_account_id(),
            'beneficiary_name': self.fake.name(),
            'beneficiary_bank': random.choice(self.banks.get(dest_country, ['UNKNOWN_BANK'])),
            'beneficiary_country': dest_country,
            'origin_country': origin_country,
            'purpose': random.choice(self.purposes),
            'risk_factors': []
        }
    
    def generate_sanctions_risk_transaction(self) -> Dict:
        """Generate transaction involving sanctioned entity"""
        # Get a sanctioned name from database
        sanctions = self.db.get_sanctions_by_name("Vladimir")  # Try to get real sanctions data
        
        if sanctions:
            sanctioned_name = sanctions[0]['name']
            sanctioned_country = sanctions[0]['country'].split(',')[0] if sanctions[0]['country'] else 'RU'
        else:
            # Fallback to known sanctioned names
            sanctioned_names = ['Vladimir Petrov', 'Dmitri Kozlov', 'Hassan Bin Rashid', 'Anna Volkov']
            sanctioned_name = random.choice(sanctioned_names)
            sanctioned_country = 'RU' if 'Vladimir' in sanctioned_name or 'Dmitri' in sanctioned_name or 'Anna' in sanctioned_name else 'IR'
        
        return {
            'transaction_id': self.generate_transaction_id(),
            'account_id': self.generate_account_id(),
            'amount': round(random.uniform(25000, 500000), 2),
            'currency': 'USD',
            'transaction_type': 'SWIFT',
            'transaction_date': self.fake.date_between(start_date='-7d', end_date='today'),
            'beneficiary_account': self.generate_account_id(),
            'beneficiary_name': sanctioned_name,
            'beneficiary_bank': random.choice(self.banks.get(sanctioned_country, ['UNKNOWN_BANK'])),
            'beneficiary_country': sanctioned_country,
            'origin_country': 'US',
            'purpose': random.choice(['Trade finance', 'Investment', 'Business payment']),
            'risk_factors': ['sanctions_entity']
        }
    
    def generate_structuring_pattern(self, count: int = 4) -> List[Dict]:
        """Generate structuring pattern (multiple small transactions)"""
        transactions = []
        account_id = self.generate_account_id()
        date = self.fake.date_between(start_date='-3d', end_date='today')
        
        total_amount = random.uniform(15000, 35000)
        amounts = self._split_amount(total_amount, count, max_individual=9900)
        
        for i, amount in enumerate(amounts):
            transaction = {
                'transaction_id': self.generate_transaction_id(),
                'account_id': account_id,
                'amount': round(amount, 2),
                'currency': 'USD',
                'transaction_type': random.choice(['WIRE', 'CASH_DEPOSIT']),
                'transaction_date': date,
                'beneficiary_account': f"ACC-{random.randint(10000, 99999)}",
                'beneficiary_name': self.fake.name(),
                'beneficiary_bank': random.choice(['FIRST_NATIONAL', 'COMMUNITY_BANK', 'LOCAL_CREDIT_UNION']),
                'beneficiary_country': 'US',
                'origin_country': 'US',
                'purpose': random.choice(['Service payment', 'Equipment purchase', 'Consulting fees']),
                'risk_factors': ['structuring_pattern']
            }
            transactions.append(transaction)
        
        return transactions
    
    def generate_high_risk_geography_transaction(self) -> Dict:
        """Generate high-risk geography transaction"""
        corridor = random.choice(list(self.high_risk_corridors.keys()))
        origin, destination = corridor
        
        return {
            'transaction_id': self.generate_transaction_id(),
            'account_id': self.generate_account_id(),
            'amount': round(random.uniform(50000, 1000000), 2),
            'currency': 'USD',
            'transaction_type': 'SWIFT',
            'transaction_date': self.fake.date_between(start_date='-14d', end_date='today'),
            'beneficiary_account': self.generate_account_id(),
            'beneficiary_name': self.fake.name(),
            'beneficiary_bank': random.choice(self.banks.get(destination, ['UNKNOWN_BANK'])),
            'beneficiary_country': destination,
            'origin_country': origin,
            'purpose': random.choice(['Energy contract', 'Trade finance', 'Equipment purchase']),
            'risk_factors': ['high_risk_geography']
        }
    
    def generate_velocity_anomaly_pattern(self) -> List[Dict]:
        """Generate high-velocity transaction pattern"""
        transactions = []
        account_id = self.generate_account_id()
        base_date = self.fake.date_between(start_date='-2d', end_date='today')
        
        # Generate 8-12 transactions in short time period
        count = random.randint(8, 12)
        
        for i in range(count):
            # Vary date slightly (same day or next day)
            transaction_date = base_date + datetime.timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 59)
            )
            
            transaction = {
                'transaction_id': self.generate_transaction_id(),
                'account_id': account_id,
                'amount': round(random.uniform(5000, 75000), 2),
                'currency': 'USD',
                'transaction_type': random.choice(['WIRE', 'ACH']),
                'transaction_date': transaction_date.date() if hasattr(transaction_date, 'date') else transaction_date,
                'beneficiary_account': self.generate_account_id(),
                'beneficiary_name': self.fake.name(),
                'beneficiary_bank': random.choice(['VARIOUS_BANK', 'MULTIPLE_BANKS']),
                'beneficiary_country': random.choice(['US', 'GB', 'DE', 'FR']),
                'origin_country': 'US',
                'purpose': random.choice(['Business payment', 'Investment', 'Trade settlement']),
                'risk_factors': ['velocity_anomaly']
            }
            transactions.append(transaction)
        
        return transactions
    
    def generate_round_trip_pattern(self) -> List[Dict]:
        """Generate round-trip transaction pattern"""
        account_a = self.generate_account_id()
        account_b = self.generate_account_id()
        amount = round(random.uniform(100000, 500000), 2)
        date1 = self.fake.date_between(start_date='-5d', end_date='-2d')
        date2 = date1 + datetime.timedelta(days=random.randint(1, 3))
        
        # Outbound transaction
        outbound = {
            'transaction_id': self.generate_transaction_id(),
            'account_id': account_a,
            'amount': amount,
            'currency': 'USD',
            'transaction_type': 'WIRE',
            'transaction_date': date1,
            'beneficiary_account': account_b,
            'beneficiary_name': self.fake.name(),
            'beneficiary_bank': random.choice(self.banks.get('KY', ['OFFSHORE_BANK'])),
            'beneficiary_country': 'KY',
            'origin_country': 'US',
            'purpose': 'Investment',
            'risk_factors': ['round_trip_out']
        }
        
        # Return transaction (slightly less due to fees)
        return_amount = amount * 0.98  # 2% fee
        inbound = {
            'transaction_id': self.generate_transaction_id(),
            'account_id': account_b,
            'amount': round(return_amount, 2),
            'currency': 'USD',
            'transaction_type': 'WIRE',
            'transaction_date': date2,
            'beneficiary_account': account_a,
            'beneficiary_name': self.fake.name(),
            'beneficiary_bank': 'FIRST_NATIONAL',
            'beneficiary_country': 'US',
            'origin_country': 'KY',
            'purpose': 'Investment return',
            'risk_factors': ['round_trip_in']
        }
        
        return [outbound, inbound]
    
    def generate_mixed_batch(self, total_count: int = 50) -> List[Dict]:
        """Generate a mixed batch of transactions with various risk levels"""
        transactions = []
        
        # Distribution of transaction types
        normal_count = int(total_count * 0.60)      # 60% normal
        sanctions_count = int(total_count * 0.08)    # 8% sanctions risk
        geography_count = int(total_count * 0.15)    # 15% geography risk
        
        # Generate normal transactions
        for _ in range(normal_count):
            transactions.append(self.generate_normal_transaction())
        
        # Generate sanctions risk transactions
        for _ in range(sanctions_count):
            transactions.append(self.generate_sanctions_risk_transaction())
        
        # Generate geography risk transactions
        for _ in range(geography_count):
            transactions.append(self.generate_high_risk_geography_transaction())
        
        # Add special patterns
        transactions.extend(self.generate_structuring_pattern(4))
        transactions.extend(self.generate_velocity_anomaly_pattern()[:6])
        transactions.extend(self.generate_round_trip_pattern())
        
        # Randomize order
        random.shuffle(transactions)
        return transactions[:total_count]
    
    def _split_amount(self, total: float, parts: int, max_individual: float = 9900) -> List[float]:
        """Split total amount into parts under the threshold"""
        amounts = []
        remaining = total
        
        for i in range(parts - 1):
            max_this_part = min(max_individual, remaining - (max_individual * (parts - i - 1)))
            amount = random.uniform(max_this_part * 0.7, max_this_part)
            amounts.append(amount)
            remaining -= amount
        
        # Last amount gets the remainder (ensure it's under threshold)
        amounts.append(min(remaining, max_individual))
        
        return amounts
    
    def store_transactions(self, transactions: List[Dict]) -> int:
        """Store generated transactions in database"""
        stored_count = 0
        for transaction in transactions:
            # Remove risk_factors before storing
            transaction_data = {k: v for k, v in transaction.items() if k != 'risk_factors'}
            
            if self.db.add_transaction(transaction_data):
                stored_count += 1
        
        return stored_count

if __name__ == "__main__":
    # Test transaction generation
    db = AMLDatabase()
    generator = TransactionGenerator(db)
    
    print("🚀 Generating sample transactions...")
    
    # Generate and store transactions
    transactions = generator.generate_mixed_batch(30)
    stored_count = generator.store_transactions(transactions)
    
    print(f"✅ Generated and stored {stored_count} transactions")
    
    # Show some examples
    print("\n📊 Sample transactions:")
    for i, txn in enumerate(transactions[:5]):
        risk_factors = txn.get('risk_factors', [])
        risk_info = f" (Risk: {', '.join(risk_factors)})" if risk_factors else ""
        print(f"  {i+1}. {txn['beneficiary_name']}: ${txn['amount']:,.2f} to {txn['beneficiary_country']}{risk_info}")
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\n📈 Database statistics: {stats}")