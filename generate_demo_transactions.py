#!/usr/bin/env python3
"""
Demo script to generate random transactions with sanctions entities
"""

from transaction_generator import TransactionGenerator
from database import AMLDatabase

def main():
    print("🚀 Generating demo transactions with random sanctions entities...")
    
    # Initialize database and generator
    db = AMLDatabase()
    generator = TransactionGenerator(db)
    
    # Generate a batch of mixed transactions
    print("\n📦 Generating mixed batch (50 transactions)...")
    transactions = generator.generate_mixed_batch(50)
    
    # Store them
    stored_count = generator.store_transactions(transactions)
    print(f"✅ Stored {stored_count} transactions")
    
    # Show some interesting examples
    print("\n🎯 Sample positive alert transactions (sanctions matches):")
    sanctions_transactions = [t for t in transactions if 'sanctions_entity' in t.get('risk_factors', [])]
    for i, txn in enumerate(sanctions_transactions[:10]):
        print(f"  {i+1}. {txn['beneficiary_name']}: ${txn['amount']:,.2f} → {txn['beneficiary_country']}")
    
    print("\n📄 Sample normal transactions:")
    normal_transactions = [t for t in transactions if not t.get('risk_factors', [])]
    for i, txn in enumerate(normal_transactions[:10]):
        print(f"  {i+1}. {txn['beneficiary_name']}: ${txn['amount']:,.2f} → {txn['beneficiary_country']}")
    
    # Show database stats
    stats = db.get_statistics()
    print(f"\n📊 Updated database statistics:")
    print(f"   Total transactions: {stats['total_transactions']}")
    print(f"   Active alerts: {stats['active_alerts']}")
    print(f"   Sanctions matches: {stats['alert_typologies'].get('R1_SANCTIONS_MATCH', 0)}")

if __name__ == "__main__":
    main()