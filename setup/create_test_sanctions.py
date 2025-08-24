#!/usr/bin/env python3
"""
Create test transactions with sanctioned entities
"""

from transaction_generator import TransactionGenerator
from database import AMLDatabase

def main():
    db = AMLDatabase()
    generator = TransactionGenerator(db)

    print('🚀 Creating 3 transactions with sanctioned entities...')

    # Generate only sanctions risk transactions
    transactions = []
    for i in range(3):
        tx = generator.generate_sanctions_risk_transaction()
        transactions.append(tx)
        print(f'  Transaction {i+1}: {tx["beneficiary_name"]} -> {tx["beneficiary_country"]} (${tx["amount"]:.2f})')

    # Store them
    stored_count = generator.store_transactions(transactions)
    print(f'✅ Stored {stored_count} new transactions')
    
    return stored_count

if __name__ == "__main__":
    main()