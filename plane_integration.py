#!/usr/bin/env python3
"""
Plane.so API Integration for AML Manual Intervention Cases
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PlaneIntegration:
    def __init__(self):
        self.api_key = os.getenv('PLANE_API_KEY')
        self.workspace_slug = os.getenv('PLANE_WORKSPACE_SLUG', 'amlops')
        self.project_key = os.getenv('PLANE_PROJECT_KEY', 'AMLOPS')
        self.base_url = "https://api.plane.so"
        
        if not self.api_key:
            print("⚠️ PLANE_API_KEY not configured - manual intervention features disabled")
        
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Plane.so integration is properly configured"""
        return bool(self.api_key and self.workspace_slug and self.project_key)
    
    def create_work_item(self, 
                        title: str, 
                        description: str, 
                        transaction_data: Dict,
                        alert_data: List[Dict] = None,
                        priority: str = "medium") -> Optional[Dict]:
        """
        Create a work item in Plane.so for manual AML intervention
        
        Args:
            title: Work item title
            description: Detailed description
            transaction_data: Transaction requiring manual review
            alert_data: Associated AML alerts
            priority: Priority level (low, medium, high, urgent)
        
        Returns:
            Dict with work item details or None if failed
        """
        if not self.is_configured():
            print("⚠️ Plane.so not configured - cannot create work item")
            return None
        
        try:
            # Prepare work item payload
            priority_map = {
                "low": "low",
                "medium": "medium", 
                "high": "high",
                "urgent": "urgent"
            }
            
            # Create rich description with transaction details
            rich_description = self._format_description(description, transaction_data, alert_data)
            
            payload = {
                "name": title,
                "description": rich_description,
                "priority": priority_map.get(priority, "medium"),
                "labels": ["aml", "manual-review", "compliance"],
                "state": "todo",  # Initial state
                "project": self.project_key,
                "assignee": None,  # Will be assigned by compliance team
            }
            
            # Add transaction-specific labels
            if transaction_data:
                amount = transaction_data.get('amount', 0)
                if amount > 100000:
                    payload["labels"].append("high-value")
                if transaction_data.get('beneficiary_country') in ['RU', 'IR', 'KP', 'SY']:
                    payload["labels"].append("high-risk-country")
            
            # Create work item via Plane API
            url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_key}/issues/"
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                work_item = response.json()
                print(f"✅ Created Plane work item: {work_item.get('id', 'Unknown')}")
                return {
                    "success": True,
                    "work_item_id": work_item.get("id"),
                    "work_item_url": f"https://app.plane.so/{self.workspace_slug}/projects/{self.project_key}/issues/{work_item.get('id')}",
                    "title": title,
                    "priority": priority,
                    "created_at": datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to create Plane work item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Plane work item: {e}")
            return None
    
    def _format_description(self, description: str, transaction_data: Dict, alert_data: List[Dict] = None) -> str:
        """Format rich description for work item"""
        
        formatted = f"""# AML Manual Intervention Required

## Issue Description
{description}

## Transaction Details
**Transaction ID**: {transaction_data.get('transaction_id', 'N/A')}
**Amount**: ${transaction_data.get('amount', 0):,.2f} {transaction_data.get('currency', 'USD')}
**Date**: {transaction_data.get('transaction_date', 'N/A')}

**Parties**:
- **Sender**: {transaction_data.get('sender_name', 'N/A')} ({transaction_data.get('sender_country', 'N/A')})
- **Beneficiary**: {transaction_data.get('beneficiary_name', 'N/A')} ({transaction_data.get('beneficiary_country', 'N/A')})

**Account Details**:
- **Sender Account**: {transaction_data.get('sender_account', 'N/A')}
- **Beneficiary Account**: {transaction_data.get('beneficiary_account', 'N/A')}
"""

        # Add alert information if available
        if alert_data:
            formatted += "\n## AML Alerts Generated\n"
            for i, alert in enumerate(alert_data, 1):
                risk_score = alert.get('risk_score', 0)
                risk_percent = f"{risk_score:.0%}" if risk_score else "Unknown"
                
                formatted += f"""
### Alert {i}: {alert.get('typology', 'Unknown')}
- **Risk Score**: {risk_percent}
- **Alert ID**: {alert.get('alert_id', 'N/A')}
- **Evidence**: {alert.get('evidence', {}).get('summary', 'See full alert details')}
"""

        # Add action items
        formatted += """
## Required Actions
- [ ] Review transaction details and parties
- [ ] Verify beneficial ownership information
- [ ] Check additional documentation if required
- [ ] Determine if transaction should be:
  - [ ] Approved and processed
  - [ ] Rejected and reported
  - [ ] Escalated for further investigation

## Compliance Notes
*Please document your analysis and decision rationale in the comments.*

---
*This work item was automatically created by the AML Detection System.*
"""
        
        return formatted
    
    def create_sanctions_match_item(self, transaction_data: Dict, sanctions_match: Dict) -> Optional[Dict]:
        """Create work item specifically for sanctions matches"""
        
        title = f"🚨 SANCTIONS MATCH: {transaction_data.get('beneficiary_name', 'Unknown Party')}"
        
        description = f"""High-priority sanctions screening match detected requiring immediate compliance review.

**Matched Entity**: {sanctions_match.get('name', 'Unknown')}
**Match Confidence**: {sanctions_match.get('match_confidence', 0):.0%}
**Sanctions Program**: {sanctions_match.get('program', 'Unknown')}
**Data Source**: {sanctions_match.get('data_source', 'Unknown')}
"""
        
        return self.create_work_item(
            title=title,
            description=description,
            transaction_data=transaction_data,
            priority="urgent"
        )
    
    def create_high_risk_geography_item(self, transaction_data: Dict, risk_details: Dict) -> Optional[Dict]:
        """Create work item for high-risk geography transactions"""
        
        origin = transaction_data.get('sender_country', 'Unknown')
        destination = transaction_data.get('beneficiary_country', 'Unknown') 
        
        title = f"🌍 HIGH-RISK CORRIDOR: {origin} → {destination}"
        
        description = f"""Transaction involving high-risk geographic corridor requires compliance review.

**Risk Level**: {risk_details.get('country_risk', 'Unknown')}
**Corridor Risk Score**: {risk_details.get('corridor_risk_score', 0):.0%}
**Transaction Value**: ${transaction_data.get('amount', 0):,.2f}
"""
        
        return self.create_work_item(
            title=title,
            description=description,
            transaction_data=transaction_data,
            priority="high"
        )
    
    def create_structuring_pattern_item(self, transaction_data: Dict, pattern_details: Dict) -> Optional[Dict]:
        """Create work item for structuring patterns"""
        
        title = f"💰 STRUCTURING PATTERN: {pattern_details.get('transaction_count', 0)} transactions"
        
        description = f"""Potential structuring pattern detected requiring investigation.

**Pattern**: {pattern_details.get('pattern', 'Unknown')}
**Total Amount**: ${pattern_details.get('total_amount', 0):,.2f}
**Transaction Count**: {pattern_details.get('transaction_count', 0)}
**Time Period**: {pattern_details.get('date', 'Unknown')}
"""
        
        return self.create_work_item(
            title=title,
            description=description,
            transaction_data=transaction_data,
            priority="high"
        )
    
    def get_work_item_status(self, work_item_id: str) -> Optional[Dict]:
        """Get current status of a work item"""
        if not self.is_configured():
            return None
        
        try:
            url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_key}/issues/{work_item_id}/"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get work item status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting work item status: {e}")
            return None

