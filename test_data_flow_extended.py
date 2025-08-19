#!/usr/bin/env python3
"""
Enhanced end-to-end data flow test with comprehensive sample data
Creates realistic AML scenarios with multiple alert types
"""

import json
import csv
import datetime
import re
from collections import defaultdict

def normalize_name(name):
    """Normalize names for comparison"""
    if not name:
        return ""
    return re.sub(r'[^A-Z0-9]', '', name.upper().strip())

def test_extended_data_flow():
    print("🚀 STARTING ENHANCED END-TO-END AML DATA FLOW TEST")
    print("=" * 60)
    
    # Load extended sample data
    print("📂 Loading enhanced sample data...")
    
    with open('sample_data/transactions_extended.json', 'r') as f:
        transactions = json.load(f)
    
    with open('sample_data/parties_extended.json', 'r') as f:
        parties = json.load(f)
    
    # Load extended watchlists
    watchlists = []
    with open('sample_data/watchlists_extended.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            watchlists.append(row)
    
    print(f"📊 Loaded: {len(transactions)} transactions, {len(parties)} parties, {len(watchlists)} watchlist entries")
    
    # SILVER LAYER PROCESSING - Enhanced data cleansing
    print("\n🥈 SILVER LAYER: Enhanced data processing...")
    
    # Process parties with normalization
    parties_silver = []
    party_map = {}
    for party in parties:
        party_clean = party.copy()
        party_clean['name_norm'] = normalize_name(party['name'])
        party_clean['processed_ts'] = datetime.datetime.utcnow().isoformat()
        parties_silver.append(party_clean)
        party_map[party['party_id']] = party_clean
    
    # Process watchlists with normalization
    watchlists_silver = []
    for wl in watchlists:
        wl_clean = wl.copy()
        wl_clean['name_norm'] = normalize_name(wl['name'])
        wl_clean['processed_ts'] = datetime.datetime.utcnow().isoformat()
        watchlists_silver.append(wl_clean)
    
    # Process transactions with enrichment
    transactions_silver = []
    account_activity = defaultdict(list)
    
    for txn in transactions:
        txn_clean = txn.copy()
        txn_clean['processed_ts'] = datetime.datetime.utcnow().isoformat()
        
        # Country risk scoring
        high_risk_countries = ['IR', 'RU', 'KP', 'SY', 'AF']
        if txn_clean.get('beneficiary_country') in high_risk_countries:
            txn_clean['country_risk'] = 'HIGH'
        elif txn_clean.get('beneficiary_country') in ['KY', 'BVI', 'CH']:
            txn_clean['country_risk'] = 'MEDIUM'
        else:
            txn_clean['country_risk'] = 'LOW'
        
        transactions_silver.append(txn_clean)
        account_activity[txn['account_id']].append(txn_clean)
    
    print(f"✅ Silver processing complete: {len(parties_silver)} parties, {len(transactions_silver)} transactions")
    
    # GOLD LAYER - Enhanced AML Rule Engine
    print("\n🥇 GOLD LAYER: Enhanced AML alert generation...")
    
    alerts = []
    alert_counter = 1
    
    # Rule 1: Enhanced Sanctions Screening
    print("🔍 R1: Enhanced Sanctions Screening...")
    sanctions_matches = 0
    for party in parties_silver:
        for wl in watchlists_silver:
            if (wl['source'] == 'OFAC' and 
                (party['name_norm'] == wl['name_norm'] or 
                 (len(party['name_norm']) > 3 and party['name_norm'] in wl['name_norm']))):
                
                alert = {
                    "alert_id": f"ALERT-{alert_counter:04d}",
                    "subject_id": party['party_id'],
                    "typology": "R1_SANCTIONS_MATCH",
                    "risk_score": 0.95 if wl['risk_level'] == 'CRITICAL' else 0.85,
                    "evidence": {
                        "source": wl['source'],
                        "program": wl['program'],
                        "party_name": party['name'],
                        "watchlist_name": wl['name'],
                        "match_type": "exact" if party['name_norm'] == wl['name_norm'] else "fuzzy",
                        "risk_level": wl['risk_level'],
                        "country": party.get('nationality', 'Unknown')
                    },
                    "created_ts": datetime.datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                alert_counter += 1
                sanctions_matches += 1
    
    # Rule 2: Enhanced Structuring Detection
    print("🔍 R2: Enhanced Structuring Detection...")
    structuring_matches = 0
    for account_id, txns in account_activity.items():
        # Group by date
        daily_activity = defaultdict(list)
        for txn in txns:
            date = txn['transaction_date']
            daily_activity[date].append(txn)
        
        for date, day_txns in daily_activity.items():
            if len(day_txns) >= 3:  # Multiple transactions same day
                total_amount = sum(float(t['amount']) for t in day_txns)
                avg_amount = total_amount / len(day_txns)
                
                # Detect structuring patterns
                if (len(day_txns) >= 4 and avg_amount < 10000 and 
                    all(float(t['amount']) < 10000 for t in day_txns)):
                    
                    alert = {
                        "alert_id": f"ALERT-{alert_counter:04d}",
                        "subject_id": account_id,
                        "typology": "R2_STRUCTURING",
                        "risk_score": min(0.9, 0.6 + (len(day_txns) * 0.05)),
                        "evidence": {
                            "transaction_count": len(day_txns),
                            "total_amount": total_amount,
                            "average_amount": avg_amount,
                            "date": date,
                            "pattern": f"{len(day_txns)}_transactions_under_10k"
                        },
                        "created_ts": datetime.datetime.utcnow().isoformat()
                    }
                    alerts.append(alert)
                    alert_counter += 1
                    structuring_matches += 1
    
    # Rule 3: Enhanced High-Risk Geography
    print("🔍 R3: Enhanced High-Risk Geography...")
    geography_matches = 0
    high_risk_corridors = {
        ('US', 'IR'): 0.85,
        ('US', 'RU'): 0.80,
        ('US', 'KP'): 0.95,
        ('US', 'SY'): 0.90,
        ('EU', 'RU'): 0.75,
        ('US', 'KY'): 0.60,
        ('US', 'BVI'): 0.65
    }
    
    for txn in transactions_silver:
        origin = txn.get('origin_country')
        dest = txn.get('beneficiary_country')
        
        if origin and dest:
            corridor = (origin, dest)
            risk_score = high_risk_corridors.get(corridor, 0)
            
            if risk_score > 0 or dest in ['IR', 'RU', 'KP', 'SY']:
                risk_score = risk_score or (0.75 if dest in ['IR', 'RU', 'KP', 'SY'] else 0.50)
                
                alert = {
                    "alert_id": f"ALERT-{alert_counter:04d}",
                    "subject_id": txn['account_id'],
                    "typology": "R3_HIGH_RISK_CORRIDOR",
                    "risk_score": risk_score,
                    "evidence": {
                        "origin_country": origin,
                        "beneficiary_country": dest,
                        "transaction_id": txn['transaction_id'],
                        "amount": float(txn['amount']),
                        "country_risk": txn.get('country_risk', 'UNKNOWN')
                    },
                    "created_ts": datetime.datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                alert_counter += 1
                geography_matches += 1
    
    # Rule 4: Velocity Anomalies
    print("🔍 R4: Velocity Anomaly Detection...")
    velocity_matches = 0
    for account_id, txns in account_activity.items():
        if len(txns) >= 2:
            amounts = [float(t['amount']) for t in txns]
            total_volume = sum(amounts)
            max_amount = max(amounts)
            
            # High volume or unusual activity
            if total_volume > 500000 or max_amount > 200000:
                alert = {
                    "alert_id": f"ALERT-{alert_counter:04d}",
                    "subject_id": account_id,
                    "typology": "R4_VELOCITY_ANOMALY",
                    "risk_score": min(0.85, 0.5 + (total_volume / 1000000) * 0.3),
                    "evidence": {
                        "total_volume": total_volume,
                        "max_single_transaction": max_amount,
                        "transaction_count": len(txns),
                        "time_period": "1_day",
                        "anomaly_type": "high_volume"
                    },
                    "created_ts": datetime.datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                alert_counter += 1
                velocity_matches += 1
    
    # Rule 5: Round-Trip Transactions
    print("🔍 R5: Round-Trip Transaction Detection...")
    roundtrip_matches = 0
    
    # Look for transactions that go out and come back
    outbound_txns = {}
    for txn in transactions_silver:
        if txn.get('beneficiary_account'):
            key = (txn['account_id'], txn.get('beneficiary_account'), float(txn['amount']))
            outbound_txns[key] = txn
    
    for txn in transactions_silver:
        if txn.get('beneficiary_account'):
            # Look for reverse transaction
            reverse_key = (txn.get('beneficiary_account'), txn['account_id'], float(txn['amount']))
            if reverse_key in outbound_txns:
                original_txn = outbound_txns[reverse_key]
                
                alert = {
                    "alert_id": f"ALERT-{alert_counter:04d}",
                    "subject_id": txn['account_id'],
                    "typology": "R5_ROUND_TRIP",
                    "risk_score": 0.70,
                    "evidence": {
                        "outbound_txn": original_txn['transaction_id'],
                        "return_txn": txn['transaction_id'],
                        "amount": float(txn['amount']),
                        "pattern": "round_trip_detected"
                    },
                    "created_ts": datetime.datetime.utcnow().isoformat()
                }
                alerts.append(alert)
                alert_counter += 1
                roundtrip_matches += 1
    
    # Display Results
    print(f"\n📊 ENHANCED AML DETECTION RESULTS:")
    print(f"   🎯 Sanctions matches: {sanctions_matches}")
    print(f"   🎯 Structuring patterns: {structuring_matches}")
    print(f"   🎯 Geography risks: {geography_matches}")
    print(f"   🎯 Velocity anomalies: {velocity_matches}")
    print(f"   🎯 Round-trip transactions: {roundtrip_matches}")
    print(f"   📈 TOTAL ALERTS: {len(alerts)}")
    
    # Sort alerts by risk score (highest first)
    alerts.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Save enhanced results
    with open('test_results_alerts_extended.json', 'w') as f:
        json.dump(alerts, f, indent=2)
    
    # Display top alerts
    print(f"\n🚨 TOP PRIORITY ALERTS:")
    for i, alert in enumerate(alerts[:10], 1):
        risk_pct = int(alert['risk_score'] * 100)
        print(f"   {i:2d}. {alert['alert_id']}: {alert['typology']} ({risk_pct}% risk)")
        if alert['typology'] == 'R1_SANCTIONS_MATCH':
            print(f"       👤 Subject: {alert['evidence']['party_name']}")
            print(f"       🎯 Match: {alert['evidence']['source']} {alert['evidence']['program']}")
        elif alert['typology'] == 'R2_STRUCTURING':
            print(f"       💰 {alert['evidence']['transaction_count']} transactions, ${alert['evidence']['total_amount']:,.0f}")
        elif alert['typology'] == 'R3_HIGH_RISK_CORRIDOR':
            print(f"       🌍 {alert['evidence']['origin_country']} → {alert['evidence']['beneficiary_country']} (${alert['evidence']['amount']:,.0f})")
        elif alert['typology'] == 'R4_VELOCITY_ANOMALY':
            print(f"       📈 Volume: ${alert['evidence']['total_volume']:,.0f} in {alert['evidence']['transaction_count']} transactions")
        elif alert['typology'] == 'R5_ROUND_TRIP':
            print(f"       🔄 Round-trip: ${alert['evidence']['amount']:,.0f}")
    
    print(f"\n✅ Enhanced results saved to: test_results_alerts_extended.json")
    print(f"🎉 ENHANCED END-TO-END TEST COMPLETED SUCCESSFULLY!")
    print(f"📊 Generated {len(alerts)} alerts across 5 typologies")

if __name__ == "__main__":
    test_extended_data_flow()