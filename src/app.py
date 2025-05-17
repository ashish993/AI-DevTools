"""
This module provides the main Streamlit application interface.
"""
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (must be before any potential usage)
load_dotenv()

# Configure Streamlit page (must be first Streamlit command)
st.set_page_config(
    page_title="AI DevTools",
    page_icon="🛠️",
    layout="wide"
)

from arch_master import render_architecture_solution
from codeforge import render_code_generation, add_custom_css
from metamorph import render_code_transformation
from diagramgptemb import execute_diagram_code, generate_diagram_prompt, clean_and_fix_code
from securityaudit import render_security_audit
from githubrepo import render_repository_analysis

# Add custom CSS after page config
add_custom_css()

# Define development tools
tools = {
    "archMaster": {
        "icon": "classical_building",  # Changed from "sitemap" to "building"
        "title": "ArchMaster - Architecture Designer",
        "description": "Design scalable architectures using Alibaba Cloud services with detailed analysis",
        "prompt": "Please describe your business requirements or problem statement. I'll help design a solution using Alibaba Cloud services with detailed technical analysis."
    },
    "diagramGPT": {
        "icon": "art",
        "title": "DiagramGPT - Architecture Visualizer",
        "description": "Generate visual architecture diagrams using Alibaba Cloud components",
        "prompt": "Describe the architecture you want to visualize using Alibaba Cloud services."
    },
    "codeForge": {
        "icon": "computer",  # Changed from "code" to "computer"
        "title": "CodeForge - Intelligent Code Generator",
        "description": "Generate optimized code from requirements",
        "prompt": "Ready to generate code. What would you like to create?"
    },
    "metamorph": {
        "icon": "repeat",  # Using "repeat" as Streamlit equivalent for fa-random
        "title": "Metamorph - Code Transformer",
        "description": "Transform and refactor code",
        "prompt": "I can help transform your code. What needs refactoring?"
    },
    
    "syntaxSage": {
        "icon": "mag",  # Changed from "magnifying-glass" to "mag"
        "title": "SyntaxSage - Code Analysis",
        "description": "Get expert code review and improvement suggestions",
        "prompt": "Please provide the code you'd like me to review. I'll analyze it for best practices, potential issues, and improvements."
    },
    "testCraft": {
        "icon": "test_tube",  # Changed from "vial" to "test_tube"
        "title": "TestCraft - Test Suite Generator",
        "description": "Generate comprehensive test cases",
        "prompt": "What functionality would you like to create tests for? Please provide context about the code or feature."
    },
    "securityAudit": {
        "icon": "lock",  # Changed from "shield" to "lock"
        "title": "Security Auditor",
        "description": "Analyze code for security vulnerabilities",
        "prompt": "I can help identify security issues in your code. What would you like me to analyze?"
    },
    "logicLens": {
        "icon": "brain",  # Using "brain" as Streamlit equivalent for fa-lightbulb
        "title": "LogicLens - Git Logic Solver",
        "description": "Enterprise-level analysis of GitHub repositories including code quality, security, architecture, and best practices",
        "prompt": "Enter the GitHub repository URL (e.g., https://github.com/username/repo) for a comprehensive analysis of code quality, security, architecture, and best practices."
    }
    
}

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

def render_diagram_review(user_input=None):
    """Render the diagram review solution using diagramgptemb functionality"""
    if user_input:
        selected_providers = ["Alibaba Cloud"]
        color_scheme = "#FF6A00"  # Alibaba Cloud orange
        layout_direction = "LR"
        
        # Generate diagram code
        prompt = generate_diagram_prompt(user_input, selected_providers, color_scheme, layout_direction)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        try:
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": "You are a helpful Cloud architecture assistant to create a alibaba cloud diagram:"},
                    {"role": "user", "content": prompt}
                ]
            )
            generated_code = response.choices[0].message.content.strip()
            generated_code = clean_and_fix_code(generated_code)
            
            # Generate and display diagram
            img_bytes = execute_diagram_code(generated_code)
            if img_bytes:
                st.image(img_bytes.getvalue(), caption="Generated Alibaba Cloud Architecture Diagram")
                st.download_button(
                    label="Download Diagram",
                    data=img_bytes.getvalue(),
                    file_name="alibaba_cloud_architecture.png",
                    mime="image/png"
                )
                with st.expander("View Generated Code"):
                    st.code(generated_code, language="python")
            else:
                # Show fallback image if diagram generation fails
                fallback_image_path = "temp/general.png"
                if not os.path.exists(fallback_image_path):
                    fallback_image_path = "temp/basic.jpg"
                
                if os.path.exists(fallback_image_path):
                    with open(fallback_image_path, "rb") as f:
                        st.image(f.read(), caption="Reference Architecture Diagram")
        except Exception as e:
            # Show fallback image in case of any error
            fallback_image_path = "temp/basic.png"
            if not os.path.exists(fallback_image_path):
                fallback_image_path = "temp/general.jpg"
            
            if os.path.exists(fallback_image_path):
                with open(fallback_image_path, "rb") as f:
                    st.image(f.read(), caption="Reference Architecture Diagram")

