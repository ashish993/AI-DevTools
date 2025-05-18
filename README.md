# AI DevTools 🛠️

An intelligent developer toolkit that provides various AI-powered features to assist in software development, architecture design, code analysis, and RFP solutions.

## LIVE DEMO: http://47.254.240.28:8501/

## LIVE DEMO: http://47.254.240.28:8501/

## Features

### 1. 🏛️ ArchMaster - Architecture Designer
- Design scalable architectures using Alibaba Cloud services
- Get detailed technical analysis and recommendations
- Generate comprehensive architecture documentation

### 2. 🎨 DiagramGPT - Architecture Visualizer
- Generate visual architecture diagrams
- Support for Alibaba Cloud components
- Export diagrams in PNG format

### 3. 💻 CodeForge - Intelligent Code Generator
- Generate optimized code from requirements
- Support for multiple programming languages
- Best practices implementation

### 4. 🔄 Metamorph - Code Transformer
- Transform and refactor code
- Improve code quality
- Optimize performance

### 5. 🔍 SyntaxSage - Code Analysis
- Get expert code review
- Receive improvement suggestions
- Best practices validation

### 6. 🧪 TestCraft - Test Suite Generator
- Generate comprehensive test cases
- Unit and integration test generation
- Edge case coverage

### 7. 🔒 Security Auditor
- Analyze code for security vulnerabilities
- OWASP compliance checking
- Security best practices recommendations

### 8. 🧠 LogicLens - Git Logic Solver
- Enterprise-level repository analysis
- Code quality assessment
- Security and architecture evaluation

### 9. 📋 RFP Solver - Document Analysis
- Analyze and process RFP documents
- Extract key requirements and specifications
- Generate comprehensive responses
- Use Sample-Template-Document.pdf for trying the internal document analysis feature
- Use questions.xlsx for sample security assessment questions

## Prerequisites

- Python 3.8 or higher
- Graphviz (for diagram generation)
- DashScope API Key (for LLM integration)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI-Hack1
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Install Graphviz:
- **macOS**: `brew install graphviz`
- **Linux**: `sudo apt-get install graphviz`
- **Windows**: Download from [Graphviz Downloads](https://graphviz.org/download/)

5. Create a `.env` file in the project root with your DashScope API key:
```
DASHSCOPE_API_KEY=your_api_key_here
```

## Running the Application

1. Ensure your virtual environment is activated
2. Start the Streamlit application:
```bash
streamlit run src/app.py
```
3. Open your browser and navigate to `http://localhost:8501`

## Project Structure

```
.
├── diagrams/                # Architecture diagram outputs
├── src/                     # Source code
│   ├── app.py              # Main application entry point
│   ├── arch_master.py      # Architecture design module
│   ├── codeforge.py        # Code generation module
│   ├── components.py       # Shared UI components
│   ├── diagramgptemb.py    # Diagram generation module
│   ├── githubrepo.py       # Repository analysis module
│   ├── logic_lens.py       # Code analysis module
│   ├── metamorph.py        # Code transformation module
│   ├── rfp_solver.py       # RFP document analysis module
│   └── securityaudit.py    # Security analysis module
├── static/                  # Static assets
├── templates/              # HTML templates
├── Sample-Template-Document.pdf  # Sample RFP document for testing
├── questions.xlsx          # Security assessment questions
├── requirements.txt        # Python dependencies
└── Dockerfile             # Container definition
```

## Usage

1. **Architecture Design**:
   - Select ArchMaster from the sidebar
   - Enter your business requirements
   - Get detailed architecture recommendations

2. **Diagram Generation**:
   - Choose DiagramGPT
   - Describe your architecture
   - Download the generated diagram

3. **Code Generation**:
   - Select CodeForge
   - Input your requirements
   - Get optimized code output

4. **RFP Analysis**:
   - Choose RFP Solver
   - Upload Sample-Template-Document.pdf or your own RFP document
   - Get detailed analysis and requirement extraction

5. **Security Assessment**:
   - Select Security Auditor
   - Use provided questions.xlsx for assessment framework
   - Get comprehensive security analysis

6. **Code Analysis**:
   - Use LogicLens
   - Enter a GitHub repository URL
   - Receive comprehensive analysis

## Environment Variables

- `DASHSCOPE_API_KEY`: Your DashScope API key for LLM integration

## Docker Support

### Building Locally
Build and run the application using Docker:

```bash
docker build -t ai-devtools .
docker run -p 8501:8501 -e DASHSCOPE_API_KEY=your_key_here ai-devtools
```

### Using Pre-built Image from Docker Hub
The application image is available on Docker Hub and can be used directly:

1. Pull the image:
```bash
docker pull erashishsharma/ai-devtools:latest
```

2. Run the container:
```bash
docker run -p 8501:8501 -e DASHSCOPE_API_KEY=your_key_here erashishsharma/ai-devtools:latest
```

Additional Docker run options:
- `-p 8501:8501`: Maps the container's port to your local machine
- `-e DASHSCOPE_API_KEY=your_key_here`: Sets the required API key
- `-d`: Run in detached mode (optional)
- `-v $(pwd)/data:/app/data`: Mount a local volume for persistent data (optional)

## Security Notes

- Keep your API keys secure and never commit them to version control
- Always review generated code before using in production
- Follow security best practices when deploying
- Use the provided questions.xlsx as a baseline for security assessments
- Regularly update your security assessment criteria

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License
Developed by Ashish Sharma.
