#!/usr/bin/env python3
"""
Test script for pending transaction processing with Plane.so integration
"""

import requests
import json
from datetime import datetime
import time

def test_pending_transaction_processing():
    """Test the complete pending transaction processing workflow"""
    
    base_url = "http://localhost:5000"  # Adjust for your environment
    
    print("🧪 Testing Pending Transaction Processing with Plane.so Integration")
    print("=" * 70)
    
    # Step 1: Create test transactions with high-risk scenarios
    print("\n1️⃣ Creating test transactions...")
    
    test_transactions = [
        # Sanctions match scenario
        {
            "transaction_id": f"TXN-SANCTIONS-{int(time.time())}",
            "account_id": "ACC-TEST-001",
            "amount": 75000,
            "currency": "USD",
            "sender_name": "Test Company Inc",
            "beneficiary_name": "Kim Jong Un",  # Should trigger sanctions match
            "sender_country": "US",
            "beneficiary_country": "KP",
            "sender_account": "1234567890",
            "beneficiary_account": "9876543210",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "WIRE_TRANSFER",
            "status": "PENDING"
        },
        # High-risk geography scenario  
        {
            "transaction_id": f"TXN-GEOGRAPHY-{int(time.time())}",
            "account_id": "ACC-TEST-002", 
            "amount": 125000,
            "currency": "USD",
            "sender_name": "Normal Business Ltd",
            "beneficiary_name": "Suspicious Entity Corp",
            "sender_country": "US",
            "beneficiary_country": "RU",  # High-risk corridor
            "sender_account": "1111111111",
            "beneficiary_account": "2222222222",
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "WIRE_TRANSFER",
            "status": "PENDING"
        },
        # Normal transaction
        {
            "transaction_id": f"TXN-NORMAL-{int(time.time())}",
            "account_id": "ACC-TEST-003",
            "amount": 5000,
            "currency": "USD", 
            "sender_name": "John Smith",
            "beneficiary_name": "Jane Doe",
            "sender_country": "US",
            "beneficiary_country": "CA",
            "sender_account": "3333333333",
            "beneficiary_account": "4444444444", 
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "WIRE_TRANSFER",
            "status": "PENDING"
        }
    ]
    
    created_transactions = []
    for tx_data in test_transactions:
        try:
            response = requests.post(f"{base_url}/api/transactions", json=tx_data)
            if response.status_code in [200, 201]:
                result = response.json()
                created_transactions.append(tx_data['transaction_id'])
                print(f"  ✅ Created {tx_data['transaction_id']}")
            else:
                print(f"  ❌ Failed to create {tx_data['transaction_id']}: {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating transaction: {e}")
    
    if not created_transactions:
        print("❌ No transactions created - cannot proceed with test")
        return False
    
    print(f"✅ Created {len(created_transactions)} test transactions")
    
    # Step 2: Check current pending transactions
    print("\n2️⃣ Checking pending transactions...")
    try:
        response = requests.get(f"{base_url}/api/transactions?status=PENDING")
        if response.status_code == 200:
            data = response.json()
            pending_count = len([tx for tx in data.get('transactions', []) if tx.get('status') == 'PENDING'])
            print(f"  📊 Found {pending_count} pending transactions")
        else:
            print(f"  ⚠️ Could not check pending transactions: {response.text}")
    except Exception as e:
        print(f"  ❌ Error checking pending transactions: {e}")
    
    # Step 3: Process pending transactions
    print("\n3️⃣ Processing pending transactions through AML engine...")
    try:
        response = requests.post(f"{base_url}/api/transactions/process")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Processing completed successfully")
            print(f"  📊 Processed: {result.get('processed_count', 0)} transactions")
            print(f"  ✅ Completed: {result['results'].get('completed', 0)}")
            print(f"  ⚠️ Under Review: {result['results'].get('under_review', 0)}")
            print(f"  ❌ Failed: {result['results'].get('failed', 0)}")
            
            # Check Plane.so integration
            plane_info = result.get('plane_integration', {})
            if plane_info.get('configured'):
                print(f"  🎯 Plane.so items created: {plane_info.get('items_created', 0)}")
                print(f"  🏢 Workspace: {plane_info.get('workspace', 'Unknown')}")
            else:
                print(f"  ⚠️ Plane.so integration not configured")
            
            # Show processing details
            details = result.get('processing_details', [])
            if details:
                print(f"\n  📋 Processing Details:")
                for detail in details:
                    status_icon = "✅" if detail['status'] == 'COMPLETED' else "⚠️" if detail['status'] == 'UNDER_REVIEW' else "❌"
                    plane_info = f" (Plane: {detail['plane_work_item']})" if detail['plane_work_item'] else ""
                    print(f"    {status_icon} {detail['transaction_id']}: {detail['status']} - {detail['alerts_generated']} alerts{plane_info}")
            
            return True
            
        else:
            print(f"  ❌ Processing failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing transactions: {e}")
        return False
    
    # Step 4: Verify results
    print("\n4️⃣ Verifying processing results...")
    try:
        response = requests.get(f"{base_url}/api/statistics")
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"  📊 Active alerts: {stats.get('active_alerts', 0)}")
            print(f"  📊 Total transactions: {stats.get('total_transactions', 0)}")
        
        # Check alerts
        response = requests.get(f"{base_url}/api/alerts")
        if response.status_code == 200:
            alerts = response.json()['alerts']
            recent_alerts = [a for a in alerts if any(tx_id in a.get('subject_id', '') for tx_id in created_transactions)]
            print(f"  🚨 New alerts generated: {len(recent_alerts)}")
            
            for alert in recent_alerts[:3]:  # Show first 3
                print(f"    • {alert.get('alert_id')}: {alert.get('typology')} (Risk: {alert.get('risk_score', 0):.0%})")
                
    except Exception as e:
        print(f"  ⚠️ Error verifying results: {e}")

