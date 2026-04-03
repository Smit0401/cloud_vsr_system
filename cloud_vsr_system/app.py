import streamlit as st
import google.generativeai as genai
import os
import time
import tempfile

# Basic Page Setup
st.set_page_config(page_title="AI Video Analyst", layout="centered")

# --- API KEY CONFIG ---
# This looks for the key in Streamlit Cloud Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Go to Streamlit Settings > Secrets and add: GEMINI_API_KEY = 'your_key_here'")
    st.stop()

genai.configure(api_key=api_key)

st.title("🎬 AI Video Recognition")
st.write("Upload a video and wait for the AI to analyze it.")

uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi"])

if uploaded_file:
    st.video(uploaded_file)
    
    if st.button("Analyze Video"):
        with st.spinner("AI is processing..."):
            try:
                # Save to a temp file
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                # Upload to Google
                video_file = genai.upload_file(path=tmp_path)
                
                # Wait for Google to process the video
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)

                # Find the correct model name (handles 404 errors)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model_name = "models/gemini-1.5-flash"
                if model_name not in available_models:
                    # Fallback to the first 1.5-flash model found
                    flash_models = [m for m in available_models if '1.5-flash' in m]
                    model_name = flash_models[0] if flash_models else "models/gemini-pro"

                model = genai.GenerativeModel(model_name)
                response = model.generate_content([
                    "What is happening in this video? Describe it in detail.",
                    video_file
                ])

                st.success("Done!")
                st.write(response.text)
                
                # Cleanup
                genai.delete_file(video_file.name)
                os.unlink(tmp_path)

            except Exception as e:
                st.error(f"Error: {str(e)}")
