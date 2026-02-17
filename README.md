# TalentScout AI Hiring Assistant

## Project Overview
TalentScout AI is an intelligent hiring assistant designed to streamline the initial candidate screening process. It combines advanced natural language processing with automated document analysis to conduct interviews, extract candidate profiles, and generate relevant technical assessments.

The system consists of two primary components:
1. **Backend**: A FastAPI-based REST API that manages conversation state, processes LLM requests using Groq and LangChain, and parses resumes and job descriptions.
2. **Frontend**: A Streamlit-based web interface providing session management, chat capabilities, and document upload features.

## Installation Instructions

### Prerequisites
- Python 3.12 or higher
- Groq API Key
- Git

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd antigravity
   ```

2. **Configure Environment**
   Create a `.env` file in the `backend/` directory:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

3. **Install Dependencies**
   It is recommended to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

## Usage Guide

### Starting the Application
1. **Run the Backend**:
   ```bash
   cd backend
   python main.py
   ```
   The API will be available at http://localhost:8000.

2. **Run the Frontend**:
   ```bash
   cd frontend
   streamlit run app.py
   ```
   Access the web interface at http://localhost:8501.

### Features
- **Intelligent Screening**: The assistant leads a conversation to collect candidate names, contact details, experience, and tech stacks.
- **Document Parsing**: Upload resumes or job descriptions in PDF, DOCX, or TXT format for automated analysis.
- **Technical Assessments**: Automated generation of relevant technical questions based on the candidate's declared expertise.

### Firebase Setup
The application uses Firebase for user authentication. To set this up:

1. **Create a Firebase Project**: Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2. **Enable Authentication**: In the "Build" menu, select "Authentication" and enable the "Email/Password" sign-in provider.
3. **Get Web API Key**: Navigate to "Project Settings" > "General". Copy the "Web API Key" and paste it into `frontend/auth.py` as the `FIREBASE_API_KEY` value.
4. **Generate Service Account Key**: 
   - Navigate to "Project Settings" > "Service accounts".
   - Click "Generate new private key".
   - Save the downloaded JSON file into the `frontend/` directory.
   - Update `_CRED_PATH` in `frontend/auth.py` to match your filename.

## Docker Deployment

The project is optimized to run as a **single unified container** for easy deployment.

### Prerequisites
- Docker installed on your system.

### Build and Run
1. **Build the Image**:
   ```bash
   docker build -t talentscout-app .
   ```

2. **Run the Container**:
   Pass your Groq API key and any other relevant env variables:
   ```bash
   docker run -p 8080:8080 \
     -e GROQ_API_KEY=your_key_here \
     talentscout-app
   ```

The container uses Nginx to serve everything on a **single port**:
- **Application UI**: http://localhost:8080/
- **Backend API**: http://localhost:8080/api/
- **API Docs**: http://localhost:8080/api/docs

### Pushing to Docker Hub

To share your image on Docker Hub:

1. **Login to Docker Hub**:
   ```bash
   docker login
   ```

2. **Tag the Image**:
   Replace `yourusername` with your actual Docker Hub username:
   ```bash
   docker tag talentscout-app yourusername/talentscout-app:latest
   ```

3. **Push the Image**:
   ```bash
   docker push yourusername/talentscout-app:latest
   ```

> [!TIP]
> After pushing, others can run your app with a single command:
> `docker run -p 8501:8501 -p 8000:8000 -e GROQ_API_KEY=your_key yourusername/talentscout-app:latest`

> [!NOTE]
> For development with live-reloading, you can mount the code:
> `docker run -p 8501:8501 -p 8000:8000 -v $(pwd):/app talentscout-app`

## Cloud Deployment (Docker)

The app is optimized for **single-port cloud deployment** using an internal Nginx reverse proxy. This is required for platforms like Render, Railway, or Fly.io.

### Deployment Steps (e.g., Render)

1. **Connect GitHub**: Push your code to a GitHub repository.
2. **New Web Service**: Select `Docker` as the runtime.
3. **Environment Variables**:
   - `GROQ_API_KEY`: `your_actual_key`
   - `ENVIRONMENT`: `production` (enables correct API routing)
4. **Deploy**: Render will build the image and bind to the dynamic `$PORT`.

> [!IMPORTANT]
> Ensure the Firebase Service Account JSON file (`talentscout-jb-475c123a5377.json`) is in the `frontend/` folder when pushing to GitHub, or use secrets to inject it.

## Technical Details

### Architecture
The application follows a client-server architecture:
- **FastAPI**: Provides high-performance endpoints for chat and parsing logic.
- **LangChain**: Orchestrates the interaction between the prompt templates and the LLM.
- **Groq Llama 3.3 70B**: Serves as the primary inference engine for high-speed, high-quality reasoning.
- **Streamlit**: Delivers a responsive, reactive frontend experience.

### Model Details
The system utilizes the `llama-3.3-70b-versatile` model hosted on Groq, selected for its balance between reasoning capability and low latency, which is essential for real-time conversational agents.

## Prompt Design
Prompts are engineered as modular templates within `hiring_prompts.py`:
- **Information Extraction**: Designed to return strictly structured JSON from natural language inputs.
- **Question Generation**: Crafts intermediate to advanced technical questions tailored to specific tools mentioned by the candidate.
- **Contextual Response**: Uses conversation history and state data to provide natural, non-repetitive feedback.

## Challenges & Solutions

### Virtual Environment Relocation
**Challenge**: Renaming project directories caused hardcoded paths in the virtual environment's bin folder to break, leading to "command not found" errors for tools like Streamlit.
**Solution**: Implemented a recursive search-and-replace script to update all internal path references within the `venv/bin/` directory, restoring environment integrity.

### Consistent JSON Parsing from LLMs
**Challenge**: LLM responses sometimes included markdown markers (e.g., ```json) that caused parsing failures.
**Solution**: Developed a robust wrapper in the backend to strip markdown formatting before JSON deserialization.

## Code Quality
- **Modularity**: Logic is separated into conversation management, prompt templates, and document loading.
- **Clean Code**: Adheres to a minimal comment policy where the code structure and type hints drive readability.
- **Error Handling**: Comprehensive try-except blocks in API endpoints ensure stability and clear error messages.
