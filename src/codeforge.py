import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import subprocess
import tempfile
import shutil
import platform
import sys
from io import StringIO
import contextlib

# Load environment variables
load_dotenv()

def add_custom_css():
    """Add custom CSS for CodeForge"""
    st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: monospace;
        line-height: 1.5;
    }
    .output-area {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        white-space: pre-wrap;
        height: 400px;
        overflow-y: auto;
    }
    .stButton button {
        width: 100%;
        margin-top: 10px;
    }
    .language-error {
        color: #721c24;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .language-info {
        color: #0c5460;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_code_from_response(response_text):
    """Extract code blocks from the LLM response"""
    code_blocks = []
    lines = response_text.split('\n')
    in_code_block = False
    current_block = []
    
    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []
            in_code_block = not in_code_block
            continue
        if in_code_block:
            current_block.append(line)
    
    return '\n'.join(code_blocks) if code_blocks else response_text

def get_llm_response(prompt):
    """Get response from Qwen LLM"""
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code generator. Generate clean, optimized code based on requirements. Always wrap code blocks with ```."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling Qwen API: {str(e)}")
        return None

def get_installation_instructions(language):
    """Get installation instructions for different languages based on OS"""
    os_type = platform.system().lower()
    instructions = {
        "python": {
            "darwin": "brew install python",
            "linux": "sudo apt-get install python3",
            "windows": "Download Python from https://www.python.org/downloads/"
        },
        "node": {
            "darwin": "brew install node",
            "linux": "sudo apt-get install nodejs",
            "windows": "Download Node.js from https://nodejs.org/"
        },
        "g++": {
            "darwin": "xcode-select --install",
            "linux": "sudo apt-get install g++",
            "windows": "Install MinGW from https://mingw-w64.org/"
        },
        "ruby": {
            "darwin": "brew install ruby",
            "linux": "sudo apt-get install ruby",
            "windows": "Download Ruby from https://rubyinstaller.org/"
        }
    }
    
    if language.lower() in instructions:
        return instructions[language.lower()].get(os_type, f"Please visit the official {language} website for installation instructions.")
    return f"Please visit the official {language} website for installation instructions."

def get_command_path(command):
    """Get the full path of a command executable"""
    command_alternatives = {
        "python": ["python3", "python"],
        "node": ["node", "nodejs"],
        "g++": ["g++", "g++-11", "g++-10"],
        "ruby": ["ruby"],
        "swift": ["swift"]
    }
    
    if command in command_alternatives:
        for cmd in command_alternatives[command]:
            path = shutil.which(cmd)
            if path:
                return path
    else:
        return shutil.which(command)
    
    return None

def execute_code(code, language="python"):
    """Execute the generated code"""
    language_config = {
        "python": {"extension": "py", "command": "python"},
        "javascript": {"extension": "js", "command": "node"},
        "c++": {"extension": "cpp", "command": "g++"},
        "ruby": {"extension": "rb", "command": "ruby"},
        "swift": {"extension": "swift", "command": "swift"}
    }
    
    if language.lower() not in language_config:
        return "Error: Unsupported language"
    
    config = language_config[language.lower()]
    command_path = get_command_path(config["command"])
    
    if not command_path:
        install_instructions = get_installation_instructions(config["command"])
        return f"""Error: {config["command"]} is not installed or not found in system PATH.

Installation instructions:
{install_instructions}"""
    
    with tempfile.NamedTemporaryFile(suffix=f'.{config["extension"]}', mode='w', delete=False) as f:
        f.write(code)
        file_path = f.name
    
    try:
        if config["command"] == "g++":
            # Special handling for C++
            output_file = file_path + ".out"
            compile_result = subprocess.run([command_path, file_path, "-o", output_file], 
                                         capture_output=True, text=True)
            if compile_result.returncode != 0:
                return f"Compilation Error:\n{compile_result.stderr}"
            result = subprocess.run([output_file], capture_output=True, text=True)
        else:
            # General case for interpreted languages
            result = subprocess.run([command_path, file_path], capture_output=True, text=True)
        
        output = result.stderr if result.stderr else result.stdout
        return output if output else "Program executed successfully with no output."
    except subprocess.CalledProcessError as e:
        return f"Error during execution:\n{e.stderr if e.stderr else str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        try:
            os.unlink(file_path)
            if config["command"] == "g++":
                try:
                    os.unlink(file_path + ".out")
                except:
                    pass
        except:
            pass

def detect_language(code):
    """Detect the programming language from the code"""
    language_indicators = {
        "python": ["def ", "import ", "print(", "if __name__"],
        "javascript": ["function ", "const ", "let ", "console.log"],
        "c++": ["#include", "using namespace", "int main()", "cout <<"],
        "ruby": ["def ", "puts ", "require '", "attr_"],
        "swift": ["func ", "var ", "let ", "print("]
    }
    
    for lang, indicators in language_indicators.items():
        if any(indicator in code for indicator in indicators):
            return lang
    
    return "python"  # default to python if no language is detected

def render_code_generation(requirement):
    """Render the code generation interface"""
    try:
        # Initialize session state for code and requirement
        if 'generated_code' not in st.session_state:
            st.session_state.generated_code = None
        if 'current_requirement' not in st.session_state:
            st.session_state.current_requirement = None
            
        # Check if this is a new requirement
        if requirement != st.session_state.current_requirement:
            st.session_state.current_requirement = requirement
            st.session_state.generated_code = None
            
        # Generate code if not already generated and requirement exists
        if st.session_state.generated_code is None and requirement:
            with st.spinner("Generating code..."):
                llm_response = get_llm_response(requirement)
                if llm_response:
                    st.session_state.generated_code = extract_code_from_response(llm_response)
        
        # Display code if generated
        if st.session_state.generated_code:
            st.subheader("Generated Code")
            language = detect_language(st.session_state.generated_code)
            st.code(st.session_state.generated_code, language=language)
            
            # Add generate new code button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Generate New Code", key="clear_code", use_container_width=True):
                    st.session_state.generated_code = None
                    st.session_state.current_requirement = None
                    st.experimental_rerun()
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")

# Keep existing functions: extract_code_from_response, get_llm_response