def render_test_cases(user_input):
    """Generate comprehensive test cases using Qwen LLM"""
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        prompt = f"""Generate comprehensive test cases for the following code or functionality:

{user_input}

Please structure the test cases as follows:
1. Unit Tests
   - Test case name and description
   - Input values and preconditions
   - Expected outcomes
   - Edge cases to consider

2. Integration Tests (if applicable)
   - Test scenarios
   - Component interactions
   - Expected behaviors

3. Additional Test Considerations
   - Error handling cases
   - Performance test scenarios
   - Security test cases (if relevant)

Generate actual test code using appropriate testing framework based on the context."""

        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are an expert test engineer. Generate comprehensive, well-structured test cases with actual test code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True
        )
        
        return process_llm_response(completion)
        
    except Exception as e:
        raise Exception(f"Error generating test cases: {str(e)}")

def main():
    # Sidebar navigation
    st.sidebar.title("🛠️ AI DevTools")
    
    # Initialize session state for selected tool if not exists
    if 'selected_tool' not in st.session_state:
        st.session_state.selected_tool = list(tools.keys())[0]
    
    # Tool selection using buttons
    st.sidebar.markdown("### Select a Tool")
    for tool_key, tool_info in tools.items():
        if st.sidebar.button(
            f":{tool_info['icon']}: {tool_info['title']}", 
            key=tool_key,
            use_container_width=True
        ):
            st.session_state.selected_tool = tool_key
    
    # Main content area
    tool = tools[st.session_state.selected_tool]
    
    st.title(f"{tool['title']} 🔧")
    st.markdown(f"_{tool['description']}_")
    
    # User input area
    if st.session_state.selected_tool != "metamorph":
        user_input = st.text_area(
            "Your Request",
            value="",
            placeholder=tool["prompt"],
            height=150
        )
    else:
        user_input = None  # Metamorph has its own input handling
    
    # Submit button and processing
    if st.session_state.selected_tool == "metamorph":
        render_code_transformation()
    elif st.button("Submit", type="primary"):
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            st.error("Please set your DASHSCOPE_API_KEY in the .env file")
            return
            
        try:
            with st.spinner("Processing your request..."):
                if st.session_state.selected_tool == "archMaster":
                    render_architecture_solution(user_input)
                elif st.session_state.selected_tool == "codeForge":
                    render_code_generation(user_input)
                elif st.session_state.selected_tool == "logicLens":
                    if not user_input.startswith("https://github.com/"):
                        st.error("Please enter a valid GitHub repository URL (e.g., https://github.com/username/repo)")
                        return
                    render_repository_analysis(user_input)
                elif st.session_state.selected_tool == "diagramReview":
                    render_diagram_review(user_input)
                elif st.session_state.selected_tool == "diagramGPT":
                    render_diagram_review(user_input)  # Use same handler as diagramReview
                elif st.session_state.selected_tool == "testCraft":
                    if not user_input.strip():
                        st.error("Please provide code or functionality description for test generation")
                        return
                    render_test_cases(user_input)
                elif st.session_state.selected_tool == "securityAudit":
                    if not user_input.strip():
                        st.error("Please provide code to analyze for security vulnerabilities")
                        return
                    render_security_audit(user_input)
                else:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                    )
                    
                    completion = client.chat.completions.create(
                        model="qwen-plus",
                        messages=[{"role": "user", "content": user_input}],
                        temperature=1,
                        max_tokens=1024,
                        top_p=1,
                        stream=True
                    )
                    
                    process_llm_response(completion)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()