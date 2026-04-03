import streamlit as st
import google.generativeai as genai
import os
import time
import tempfile

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Video Analyst",
    page_icon="🎬",
    layout="centered"
)

# --- STYLE ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIG ---
# Streamlit Cloud uses st.secrets for API keys
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Fallback for local testing
    api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("⚠️ Gemini API Key not found. Please add it to Secrets in Streamlit Cloud.")
    st.stop()

# --- APP UI ---
st.title("🎬 AI Video Recognition System")
st.write("Upload a video and let Gemini AI analyze the content, objects, and actions.")

uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # 1. Display the video
    st.video(uploaded_file)
    
    # 2. Analysis Button
    if st.button("🚀 Analyze Video Content"):
        with st.status("Processing video with Gemini AI...", expanded=True) as status:
            try:
                # Save uploaded file to a temporary location
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                st.write("📤 Uploading to Google AI Studio...")
                video_file = genai.upload_file(path=video_path)
                
                # Wait for the file to be processed by Google
                st.write("⏳ AI is watching the video...")
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)

                if video_file.state.name == "FAILED":
                    st.error("❌ Video processing failed on the AI server.")
                    st.stop()

                st.write("🧠 Generating analysis...")
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                response = model.generate_content([
                    "Analyze this video in detail. Describe the setting, the main subjects, any significant actions, and provide a summary of the events.",
                    video_file
                ])

                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                # Display Results
                st.success("Analysis Result:")
                st.markdown(response.text)

                # Cleanup
                os.unlink(video_path)
                genai.delete_file(video_file.name)

            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                if 'video_path' in locals(): os.unlink(video_path)
else:
    st.info("💡 Please upload a video file (MP4, MOV, etc.) to begin.")
