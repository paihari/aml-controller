# Sample Data Archive

This directory contains sample/demo data files used for testing and development of the AML Controller.

## 📄 **Files Overview**

### **👥 Sample Entity Data**
- `accounts.json` - Sample bank account records
- `parties.json` - Basic party/entity data for testing
- `parties_extended.json` - Extended party data with additional fields

### **💳 Sample Transaction Data**  
- `transactions.json` - Basic transaction records for testing
- `transactions_extended.json` - Extended transaction data with risk factors

### **🚨 Sample Watchlist Data**
- `watchlists.csv` - Basic watchlist/sanctions data
- `watchlists_extended.csv` - Extended watchlist with more entities

### **📊 Data Model**
- `model.json` - OpenSanctions data model schema definition

## 🎯 **Purpose**

These files are used for:
- **Development testing** - Quick data for local development
- **Demo purposes** - Sample data for demonstrations
- **API testing** - Test data for endpoint validation
- **Data format reference** - Examples of expected data structures

## 🔧 **Usage**

### **For Development**
```bash
# Use sample data for local testing
python3 -c "
import json
with open('sample_data_archive/transactions.json') as f:
    sample_transactions = json.load(f)
print(f'Loaded {len(sample_transactions)} sample transactions')
"
```

### **For API Testing**
```bash
# Test API with sample transaction data
curl -X POST http://localhost:5001/api/transactions \
  -H "Content-Type: application/json" \
  -d @sample_data_archive/transactions.json
```

## ⚠️ **Important Notes**

- This data is **for testing only** - not real financial data
- Files are **not required** for normal AML Controller operation  
- The main application uses **live Supabase data**, not these files
- Sample data may be outdated - use for structure reference only

## 📁 **File Formats**

- **JSON files**: Structured data for API testing
- **CSV files**: Tabular data for bulk operations
- **Extended files**: Include additional fields for comprehensive testing