# Example usage and testing
if __name__ == "__main__":
    # Test Plane.so integration
    plane = PlaneIntegration()
    
    if not plane.is_configured():
        print("❌ Plane.so integration not configured")
        print("Required environment variables:")
        print("- PLANE_API_KEY")
        print("- PLANE_WORKSPACE_SLUG")
        print("- PLANE_PROJECT_KEY")
    else:
        print("✅ Plane.so integration configured")
        print(f"Workspace: {plane.workspace_slug}")
        print(f"Project: {plane.project_key}")
        
        # Test work item creation
        test_transaction = {
            "transaction_id": "TXN-TEST-001",
            "amount": 150000,
            "currency": "USD",
            "sender_name": "Test Company Inc",
            "beneficiary_name": "Suspicious Entity Ltd",
            "sender_country": "US", 
            "beneficiary_country": "RU",
            "transaction_date": "2025-08-21"
        }
        
        test_alert = [{
            "alert_id": "ALERT-TEST-001",
            "typology": "R1_SANCTIONS_MATCH",
            "risk_score": 0.95,
            "evidence": {"summary": "High confidence sanctions match detected"}
        }]
        
        result = plane.create_work_item(
            title="Test AML Manual Intervention",
            description="This is a test work item for AML manual intervention workflow",
            transaction_data=test_transaction,
            alert_data=test_alert,
            priority="medium"
        )
        
        if result:
            print(f"✅ Test work item created: {result['work_item_url']}")
        else:
            print("❌ Failed to create test work item")