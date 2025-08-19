# AML Alert Dashboard

🛡️ **Real-time Anti-Money Laundering Detection Results Dashboard**

A modern, responsive web dashboard for visualizing AML alerts and compliance monitoring results from our Azure-based AML Agentic Platform.

## 🌟 Features

- **Real-time Alert Visualization** - Live display of AML detection results
- **Interactive Charts** - Risk distribution and typology breakdown
- **Responsive Design** - Mobile-friendly interface
- **Live Status Indicators** - Real-time system status monitoring
- **Detailed Evidence View** - Complete alert context and evidence

## 🚀 Live Dashboard

**[View Live Dashboard →](https://aml-dashboard.vercel.app)**

## 📊 Current Test Results

The dashboard displays results from our end-to-end AML platform test:

- **3 Active Alerts** detected across multiple typologies
- **1 Critical Risk** sanctions match (99% confidence)
- **1 High Risk** structuring pattern (80% confidence)  
- **1 Medium Risk** geography transaction (70% confidence)

## 🏗️ Architecture

Built on our comprehensive AML Agentic Platform:
- **Azure Data Lake Storage** - Raw data ingestion
- **Databricks** - Data processing and ML
- **Delta Live Tables** - Real-time streaming
- **Master Orchestrator** - AI task planning
- **MCP Servers** - Specialized agents

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **Hosting**: Vercel (Production), Python HTTP Server (Development)
- **Data**: JSON API endpoints
- **Styling**: Modern CSS Grid/Flexbox

## 📱 Screenshots

### Desktop View
![Dashboard Desktop](dashboard-desktop.png)

### Mobile View  
![Dashboard Mobile](dashboard-mobile.png)

## 🔧 Local Development

```bash
# Clone the repository
git clone https://github.com/aml-platform/dashboard
cd dashboard

# Start local server
python3 -m http.server 8080

# Or use the custom server with API
python3 server.py

# Open in browser
open http://localhost:8080
```

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Azure Static Web Apps
```bash
# Deploy to Azure
az staticwebapp create \
  --name aml-dashboard \
  --source . \
  --location "East US 2"
```

## 📈 Data Sources

The dashboard connects to multiple data sources:

1. **Alert Data**: `test_results_alerts.json` - Live AML alerts
2. **Metrics API**: Real-time system metrics
3. **Azure Storage**: Historical data and logs

## 🔒 Security

- **No sensitive data** exposed in frontend code
- **CORS enabled** for cross-origin requests
- **HTTPS enforced** in production
- **Data sanitization** for all user inputs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- 📧 Email: support@aml-platform.com
- 📞 Phone: +1-800-AML-HELP
- 💬 Slack: #aml-platform-support

---

**Built with ❤️ by the AML Platform Team**