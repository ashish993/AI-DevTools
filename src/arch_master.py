import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_alicloud_response(requirement):
    """Generate a detailed analysis and solution using Alibaba Cloud services"""
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    
    prompt = f"""Analyze the following requirement and provide a detailed solution using Alibaba Cloud services:

{requirement}

Please structure your response in the following format:

1. Problem Analysis:
   - Break down the key requirements
   - Identify technical challenges
   - List business objectives

2. Technical Solution:
   - Detailed architecture overview
   - Key Alibaba Cloud services to be used
   - Service configurations and specifications
   - Integration points
   - Security considerations
   - Scalability approach
   - Disaster recovery strategy

3. Implementation Recommendations:
   - Deployment phases
   - Best practices
   - Cost optimization suggestions
   - Monitoring and maintenance guidelines"""

    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True
        )
        
        return completion
        
    except Exception as e:
        raise Exception(f"Error generating architecture analysis: {str(e)}")

def process_llm_response(response_stream):
    """Process streaming response from Qwen"""
    response_container = st.empty()
    full_response = ""
    
    try:
        for chunk in response_stream:
            if hasattr(chunk.choices[0], 'delta'):
                content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else ""
            else:
                content = chunk.choices[0].text if hasattr(chunk.choices[0], 'text') else ""
            
            if content:
                full_response += content
                response_container.markdown(full_response)
        
        return full_response
    except Exception as e:
        st.error(f"Error processing response: {str(e)}")
        return ""

def render_architecture_solution(requirement):
    """Render the complete architecture solution with analysis"""
    try:
        # Generate the analysis and solution
        with st.spinner("Analyzing requirements and generating solution..."):
            completion = generate_alicloud_response(requirement)
            
            # Create container for the analysis
            with st.container():
                st.subheader("Solution Analysis")
                process_llm_response(completion)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")