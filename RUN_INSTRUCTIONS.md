# SmartDocFlow - Run Instructions

## 🚀 Quick Start Guide

### Prerequisites

1. **TiDB Cloud Account**
   - Sign up at [TiDB Cloud](https://tidbcloud.com)
   - Create a new cluster
   - Note down your connection details

2. **OpenAI API Key**
   - Get your API key from [OpenAI Platform](https://platform.openai.com)

3. **System Requirements**
   - Python 3.9+
   - Node.js 16+
   - Docker (optional)

### Step 1: Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smartdocflow
   ```

2. **Create environment file**
   ```bash
   cp env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` file with your credentials:
   ```env
   TIDB_HOST=your-tidb-host.tidbcloud.com
   TIDB_PORT=4000
   TIDB_USER=your-username
   TIDB_PASSWORD=your-password
   TIDB_DATABASE=smartdocflow
   OPENAI_API_KEY=your-openai-api-key
   ```

### Step 2: Backend Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database**
   ```bash
   python scripts/init_database.py
   ```

3. **Start backend server**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Step 3: Frontend Setup

1. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start frontend development server**
   ```bash
   npm start
   ```
   The UI will be available at `http://localhost:3000`

### Step 4: Using Docker (Alternative)

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## 📖 Usage Guide

### 1. Upload Documents
- Navigate to the Upload page
- Drag and drop or select files (PDF, TXT, PNG, JPG)
- Documents are automatically processed and indexed

### 2. Search Documents
- Use the Search page to find documents
- Choose between Vector, Full-text, or Hybrid search
- View similarity scores and relevance rankings

### 3. AI Analysis
- Select documents for AI-powered analysis
- Choose analysis type (General, Legal, Financial, Technical)
- Get insights, summaries, and key findings

### 4. Automated Workflows
- Execute multi-step document processing workflows
- Enable notifications and external integrations
- Monitor workflow execution status

## 🔧 Configuration Options

### External Integrations

**Slack Notifications**
```env
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_CHANNEL_ID=your-channel-id
```

**Google Calendar**
```env
GOOGLE_CALENDAR_CREDENTIALS=path-to-credentials.json
```

### Performance Tuning

**Vector Search Settings**
```env
VECTOR_DIMENSION=768
SIMILARITY_THRESHOLD=0.7
```

**File Upload Limits**
```env
MAX_FILE_SIZE=10485760  # 10MB
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify TiDB Cloud credentials
   - Check network connectivity
   - Ensure cluster is running

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check API quota and billing
   - Ensure proper API permissions

3. **Document Processing Fails**
   - Check file format support
   - Verify file size limits
   - Review error logs

### Logs and Debugging

**Backend Logs**
```bash
python main.py --log-level debug
```

**Database Connection Test**
```bash
python scripts/init_database.py
```

## 📊 Monitoring

### Health Checks
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000/health`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔒 Security Notes

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use strong, unique passwords
   - Rotate API keys regularly

2. **File Uploads**
   - Validate file types and sizes
   - Scan for malware (recommended)
   - Implement proper access controls

3. **API Security**
   - Use HTTPS in production
   - Implement rate limiting
   - Add authentication/authorization

## 🚀 Production Deployment

### Recommended Setup

1. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set up reverse proxy (nginx)**
   ```nginx
   location /api/ {
       proxy_pass http://localhost:8000;
   }
   ```

3. **Configure SSL certificates**
   - Use Let's Encrypt or your preferred CA
   - Enable HTTPS redirects

4. **Database optimization**
   - Use connection pooling
   - Monitor query performance
   - Set up backups

## 📞 Support

For issues and questions:
- Check the API documentation
- Review error logs
- Open an issue in the repository

## 🎯 Demo Features

The application demonstrates:
- ✅ TiDB Serverless vector search
- ✅ Multi-step agentic workflows
- ✅ LLM integration (OpenAI GPT-4)
- ✅ External API integrations (Slack, Calendar)
- ✅ Automated document processing pipeline
- ✅ Real-time search and analysis
- ✅ Modern React frontend with TypeScript
- ✅ Docker containerization
- ✅ Comprehensive API documentation


