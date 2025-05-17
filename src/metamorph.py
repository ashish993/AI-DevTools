import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

def render_code_transformation(user_input=None):
    # Create two columns for the interface
    col1, col2 = st.columns(2)
    
    # Left panel for input code
    with col1:
        st.markdown("### Input Code")
        if user_input:
            input_code = st.text_area("Enter your code", value=user_input, height=400)
        else:
            input_code = st.text_area("Enter your code", height=400)
    
    # Right panel for output and controls
    with col2:
        st.markdown("### Output")
        
        # Language selection dropdown
        target_language = st.selectbox(
            "Select Target Language",
            ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby"]
        )
        
        # Output area
        output_area = st.empty()
        
        # Convert button
        if st.button("Convert", type="primary"):
            if not input_code.strip():
                st.error("Please enter some code to convert")
                return
                
            try:
                # Initialize OpenAI client with Qwen configuration
                client = OpenAI(
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                )
                
                # Prepare the prompt for code conversion
                prompt = f"""Convert the following code to {target_language}. 
                Only return the converted code without any explanations.
                Here's the code to convert:
                
                {input_code}"""
                
                # Create completion with streaming
                completion = client.chat.completions.create(
                    model="qwen-plus",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower temperature for more precise code generation
                    max_tokens=2048,
                    top_p=1,
                    stream=True
                )
                
                # Process streaming response
                converted_code = ""
                with st.spinner(f"Converting to {target_language}..."):
                    for chunk in completion:
                        if hasattr(chunk.choices[0], 'delta'):
                            content = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else ""
                        elif hasattr(chunk.choices[0], 'text'):
                            content = chunk.choices[0].text
                        else:
                            content = ""
                            
                        if content:
                            converted_code += content
                            # Update the output area with the current state
                            output_area.code(converted_code, language=target_language.lower())
                
            except Exception as e:
                st.error(f"An error occurred during conversion: {str(e)}")