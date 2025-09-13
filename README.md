# SmartDocFlow - Intelligent Document Processing & Analysis Platform

## 🚀 Project Overview

SmartDocFlow is an innovative document processing platform that leverages TiDB Serverless with vector search capabilities to create intelligent, multi-step workflows for document analysis and automation.

### Key Features
- **Multi-format Document Processing**: PDFs, images, text files
- **Vector-based Similarity Search**: Find similar documents using embeddings
- **AI-powered Content Analysis**: Extract insights and generate summaries
- **Automated Workflow Orchestration**: Chain multiple AI operations
- **External API Integration**: Slack notifications, calendar events
- **Real-time Processing**: Streamlined document-to-insight pipeline

## 🏗️ Architecture

```
Document Upload → Text Extraction → Vector Embeddings → TiDB Storage
                                                           ↓
External Actions ← LLM Analysis ← Similarity Search ← Query Processing
```

## 🛠️ Technology Stack

- **Backend**: Python FastAPI
- **Database**: TiDB Serverless (with vector search)
- **AI/ML**: OpenAI GPT-4, sentence-transformers
- **Document Processing**: PyPDF2, Pillow, pytesseract
- **External APIs**: Slack, Google Calendar
- **Frontend**: React with TypeScript
- **Deployment**: Docker, Vercel

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- TiDB Cloud account
- OpenAI API key
- Slack workspace (for notifications)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd smartdocflow
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
TIDB_HOST=your-tidb-host
TIDB_PORT=4000
TIDB_USER=your-username
TIDB_PASSWORD=your-password
TIDB_DATABASE=smartdocflow
OPENAI_API_KEY=your-openai-key
SLACK_BOT_TOKEN=your-slack-token
SLACK_CHANNEL_ID=your-channel-id
GOOGLE_CALENDAR_CREDENTIALS=path-to-credentials.json
```

### 3. Install Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

### 4. Initialize Database
```bash
python scripts/init_database.py
```

### 5. Run the Application
```bash
# Start backend server
python main.py

# Start frontend (in another terminal)
cd frontend
npm start
```

## 📖 Usage

1. **Upload Documents**: Drag and drop PDFs, images, or text files
2. **Automatic Processing**: Documents are processed and indexed automatically
3. **Search & Analyze**: Use vector search to find similar documents
4. **AI Insights**: Get AI-generated summaries and insights
5. **Automated Actions**: Receive notifications and calendar events

## 🏆 Challenge Requirements Met

✅ **TiDB Serverless Integration**: Vector search and full-text search  
✅ **Multi-step Agentic Workflow**: Document processing pipeline  
✅ **LLM Integration**: OpenAI GPT-4 for analysis  
✅ **External API Integration**: Slack notifications, Google Calendar  
✅ **Automated Flow**: End-to-end document processing  

## 📁 Project Structure

```
smartdocflow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── scripts/
│   └── main.py
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/
├── tests/
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🎯 Demo Video

[Link to demonstration video will be added]

## 📞 Support

For questions or support, please open an issue in the repository.

