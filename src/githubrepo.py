import streamlit as st
from openai import OpenAI
import os
import requests
from base64 import b64decode
import json
from collections import defaultdict
import re
from typing import Dict, List, Any
import ast
import radon.complexity as radon
from radon.metrics import h_visit
from bandit.core import manager
from bandit.core import config
import subprocess

def get_github_repo_contents(repo_url: str, path: str = "") -> List[Dict[str, Any]]:
    """Fetch contents of a GitHub repository"""
    try:
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        # Make request to GitHub API
        response = requests.get(api_url)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        raise Exception(f"Error fetching repository contents: {str(e)}")

def get_file_content(file_url: str) -> str:
    """Fetch and decode content of a specific file from GitHub"""
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        content = response.json()
        
        if content.get("encoding") == "base64":
            return b64decode(content["content"]).decode('utf-8')
        return ""
        
    except Exception as e:
        return f"Error fetching file content: {str(e)}"

def analyze_code_structure(contents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the repository structure and code organization"""
    structure = defaultdict(int)
    
    for item in contents:
        if item["type"] == "file":
            ext = os.path.splitext(item["name"])[1].lower()
            structure[ext] += 1
            
    return dict(structure)

def analyze_file_content(file_content: str, file_name: str) -> Dict[str, Any]:
    """Analyze individual file content for code quality and vulnerabilities"""
    analysis = {
        "complexity_metrics": {},
        "potential_vulnerabilities": [],
        "code_smells": [],
        "security_issues": []
    }
    
    try:
        # Calculate code complexity metrics
        if file_name.endswith('.py'):
            try:
                # Calculate cyclomatic complexity
                complexity = radon.cc_visit(file_content)
                analysis["complexity_metrics"]["cyclomatic_complexity"] = [
                    {"name": item.name, "complexity": item.complexity}
                    for item in complexity
                ]
                
                # Calculate Halstead metrics
                halstead_metrics = h_visit(file_content)
                analysis["complexity_metrics"]["halstead_metrics"] = {
                    "h1": halstead_metrics.h1,
                    "h2": halstead_metrics.h2,
                    "N1": halstead_metrics.N1,
                    "N2": halstead_metrics.N2
                }
            except:
                analysis["complexity_metrics"] = "Unable to calculate metrics"
        
        # Security vulnerability scanning
        try:
            # Create a temporary file for bandit analysis
            temp_file = f"temp_{os.path.basename(file_name)}"
            with open(temp_file, 'w') as f:
                f.write(file_content)
            
            # Run bandit security analysis
            b_conf = config.BanditConfig()
            b_mgr = manager.BanditManager(b_conf, 'file')
            b_mgr.discover_files([temp_file])
            b_mgr.run_tests()
            
            # Extract security issues
            for issue in b_mgr.get_issue_list():
                analysis["security_issues"].append({
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "description": issue.text,
                    "line_number": issue.line_number
                })
            
            # Cleanup temporary file
            os.remove(temp_file)
        except Exception as e:
            analysis["security_issues"].append(f"Security analysis error: {str(e)}")
        
        # Code smell detection
        try:
            tree = ast.parse(file_content)
            
            # Check for large functions (more than 50 lines)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.end_lineno - node.lineno > 50:
                        analysis["code_smells"].append(f"Large function '{node.name}' ({node.end_lineno - node.lineno} lines)")
                        
            # Check for too many function arguments (more than 5)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.args.args) > 5:
                        analysis["code_smells"].append(f"Too many arguments in function '{node.name}' ({len(node.args.args)} args)")
        except:
            analysis["code_smells"].append("Unable to perform code smell analysis")
            
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis

def analyze_dependencies(contents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze project dependencies and their potential vulnerabilities"""
    dependencies = {
        "python": [],
        "javascript": [],
        "vulnerabilities": []
    }
    
    for item in contents:
        if item["name"] == "requirements.txt":
            try:
                content = get_file_content(item["download_url"])
                dependencies["python"] = [
                    line.strip() for line in content.split('\n')
                    if line.strip() and not line.startswith('#')
                ]
                
                # Check for known vulnerabilities using safety
                try:
                    result = subprocess.run(
                        ["safety", "check"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        dependencies["vulnerabilities"].extend(
                            result.stdout.split('\n')
                        )
                except:
                    dependencies["vulnerabilities"].append(
                        "Unable to check Python package vulnerabilities"
                    )
            except:
                dependencies["python"].append("Error reading requirements.txt")
                
        elif item["name"] == "package.json":
            try:
                content = get_file_content(item["download_url"])
                pkg_json = json.loads(content)
                dependencies["javascript"] = {
                    "dependencies": pkg_json.get("dependencies", {}),
                    "devDependencies": pkg_json.get("devDependencies", {})
                }
                
                # Check for known vulnerabilities using npm audit
                try:
                    result = subprocess.run(
                        ["npm", "audit", "--json"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        audit_result = json.loads(result.stdout)
                        dependencies["vulnerabilities"].extend(
                            [vuln["title"] for vuln in audit_result.get("vulnerabilities", [])]
                        )
                except:
                    dependencies["vulnerabilities"].append(
                        "Unable to check JavaScript package vulnerabilities"
                    )
            except:
                dependencies["javascript"].append("Error reading package.json")
    
    return dependencies

def analyze_repository(repo_url: str) -> None:
    """Perform comprehensive analysis of the GitHub repository"""
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        # Fetch repository contents
        contents = get_github_repo_contents(repo_url)
        
        # Analyze code structure
        structure = analyze_code_structure(contents)
        
        # Analyze dependencies
        dependency_analysis = analyze_dependencies(contents)
        
        # Analyze each file
        file_analyses = {}
        for item in contents:
            if item["type"] == "file" and item["name"].endswith(('.py', '.js', '.ts', '.java')):
                content = get_file_content(item["download_url"])
                file_analyses[item["name"]] = analyze_file_content(content, item["name"])
        
        # Prepare repository analysis prompt
        analysis_prompt = f"""Analyze the following GitHub repository and provide a comprehensive enterprise-level analysis:

Repository URL: {repo_url}
File Structure: {json.dumps(structure, indent=2)}
Dependencies: {json.dumps(dependency_analysis, indent=2)}
File-Level Analysis: {json.dumps(file_analyses, indent=2)}

Please provide a detailed analysis with the following sections:

1. Project Overview
   - Purpose and main features
   - Technology stack analysis
   - Architecture overview
   - Project structure assessment

2. Code Quality Analysis
   - Code organization and modularity
   - Coding standards compliance
   - Design patterns used
   - Technical debt assessment
   - Maintainability index
   - Code complexity metrics
   - Individual file analysis and metrics

3. Security Assessment
   - Security vulnerabilities (per file)
   - Authentication and authorization
   - Data protection measures
   - API security (if applicable)
   - Dependency security analysis
   - OWASP Top 10 compliance
   - Known CVEs in dependencies

4. Performance Analysis
   - Resource utilization
   - Scalability considerations
   - Caching strategies
   - Database optimization (if applicable)
   - Network efficiency

5. Best Practices Review
   - Industry standard compliance
   - Documentation quality
   - Testing coverage
   - CI/CD implementation
   - Error handling
   - Logging and monitoring

6. File-Level Details
   - Per-file complexity analysis
   - Security issues found
   - Code smells detected
   - Improvement recommendations

7. Recommendations
   - High-priority improvements
   - Security enhancements
   - Performance optimizations
   - Architecture improvements
   - Best practices implementation

8. Risk Assessment
   - Technical risks
   - Security risks
   - Scalability risks
   - Maintenance risks
   - Dependencies risks

Format the analysis in a clear, structured manner with detailed explanations and actionable insights."""

        # Generate analysis using Qwen LLM
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software architect and code analyst. Provide thorough analysis with actionable insights."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            temperature=0.7,
            max_tokens=5000,
            top_p=1,
            stream=True
        )
        
        return completion
        
    except Exception as e:
        raise Exception(f"Error analyzing repository: {str(e)}")

def render_repository_analysis(repo_url: str) -> None:
    """Render the repository analysis interface and results"""
    try:
        if not repo_url or not repo_url.startswith("https://github.com/"):
            st.error("Please provide a valid GitHub repository URL")
            return
            
        completion = analyze_repository(repo_url)
        
        # Create expanding sections for the analysis
        with st.expander("🔍 Repository Analysis Report", expanded=True):
            report_container = st.empty()
            full_report = ""
            
            try:
                for chunk in completion:
                    if hasattr(chunk.choices[0], 'delta'):
                        content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else ""
                    else:
                        content = chunk.choices[0].text if hasattr(chunk.choices[0], 'text') else ""
                    
                    if content:
                        full_report += content
                        report_container.markdown(full_report)
                
            except Exception as e:
                st.error(f"Error processing analysis response: {str(e)}")
                
    except Exception as e:
        st.error(f"An error occurred during repository analysis: {str(e)}")