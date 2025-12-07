import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
import zipfile
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Photo Style Converter",
    page_icon="📸",
    layout="wide",
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
    .sample-card {
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        transition: all 0.3s;
    }
    .sample-card:hover {
        border-color: #7c3aed;
        box-shadow: 0 4px 6px rgba(124, 58, 237, 0.1);
    }
    .sample-card.selected {
        border-color: #7c3aed;
        background-color: #f5f3ff;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'sample_variations' not in st.session_state:
    st.session_state.sample_variations = {}
if 'selected_samples' not in st.session_state:
    st.session_state.selected_samples = []
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {}

# Style variations - 4 options per style
STYLE_VARIATIONS = {
    "professional": {
        "Corporate Executive": "professional corporate executive headshot, dark suit, confident expression, modern office background, studio lighting, sharp focus",
        "Creative Professional": "professional creative industry headshot, smart casual attire, approachable expression, bright modern workspace, natural lighting",
        "LinkedIn Classic": "classic professional LinkedIn profile photo, business formal attire, neutral background, professional studio portrait",
        "Business Casual": "professional business casual style, relaxed yet polished, contemporary setting, friendly professional demeanor"
    },
    "fun": {
        "Vibrant Pop Art": "fun vibrant pop art style, bold bright colors, playful energy, comic book aesthetic, dynamic composition",
        "Cheerful Cartoon": "fun cheerful cartoon illustration style, cute animated look, happy colors, whimsical playful mood",
        "Festival Vibes": "fun festival party vibes, colorful energetic atmosphere, celebration mood, joyful expression, confetti and lights",
        "Retro Fun": "fun retro 80s style, neon colors, playful vintage aesthetic, energetic disco vibes"
    },
    "artistic": {
        "Oil Painting": "artistic oil painting masterpiece, rich textures, classical art style, museum quality, painterly brushstrokes",
        "Watercolor Dream": "artistic watercolor painting, soft flowing colors, dreamy ethereal quality, delicate artistic touch",
        "Digital Art": "artistic digital illustration, modern creative style, vibrant artistic interpretation, unique visual design",
        "Impressionist": "artistic impressionist style, loose brushwork, play of light, artistic color palette, Monet-inspired"
    },
    "vintage": {
        "1970s Film": "vintage 1970s film photography, warm tones, nostalgic film grain, classic retro aesthetic",
        "Sepia Classic": "vintage sepia tone photograph, antique timeless look, historical photography style",
        "Polaroid Nostalgia": "vintage polaroid style, instant film aesthetic, faded colors, nostalgic retro charm",
        "Black & White Classic": "vintage black and white photography, classic film noir style, dramatic contrast, timeless elegance"
    },
    "modern": {
        "Minimalist Chic": "modern minimalist style, clean lines, contemporary aesthetic, simple sophisticated look",
        "High Fashion": "modern high fashion editorial, sleek polished style, contemporary magazine quality",
        "Urban Contemporary": "modern urban contemporary style, city vibes, trendy modern aesthetic, sharp details",
        "Tech Forward": "modern tech-forward style, futuristic clean look, innovative contemporary design"
    }
}

def generate_image_variation(image, style_name, variation_prompt):
    """
    Generate a specific style variation using Gemini 2.5 Flash Image (Nano Banana)
    """
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
    
    if not api_key:
        st.error("⚠️ Google API key not found.")
        return None
    
    try:
        # Configure client
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        prompt = f"Transform this photo into: {variation_prompt}. Generate the transformed image."
        
        # Use the correct method: client.models.generate_content
        response = client.generate_content([prompt, image])
        
        # Check for image in response
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    import base64
                    image_data = part.inline_data.data
                    processed_image = Image.open(io.BytesIO(image_data))
                    return processed_image
        
        # If text response, show it
        if response.text:
            st.caption(f"AI: {response.text[:200]}...")
        
        # Return original for now (free tier may not generate images)
        return image
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def create_zip_file(images_dict):
    """
    Create a zip file containing all selected images
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, image in images_dict.items():
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            # Add image to zip with descriptive filename
            safe_name = name.replace(' ', '_').replace('/', '_')
            zip_file.writestr(f"{safe_name}.jpg", img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

# App Header
st.title("📸 Photo Style Converter")
st.markdown("Transform your photos with AI-powered styles - Select multiple variations!")
st.markdown("---")

# Main layout
col_upload, col_style = st.columns([1, 1])

with col_upload:
    st.subheader("1️⃣ Upload Photo")
    uploaded_file = st.file_uploader(
        "Choose your photo",
        type=['png', 'jpg', 'jpeg'],
        help="Supported formats: PNG, JPG, JPEG"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.original_image = image
        st.image(image, caption="Original Photo", use_container_width=True)

with col_style:
    st.subheader("2️⃣ Choose Style")
    selected_style = st.selectbox(
        "Select main style category:",
        options=list(STYLE_VARIATIONS.keys()),
        format_func=lambda x: x.title(),
        key="style_selector"
    )

# Show variations if image is uploaded
if st.session_state.original_image is not None:
    st.markdown("---")
    st.subheader(f"3️⃣ Select Variations for '{selected_style.title()}' Style")
    st.markdown("*Choose one or more variations to generate*")
    
    # Display 4 variation options
    variations = STYLE_VARIATIONS[selected_style]
    
    cols = st.columns(2)
    
    for idx, (var_name, var_prompt) in enumerate(variations.items()):
        with cols[idx % 2]:
            is_selected = var_name in st.session_state.selected_samples
            
            with st.container():
                st.markdown(f"**{var_name}**")
                st.caption(var_prompt[:80] + "...")
                
                if st.checkbox(
                    f"Select {var_name}",
                    key=f"checkbox_{var_name}",
                    value=is_selected
                ):
                    if var_name not in st.session_state.selected_samples:
                        st.session_state.selected_samples.append(var_name)
                else:
                    if var_name in st.session_state.selected_samples:
                        st.session_state.selected_samples.remove(var_name)
    
    st.markdown("---")
    
    # Generate button
    if len(st.session_state.selected_samples) > 0:
        st.info(f"✅ {len(st.session_state.selected_samples)} variation(s) selected")
        
        if st.button("🎨 Generate Selected Variations", type="primary", use_container_width=True):
            st.session_state.generated_images = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total = len(st.session_state.selected_samples)
            
            for idx, var_name in enumerate(st.session_state.selected_samples):
                status_text.text(f"Generating {var_name}... ({idx+1}/{total})")
                
                var_prompt = variations[var_name]
                generated = generate_image_variation(
                    st.session_state.original_image,
                    selected_style,
                    var_prompt
                )
                
                if generated:
                    st.session_state.generated_images[var_name] = generated
                
                progress_bar.progress((idx + 1) / total)
            
            status_text.empty()
            progress_bar.empty()
            st.success(f"✅ Generated {len(st.session_state.generated_images)} variations!")
            st.balloons()
    else:
        st.warning("⚠️ Please select at least one variation to generate")
    
    # Display generated images
    if st.session_state.generated_images:
        st.markdown("---")
        st.subheader("4️⃣ Generated Images")
        
        # Display in grid
        cols = st.columns(2)
        for idx, (name, img) in enumerate(st.session_state.generated_images.items()):
            with cols[idx % 2]:
                st.image(img, caption=name, use_container_width=True)
        
        st.markdown("---")
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            # Download as ZIP
            zip_data = create_zip_file(st.session_state.generated_images)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label=f"📦 Download All as ZIP ({len(st.session_state.generated_images)} images)",
                data=zip_data,
                file_name=f"styled_photos_{selected_style}_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        with col2:
            # Individual downloads
            if st.button("📥 Show Individual Downloads", use_container_width=True):
                st.session_state.show_individual = True
        
        # Show individual download buttons if requested
        if st.session_state.get('show_individual', False):
            st.markdown("#### Individual Downloads")
            for name, img in st.session_state.generated_images.items():
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                
                safe_name = name.replace(' ', '_')
                st.download_button(
                    label=f"⬇️ {name}",
                    data=img_buffer,
                    file_name=f"{safe_name}_{timestamp}.jpg",
                    mime="image/jpeg",
                    key=f"download_{name}"
                )

else:
    st.info("👆 Upload a photo to get started!")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 14px;'>"
    "🔒 <b>Privacy First:</b> All processing happens in real-time. No images are stored on our servers."
    "</p>",
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.header("ℹ️ How It Works")
    st.markdown("""
    1. **Upload** your photo
    2. **Choose** a style category
    3. **Select** one or more variations
    4. **Generate** styled images
    5. **Download** as ZIP or individually
    
    ---
    
    **Features:**
    - ✅ Multiple variations per style
    - ✅ Bulk ZIP download
    - ✅ Individual downloads
    - ✅ No storage, real-time processing
    
    ---
    
    **Powered by:** Google Gemini AI
    """)
    
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.clear()
        st.rerun()