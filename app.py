import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# Page config
st.set_page_config(
    page_title="Photo Style Converter",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #7c3aed;
        color: white;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #6d28d9;
    }
    .download-button>button {
        background-color: #10b981;
    }
    .download-button>button:hover {
        background-color: #059669;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'original_image' not in st.session_state:
    st.session_state.original_image = None

def process_image_with_gemini(image, style):
    """
    Process image using Gemini 2.5 Flash (Nano Banana) for image generation
    """
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
    
    if not api_key:
        st.error("⚠️ Google API key not found. Please add GOOGLE_API_KEY to Streamlit secrets.")
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Style-specific prompts for image generation
        style_prompts = {
            "professional": "Generate a professional corporate headshot version of this person with studio lighting, formal business attire, clean neutral background, sharp focus, high quality professional photography style",
            "fun": "Generate a fun, vibrant, and playful version of this photo with bright cheerful colors, energetic mood, joyful atmosphere, pop art influences, creative and upbeat style",
            "artistic": "Generate an artistic masterpiece version with creative expressive style, painterly effects, unique artistic vision, fine art photography aesthetic, creative interpretation",
            "vintage": "Generate a vintage classic version with retro film aesthetic, nostalgic warm tones, subtle film grain, 1970s photography style, timeless classic appeal",
            "modern": "Generate a modern contemporary version with clean minimalist aesthetic, crisp sharp details, modern color grading, sleek sophisticated look, contemporary style"
        }
        
        prompt = style_prompts.get(style, "Generate a stylized artistic version of this photo")
        
        # Use Gemini 2.5 Flash with image generation
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Generate styled image
        response = model.generate_content([prompt, image])
        
        # Check if response contains an image
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Get image data
                    import base64
                    image_data = part.inline_data.data
                    processed_image = Image.open(io.BytesIO(image_data))
                    return processed_image
        
        # If no image in response, show text if available
        if response.text:
            st.info(f"🎨 **AI Response**: {response.text}")
        
        st.warning("⚠️ No image was generated. The model may not support image output yet.")
        return image
        
    except Exception as e:
        st.error(f"❌ Error processing image: {str(e)}")
        st.info("💡 Tip: Make sure your Google API key has access to Gemini 2.5 Flash image generation.")
        return None

# App Header
st.title("📸 Photo Style Converter")
st.markdown("Transform your photos with AI-powered styles using Google Gemini")
st.markdown("---")

# Style selection
styles = {
    "professional": "Professional - Corporate headshot style",
    "fun": "Fun - Vibrant and playful",
    "artistic": "Artistic - Creative and expressive",
    "vintage": "Vintage - Classic retro look",
    "modern": "Modern - Clean contemporary style"
}

selected_style = st.selectbox(
    "Choose a style:",
    options=list(styles.keys()),
    format_func=lambda x: styles[x],
    key="style_selector"
)

st.markdown("")

# Image upload
uploaded_file = st.file_uploader(
    "Upload your photo",
    type=['png', 'jpg', 'jpeg'],
    help="Supported formats: PNG, JPG, JPEG (Max 10MB)"
)

if uploaded_file is not None:
    # Display original image
    image = Image.open(uploaded_file)
    st.session_state.original_image = image
    
    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📷 Original")
        st.image(image, use_container_width=True)
    
    with col2:
        if st.session_state.processed_image is not None:
            st.subheader("✨ Processed")
            st.image(st.session_state.processed_image, use_container_width=True)
        else:
            st.subheader("✨ Processed")
            st.info("👆 Click 'Apply Style' to process your image")
    
    st.markdown("")
    
    # Process button
    if st.button("✨ Apply Style", type="primary"):
        with st.spinner(f"🎨 Generating {selected_style} style with Nano Banana (Gemini 2.5)..."):
            processed = process_image_with_gemini(image, selected_style)
            if processed:
                st.session_state.processed_image = processed
                st.success("✅ Image processed successfully!")
                st.balloons()
    
    # Download section
    if st.session_state.processed_image is not None:
        st.markdown("---")
        st.markdown("### 💾 Download Your Photo")
        
        # Convert image to bytes for download
        img_byte_arr = io.BytesIO()
        st.session_state.processed_image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        # Create download button
        st.download_button(
            label="⬇️ Download Photo",
            data=img_byte_arr,
            file_name=f"photo-{selected_style}-{uploaded_file.name}",
            mime="image/jpeg",
            key="download_button",
            use_container_width=True
        )
        
        st.success("👆 Click the button above to download your photo!")

else:
    # Show instructions when no image is uploaded
    st.info("👆 Upload a photo to get started!")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 14px;'>"
    "🔒 <b>Privacy First:</b> All processing happens in real-time. No images are stored on our servers."
    "</p>",
    unsafe_allow_html=True
)

# Sidebar info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **Photo Style Converter** uses Nano Banana (Gemini 2.5 Flash) to generate styled versions of your photos.
    
    **How to use:**
    1. Choose a style
    2. Upload your photo
    3. Click 'Apply Style'
    4. Get AI-generated styled image
    5. Download your result
    
    **Styles available:**
    - 🎯 Professional
    - 🎉 Fun
    - 🎨 Artistic
    - 📼 Vintage
    - 🔮 Modern
    
    ---
    
    **Privacy & Security:**
    - ✅ No image storage
    - ✅ Real-time processing
    - ✅ Secure API calls
    
    ---
    
    **Powered by:** Google Gemini 2.5 Flash (Nano Banana)
    """)