import streamlit as st
import requests
from PIL import Image
import io
import base64
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

def process_image_with_nanobananapro(image, style):
    """
    Process image using Nano Banana Pro API
    """
    api_key = os.getenv("NANOBANANAPRO_API_KEY") or st.secrets.get("NANOBANANAPRO_API_KEY", None)
    
    if not api_key:
        st.error("⚠️ Nano Banana Pro API key not found. Please add it to Streamlit secrets.")
        return None
    
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Encode to base64
        img_base64 = base64.b64encode(img_byte_arr).decode()
        
        # Prepare API call to Nano Banana Pro
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Style-specific prompts for better results
        style_prompts = {
            "professional": "professional corporate headshot, studio lighting, formal business attire, clean background",
            "fun": "vibrant colorful playful style, bright colors, cheerful energetic mood",
            "artistic": "artistic creative expressive style, painterly effect, unique artistic vision",
            "vintage": "vintage retro classic look, nostalgic film grain, warm tones",
            "modern": "modern clean contemporary style, minimalist aesthetic, crisp sharp details"
        }
        
        payload = {
            "image": img_base64,
            "prompt": style_prompts.get(style, ""),
            "style": style,
            # Add other parameters based on Nano Banana Pro API documentation
        }
        
        # Replace with actual Nano Banana Pro endpoint
        # response = requests.post(
        #     "https://api.nanobananapro.com/v1/image/process",
        #     headers=headers,
        #     json=payload,
        #     timeout=60
        # )
        # 
        # if response.status_code == 200:
        #     result = response.json()
        #     processed_image_base64 = result['image']
        #     processed_image_bytes = base64.b64decode(processed_image_base64)
        #     return Image.open(io.BytesIO(processed_image_bytes))
        
        # For demo purposes, returning original image
        # Remove this and uncomment above code when using real API
        return image
        
    except Exception as e:
        st.error(f"❌ Error processing image: {str(e)}")
        return None

# App Header
st.title("📸 Photo Style Converter")
st.markdown("Transform your photos with AI-powered styles")
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
        with st.spinner(f"🎨 Applying {selected_style} style to your image..."):
            processed = process_image_with_nanobananapro(image, selected_style)
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
        
        st.success("👆 Click the button above to download your styled photo!")

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
    **Photo Style Converter** uses AI to transform your photos into different artistic styles.
    
    **How to use:**
    1. Choose a style
    2. Upload your photo
    3. Click 'Apply Style'
    4. Download your result
    
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
    - ✅ Secure processing
    """)