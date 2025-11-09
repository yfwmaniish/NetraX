# 🕵️ H4$HCR4CK$ Dark Web Intelligence System
Made by [@Vectorindia1](https://github.com/Vectorindia1) & [@yfwmaniish](https://github.com/yfwmaniish)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/Status-Active-green.svg)](#)

> **Advanced Dark Web Intelligence & Leak Detection System with AI-Powered Analysis**

An enterprise-grade cybersecurity tool that combines web crawling, artificial intelligence, and advanced data analysis to detect, classify, and assess data leaks across dark web platforms. Built for cybersecurity professionals, researchers, and threat intelligence teams.

## 🎯 Key Features

### 🧠 AI-Powered Analysis
- **Google Gemini Integration**: Advanced AI-driven leak detection and classification
- **Intelligent PII Detection**: Automatically identifies Aadhaar numbers, PAN cards, phone numbers, emails, banking information
- **Smart Classification**: Categorizes leaks by type, severity, and potential impact
- **Fuzzy Matching**: AI-powered identifier searches with context awareness

### 🕷️ Advanced Web Crawling
- **Tor Network Support**: Built-in proxy integration for anonymous crawling
- **Intelligent Scraping**: Automated discovery and analysis of dark web content
- **Rate Limiting**: Configurable delays to avoid detection
- **Robust Error Handling**: Continues operation despite network issues

### 📊 Comprehensive Dashboard
- **Real-time Monitoring**: Live view of crawling progress and discoveries
- **Interactive Search**: Multi-parameter search with AI enhancement
- **Statistical Analysis**: Detailed reports on leak patterns and trends
- **Export Capabilities**: JSON, CSV, and Excel export formats

### 🛡️ Security & Privacy
- **Secure Configuration**: Environment-based API key management
- **Data Protection**: Encrypted storage of sensitive information
- **Access Control**: Authentication system for dashboard access
- **Audit Logging**: Comprehensive logging of all operations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Tor Browser or Tor service
- Privoxy proxy server
- Google Gemini API key

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE.git
cd H4_HCR4CK_DARKWEB_INTELLIGENCE
```

2. **Set up the environment:**
```bash
chmod +x setup.sh
./setup.sh
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. **Launch the system:**
```bash
./launcher.sh
```

## 📋 Configuration

### Environment Variables (.env)
```bash
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Dashboard Configuration
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password

# Proxy Configuration
HTTP_PROXY=http://127.0.0.1:8118
HTTPS_PROXY=http://127.0.0.1:8118

# AI Processing Settings
AI_PROCESSING_ENABLED=true
AI_MAX_TEXT_LENGTH=4000
AI_TIMEOUT=30
```

## 🔧 Components

### Core Modules
- **`ai_utils.py`**: Gemini AI integration and processing
- **`crawler/decimal_crawler.py`**: Main web crawling engine
- **`dashboard/decimal_dashboard.py`**: Web interface and API
- **`database/models.py`**: Database schema and operations
- **`ocr_parser.py`**: Document processing and OCR

### AI Capabilities
- **Local Regex Detection**: Fast pattern matching for common PII
- **Gemini Classification**: Context-aware leak assessment
- **Severity Scoring**: Automated risk evaluation
- **Entity Extraction**: Advanced named entity recognition

## 📊 Supported Data Types

### Indian PII Detection
- 🔢 **Aadhaar Numbers**: Complete validation and format checking
- 💳 **PAN Cards**: Permanent Account Number detection
- 📱 **Phone Numbers**: Indian mobile and landline formats
- 🏦 **Banking Information**: Account numbers, IFSC codes
- 🆔 **Government IDs**: Passport, driving license, voter ID

### International Data
- 📧 **Email Addresses**: All standard formats
- 💳 **Credit Cards**: Major card providers
- 🏢 **Corporate Data**: Tax IDs, business registrations
- 🛂 **Travel Documents**: Passport numbers, visa information

## 🎨 Dashboard Features

### Main Interface
- **Real-time Statistics**: Live counters and progress indicators
- **Search & Filter**: Advanced search with AI enhancement
- **Leak Timeline**: Chronological view of discoveries
- **Export Tools**: Multiple format support

### Search Capabilities
- **Identifier Search**: Find leaks by specific PII
- **Category Browsing**: Filter by leak type and severity
- **AI-Enhanced Matching**: Fuzzy search with context understanding
- **Bulk Operations**: Export and analysis of multiple results

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Test AI integration
python3 test_gemini_simple.py

# Full system validation
python3 test_ai_system.py

# Database verification
python3 -c "from database.models import test_database_connection; test_database_connection()"
```

## 📈 Performance & Scalability

- **Concurrent Processing**: Multi-threaded crawling and AI analysis
- **Rate Limiting**: Configurable delays and throttling
- **Memory Management**: Optimized for large-scale operations
- **Database Optimization**: Indexed searches and efficient queries

## 🚨 Legal & Ethical Use

⚠️ **Important Notice**: This tool is designed for legitimate cybersecurity research, threat intelligence, and authorized penetration testing only.

### Authorized Use Cases
- ✅ Security research and vulnerability assessment
- ✅ Threat intelligence gathering
- ✅ Authorized penetration testing
- ✅ Digital forensics investigations
- ✅ Academic research (with proper approvals)

### Prohibited Activities
- ❌ Unauthorized access to systems or data
- ❌ Privacy violations or stalking
- ❌ Commercial data harvesting
- ❌ Any illegal or malicious activities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub Repository**: https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE
- **Documentation**: [Wiki](https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE/wiki)
- **Issues**: [Bug Reports](https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE/issues)

## 💬 Support

For support and questions:
- Open an [issue](https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE/issues)
- Check the [documentation](https://github.com/Vectorindia1/H4_HCR4CK_DARKWEB_INTELLIGENCE/wiki)
- Review the troubleshooting guide

---

**Built with ❤️ by the H4$HCR4CK$ Team**

*Advancing cybersecurity through intelligent automation and AI-powered threat detection.*