def test_plane_integration():
    """Test Plane.so integration independently"""
    print("\n🎯 Testing Plane.so Integration")
    print("=" * 40)
    
    try:
        from plane_integration import PlaneIntegration
        
        plane = PlaneIntegration()
        
        if not plane.is_configured():
            print("❌ Plane.so integration not configured")
            print("Required environment variables:")
            print("  - PLANE_API_KEY")
            print("  - PLANE_WORKSPACE_SLUG") 
            print("  - PLANE_PROJECT_KEY")
            return False
        
        print(f"✅ Plane.so configured:")
        print(f"  🏢 Workspace: {plane.workspace_slug}")
        print(f"  📋 Project: {plane.project_key}")
        
        # Test work item creation
        test_transaction = {
            "transaction_id": f"TXN-PLANE-TEST-{int(time.time())}",
            "amount": 100000,
            "currency": "USD",
            "sender_name": "Test Sender",
            "beneficiary_name": "Test Beneficiary", 
            "sender_country": "US",
            "beneficiary_country": "IR",
            "transaction_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        result = plane.create_work_item(
            title="🧪 AML Test Work Item",
            description="This is a test work item created by the AML system test script",
            transaction_data=test_transaction,
            priority="medium"
        )
        
        if result and result.get('success'):
            print(f"✅ Test work item created successfully")
            print(f"  🆔 Work Item ID: {result['work_item_id']}")
            print(f"  🔗 URL: {result['work_item_url']}")
            return True
        else:
            print("❌ Failed to create test work item")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Plane.so integration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AML Pending Transaction Processing Test Suite")
    print("=" * 60)
    
    # Test Plane.so integration first
    plane_success = test_plane_integration()
    
    # Test complete workflow
    workflow_success = test_pending_transaction_processing()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Plane.so Integration: {'✅ PASS' if plane_success else '❌ FAIL'}")
    print(f"  Workflow Processing: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    
    if plane_success and workflow_success:
        print("\n🎉 All tests passed! Pending transaction processing is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check configuration and try again.")
    
    print("\n💡 Next steps:")
    print("  1. Test on localhost by running the Flask app")
    print("  2. Create pending transactions via the dashboard")
    print("  3. Click 'Process Pending Transactions' button")
    print("  4. Check Plane.so workspace for created work items")