# Intelligent Task Routing System - Frontend

Angular 17 frontend application for the Intelligent Task Routing System. This application provides an admin portal, task analysis interface, and chat assistant for optimal task-to-resource assignment using AI.

## Features

### Admin Portal (Phase 7)
- **Resource Management**: View and manage human resources and AI agents
- **Project Management**: Create and track projects
- **Task Management**: Define and monitor tasks
- **Knowledge Base**: Upload documents, policies, SOPs for RAG
- **Expert Analysis**: Capture expert knowledge and historical insights
- **SLA Rules**: Define and manage service level agreements
- **Cost Models**: Configure cost models for resources

### Task Analysis UI (Phase 8)
- **Document Upload**: Upload project documents (PDF, DOCX, TXT)
- **Task Extraction**: AI-powered extraction of tasks from documents
- **Resource Recommendations**: View optimal resource assignments with:
  - Skill match scores
  - Workload distribution
  - Cost analysis
  - SLA compliance
  - Risk assessment
- **Visualizations**: Charts for workload, cost, skill matching, SLA risk

### Chat Assistant (Phase 9)
- **Conversational Interface**: Ask questions about routing decisions
- **Context-Aware**: Maintains analysis context
- **Voice Support**: Speech-to-text and text-to-speech
- **OCR Integration**: Extract text from images
- **MCP Tool Invocation**: Direct access to MCP server tools

## Tech Stack

- **Framework**: Angular 17
- **UI**: Angular Material / Custom CSS
- **Charts**: Chart.js / ngx-charts
- **HTTP**: HttpClient with JWT interceptor
- **Routing**: Angular Router with auth guards
- **State**: RxJS / Services

## Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:5004

## Setup

### 1. Install Dependencies

```bash
# Run setup script
setup.bat

# Or manually
npm install
```

### 2. Configure Environment

The proxy configuration (`proxy.conf.json`) is already set to target backend on port 5004.

### 3. Start Development Server

```bash
# Run start script
start.bat

# Or manually
npm start
```

Access the application at: **http://localhost:4204**

## Project Structure

```
src/
├── app/
│   ├── admin/              # Admin portal components
│   │   ├── dashboard/      # Main admin dashboard
│   │   ├── resources/      # Resource management
│   │   ├── projects/       # Project management
│   │   ├── tasks/          # Task management
│   │   ├── knowledge-base/ # Document upload & RAG
│   │   ├── expert-analysis/# Expert knowledge capture
│   │   ├── sla-rules/      # SLA configuration
│   │   └── cost-models/    # Cost model management
│   ├── analysis/           # Task analysis components
│   │   ├── upload/         # Document upload
│   │   ├── results/        # Analysis results display
│   │   ├── task-detail/    # Task detail modal
│   │   └── charts/         # Visualization components
│   ├── chat/               # Chat assistant components
│   │   ├── interface/      # Chat UI
│   │   ├── voice/          # Voice input/output
│   │   └── ocr/            # Image upload for OCR
│   ├── login/              # Authentication
│   ├── services/           # Shared services
│   │   ├── auth.service.ts
│   │   ├── api.service.ts
│   │   ├── task-routing.service.ts
│   │   └── chat.service.ts
│   ├── guards/             # Route guards
│   │   └── auth.guard.ts
│   └── models/             # TypeScript interfaces
└── environments/           # Environment configs
```

## Key Services

### AuthService
Handles user authentication with JWT tokens:
- `login(username, password)`
- `logout()`
- `isAuthenticated()`
- `getToken()`

### ApiService
Core HTTP service with interceptor for JWT:
- Automatic token injection
- Error handling
- Base URL configuration

### TaskRoutingService
Interacts with task routing API:
- `analyzeDocument(file)` - Upload and analyze document
- `getAnalysisResults(id)` - Retrieve analysis results
- `getResources()` - Fetch available resources
- `getProjects()` - Fetch projects
- `uploadKnowledge(file, category)` - Upload to knowledge base

### ChatService
Manages chat conversations:
- `startSession()` - Initialize chat
- `sendMessage(message)` - Send chat message
- `getHistory()` - Retrieve chat history
- `speechToText(audio)` - Convert speech to text
- `textToSpeech(text)` - Convert text to speech

## API Endpoints

All endpoints are proxied through `/api`:

- `POST /api/auth/login` - User login
- `POST /api/task-routing/analyze` - Analyze document
- `GET /api/task-routing/results/:id` - Get analysis results
- `GET /api/admin/resources` - List resources
- `POST /api/admin/resources` - Create resource
- `GET /api/admin/projects` - List projects
- `POST /api/knowledge/upload` - Upload document to knowledge base
- `POST /api/chat/start` - Start chat session
- `POST /api/chat/message` - Send chat message
- `POST /api/ocr/extract` - Extract text from image
- `POST /api/voice/speech-to-text` - Convert speech to text

## Authentication

The application uses JWT authentication:

1. Login via `/login` route
2. JWT token stored in localStorage
3. Auth guard protects all routes except `/login`
4. Token automatically injected in API requests
5. Automatic redirect to login on 401 responses

## Default Credentials

```
Username: admin
Password: admin123
```

## Development

### Run Development Server
```bash
npm start
# or
ng serve --port 4204
```

### Build for Production
```bash
npm run build
# Output in dist/
```

### Run Tests
```bash
npm test
```

## Troubleshooting

### Backend Not Responding
- Verify backend is running on http://localhost:5004
- Check `proxy.conf.json` configuration
- Restart Angular dev server

### Authentication Errors
- Clear localStorage and login again
- Check JWT token expiration
- Verify backend auth endpoints

### CORS Issues
- Ensure proxy.conf.json is configured
- Backend should have CORS enabled for port 4204

## Next Steps

1. **Install Dependencies**: Run `setup.bat`
2. **Start Backend**: Ensure backend is running on port 5004
3. **Start Frontend**: Run `start.bat`
4. **Login**: Use admin/admin123
5. **Upload Knowledge**: Add documents to knowledge base
6. **Analyze Tasks**: Upload project document for analysis
7. **Review Results**: View recommendations and metrics
8. **Use Chat**: Ask questions about routing decisions

## Implementation Progress

- ✅ Project Setup and Configuration
- ✅ Authentication System (Login, Auth Guard, Services)
- ✅ Admin Portal Structure
- 🔄 Task Analysis UI (In Progress)
- 🔄 Chat Assistant (In Progress)
- ⏳ Voice and OCR Integration (Planned)

## License

TCS Internal Project
