"""
This module handles RFP document processing and question answering functionality.
"""
import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from PyPDF2 import PdfReader
import docx
import tempfile

def read_pdf(file):
    """Extract text from PDF file"""
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_docx(file):
    """Extract text from DOCX file"""
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def process_document(uploaded_file):
    """Process uploaded document and extract text"""
    if uploaded_file is None:
        return None
    
    # Create temp file to handle the upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file.flush()
        
        try:
            if uploaded_file.name.endswith('.pdf'):
                text = read_pdf(tmp_file.name)
            elif uploaded_file.name.endswith(('.doc', '.docx')):
                text = read_docx(tmp_file.name)
            else:
                st.error("Unsupported file format. Please upload PDF or DOCX files.")
                return None
                
            return text
        finally:
            os.unlink(tmp_file.name)

def process_questions(questions_file, document_text):
    """Process questions from Excel/CSV and generate answers"""
    try:
        if questions_file.name.endswith('.csv'):
            df = pd.read_csv(questions_file)
        else:
            df = pd.read_excel(questions_file)
        
        if 'Question' not in df.columns:
            st.error("The file must contain a 'Question' column")
            return None
        
        answers = []
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        progress_bar = st.progress(0)
        for idx, row in df.iterrows():
            prompt = f"""Based on the following internal document, answer the question professionally and concisely (1-2 lines):

Document: {document_text}

Question: {row['Question']}

Remember to:
1. Answer only based on information in the document
2. Be professional and clear
3. Keep the answer concise (1-2 lines)
4. If information is not in the document, say "Information not available in the provided document."
"""
            
            try:
                response = client.chat.completions.create(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": "You are a professional RFP response generator. Generate concise, accurate answers based solely on the provided document."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                answer = response.choices[0].message.content.strip()
                answers.append(answer)
                progress_bar.progress((idx + 1) / len(df))
            except Exception as e:
                st.error(f"Error processing question {idx + 1}: {str(e)}")
                answers.append("Error processing this question")
        
        df['Answer'] = answers
        return df
        
    except Exception as e:
        st.error(f"Error processing questions file: {str(e)}")
        return None

def render_rfp_solver():
    """Main function to render the RFP solver interface"""
    st.write("Upload your internal document (PDF/DOCX) and questions file (Excel/CSV) to generate professional RFP responses.")
    
    # Initialize session state for document text
    if 'document_text' not in st.session_state:
        st.session_state.document_text = None
    
    # Document upload section
    if st.session_state.document_text is None:
        uploaded_doc = st.file_uploader(
            "Upload Internal Document",
            type=['pdf', 'doc', 'docx'],
            key='doc_uploader'
        )
        
        if uploaded_doc is not None:
            with st.spinner("Processing document..."):
                document_text = process_document(uploaded_doc)
                if document_text:
                    st.session_state.document_text = document_text
                    st.success("Document processed successfully!")
                    st.rerun()  # Changed from experimental_rerun to rerun
    
    # Questions upload section
    if st.session_state.document_text is not None:
        questions_file = st.file_uploader(
            "Upload Questions File",
            type=['xlsx', 'csv'],
            key='questions_uploader'
        )
        
        if questions_file is not None:
            with st.spinner("Processing questions and generating answers..."):
                results_df = process_questions(questions_file, st.session_state.document_text)
                
                if results_df is not None:
                    st.write("### Generated Answers")
                    st.dataframe(results_df[['Question', 'Answer']])
                    
                    # Download results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name="rfp_responses.csv",
                        mime="text/csv"
                    )
        
        # Option to reset
        if st.button("Process New Document"):
            st.session_state.document_text = None
            st.rerun()  # Changed from experimental_rerun to rerun