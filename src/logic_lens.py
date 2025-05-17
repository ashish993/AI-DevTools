import streamlit as st
import os
import git
import tempfile
import shutil
from openai import OpenAI
import glob
from pathlib import Path
import base64

def analyze_file(content, filename, extension):
    """Analyze individual file content"""
    file_type_analysis = {
        '.py': {
            'language': 'Python',
            'indicators': {
                'imports': ['import ', 'from '],
                'classes': ['class '],
                'functions': ['def '],
                'async': ['async ', 'await'],
                'decorators': ['@'],
            }
        },
        '.js': {
            'language': 'JavaScript',
            'indicators': {
                'imports': ['import ', 'require('],
                'classes': ['class '],
                'functions': ['function ', '=>'],
                'async': ['async ', 'await'],
                'decorators': ['@'],
            }
        },
        '.ts': {
            'language': 'TypeScript',
            'indicators': {
                'imports': ['import '],
                'interfaces': ['interface '],
                'types': ['type '],
                'classes': ['class '],
                'functions': ['function ', '=>'],
                'async': ['async ', 'await'],
                'decorators': ['@'],
            }
        }
    }
    
    analysis = {
        'filename': filename,
        'extension': extension,
        'size_bytes': len(content),
        'line_count': len(content.splitlines()),
        'empty_lines': len([l for l in content.splitlines() if not l.strip()]),
        'features': {}
    }
    
    # Get language-specific analysis if available
    if extension in file_type_analysis:
        lang_spec = file_type_analysis[extension]
        analysis['language'] = lang_spec['language']
        
        # Count occurrences of each indicator
        for feature, indicators in lang_spec['indicators'].items():
            count = sum(content.count(ind) for ind in indicators)
            analysis['features'][feature] = count
    
    return analysis

def analyze_git_repo(repo_url):
    """Clone and analyze a git repository"""
    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repository
            repo = git.Repo.clone_from(repo_url, temp_dir)
            
            # Get repository info
            repo_info = {
                "branches": [b.name for b in repo.branches],
                "active_branch": repo.active_branch.name,
                "last_commit": {
                    "message": repo.head.commit.message,
                    "author": str(repo.head.commit.author),
                    "date": str(repo.head.commit.authored_datetime)
                },
                "commit_count": sum(1 for _ in repo.iter_commits()),
                "contributors": len(set(c.author.name for c in repo.iter_commits()))
            }
            
            # Read all files recursively
            file_contents = {}
            file_analyses = {}
            ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env'}
            ignore_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.class'}
            
            for filepath in glob.glob(f"{temp_dir}/**/*", recursive=True):
                rel_path = os.path.relpath(filepath, temp_dir)
                
                # Skip ignored directories and files
                if any(d in Path(rel_path).parts for d in ignore_dirs):
                    continue
                    
                extension = os.path.splitext(rel_path)[1]
                if extension in ignore_extensions:
                    continue
                    
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_contents[rel_path] = content
                            # Analyze each file individually
                            file_analyses[rel_path] = analyze_file(content, rel_path, extension)
                    except UnicodeDecodeError:
                        # Skip binary files
                        continue
            
            return analyze_codebase(repo_info, file_contents, file_analyses)
            
        except Exception as e:
            raise Exception(f"Error analyzing repository: {str(e)}")

def analyze_codebase(repo_info, file_contents, file_analyses):
    """Analyze the codebase using Qwen LLM"""
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    
    # Calculate codebase metrics
    total_files = len(file_contents)
    total_lines = sum(analysis['line_count'] for analysis in file_analyses.values())
    language_distribution = {}
    for analysis in file_analyses.values():
        if 'language' in analysis:
            language_distribution[analysis['language']] = language_distribution.get(analysis['language'], 0) + 1
    
    # Prepare repository summary with detailed metrics
    repo_summary = f"""Repository Analysis:
General Statistics:
- Total Files: {total_files}
- Total Lines of Code: {total_lines}
- Total Commits: {repo_info['commit_count']}
- Contributors: {repo_info['contributors']}
- Language Distribution: {', '.join(f'{lang}: {count}' for lang, count in language_distribution.items())}

Branch Info:
- Active Branch: {repo_info['active_branch']}
- Available Branches: {', '.join(repo_info['branches'])}

Latest Commit:
- Message: {repo_info['last_commit']['message']}
- Author: {repo_info['last_commit']['author']}
- Date: {repo_info['last_commit']['date']}

Detailed File Analysis:
{chr(10).join(f'''
File: {analysis['filename']}
- Language: {analysis.get('language', 'Unknown')}
- Lines of Code: {analysis['line_count']} ({analysis['empty_lines']} empty)
- Features: {', '.join(f'{k}: {v}' for k, v in analysis.get('features', {}).items() if v > 0)}
''' for analysis in file_analyses.values())}

File Contents:
{chr(10).join(f"### {path} ###{chr(10)}{content}{chr(10)}" for path, content in file_contents.items())}"""

    prompt = f"""Analyze the following git repository and provide a comprehensive review covering:

1. Repository Overview:
   - Project structure and organization
   - Language distribution and technologies used
   - Code metrics and statistics
   - Development activity indicators

2. Per-File Analysis:
   - Architecture and design patterns used in each file
   - Code quality assessment
   - Function and class organization
   - Dependencies and coupling
   - Potential code smells or anti-patterns

3. Security Analysis:
   - Potential security vulnerabilities
   - Authentication and authorization patterns
   - Data handling and privacy concerns
   - Dependencies security assessment

4. Performance Analysis:
   - Performance bottlenecks
   - Resource utilization patterns
   - Scalability considerations
   - Optimization opportunities

5. Testing & Quality:
   - Test coverage assessment
   - Testing patterns used
   - CI/CD practices
   - Code quality metrics

6. Documentation & Maintainability:
   - Documentation quality
   - Code readability
   - Dependency management
   - Developer onboarding considerations

7. Recommendations:
   - High-priority improvements
   - Architectural enhancements
   - Security improvements
   - Performance optimizations
   - Testing suggestions
   - Documentation improvements

Repository Details:
{repo_summary}"""

    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
            top_p=1,
            stream=True
        )
        
        return completion
        
    except Exception as e:
        raise Exception(f"Error generating analysis: {str(e)}")

def render_logic_lens(repo_url):
    """Render the Git repository analysis interface"""
    try:
        # Show analysis in progress
        with st.spinner("Analyzing repository..."):
            completion = analyze_git_repo(repo_url)
            
            # Create container for the analysis
            with st.container():
                st.subheader("Repository Analysis")
                
                # Process streaming response
                response_container = st.empty()
                full_response = ""
                
                for chunk in completion:
                    if hasattr(chunk.choices[0], 'delta'):
                        content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else ""
                    elif hasattr(chunk.choices[0], 'text'):
                        content = chunk.choices[0].text
                    else:
                        content = ""
                    
                    if content:
                        full_response += content
                        response_container.markdown(full_response)
                
                return full_response
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None