import streamlit as st
from openai import OpenAI 
import os

def analyze_security_vulnerabilities(code_input):
    """
    Analyze code for security vulnerabilities using Qwen LLM
    Returns a detailed security audit report similar to SonarQube
    """
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        prompt = f"""Perform a comprehensive security audit of the following code:

{code_input}

Please analyze and provide a detailed report with the following sections:

1. Critical Vulnerabilities
   - Description of each vulnerability
   - Impact assessment
   - CVSS score (if applicable)
   - Remediation steps

2. Code Quality & Security Issues
   - Security code smells
   - Potentially insecure patterns
   - Secure coding best practices violations
   - Technical debt assessment

3. Security Best Practices Review
   - Authentication & Authorization
   - Data validation and sanitization
   - Error handling and logging
   - Secure configuration

4. Dependencies & Third-Party Components
   - Known vulnerabilities in dependencies
   - Version analysis
   - Supply chain security concerns

5. Compliance & Standards
   - OWASP Top 10 violations
   - Compliance issues (if applicable)
   - Industry standard violations

6. Performance & Security Trade-offs
   - Security impact on performance
   - Resource management concerns
   - Scalability implications

7. Remediation Plan
   - Prioritized list of fixes
   - Code examples for critical fixes
   - Security improvement recommendations

Format the report in a clear, structured manner with severity levels and clear action items."""

        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are an expert security auditor with deep knowledge of secure coding practices, vulnerabilities, and security standards. Provide thorough security analysis with actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True
        )
        
        return completion
        
    except Exception as e:
        raise Exception(f"Error performing security audit: {str(e)}")

def render_security_audit(code_input):
    """Render the security audit interface and results"""
    try:
        if not code_input.strip():
            st.error("Please provide code to analyze for security vulnerabilities")
            return
            
        completion = analyze_security_vulnerabilities(code_input)
        
        # Create an expanding report container
        with st.expander("🔒 Security Audit Report", expanded=True):
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
                st.error(f"Error processing security audit response: {str(e)}")
                
    except Exception as e:
        st.error(f"An error occurred during security audit: {str(e)}")