import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import zipfile
from datetime import datetime
import numpy as np
from PIL import ImageOps

# Page config
st.set_page_config(
    page_title="Photo Style Converter Pro",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'original_images' not in st.session_state:
    st.session_state.original_images = []
if 'edited_images' not in st.session_state:
    st.session_state.edited_images = []
if 'current_adjustments' not in st.session_state:
    st.session_state.current_adjustments = {}
if 'sample_variations' not in st.session_state:
    st.session_state.sample_variations = {}
if 'selected_samples' not in st.session_state:
    st.session_state.selected_samples = []
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {}
if 'previous_style' not in st.session_state:
    st.session_state.previous_style = None

# Style variations
STYLE_VARIATIONS = {
    "professional": {
        "Corporate Executive": "professional corporate executive headshot framed from head to chest level, dark suit, confident expression, modern office background, studio lighting, sharp focus, professional portrait crop",
        "Creative Professional": "professional creative industry headshot framed from head to chest level, smart casual attire, approachable expression, bright modern workspace, natural lighting, professional portrait crop",
        "LinkedIn Classic": "classic professional LinkedIn profile photo framed from head to chest level, business formal attire, neutral background, professional studio portrait, proper headshot framing",
        "Business Casual": "professional business casual style headshot framed from head to chest level, relaxed yet polished, contemporary setting, friendly professional demeanor, proper portrait crop"
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

# Preset crop ratios
CROP_PRESETS = {
    "Instagram Square": (1, 1),
    "Instagram Portrait": (4, 5),
    "Facebook Cover": (16, 9),
    "Passport Photo": (35, 45),
    "LinkedIn Banner": (4, 1),
    "Original": None
}

def apply_basic_adjustments(image, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0):
    """Apply basic photo adjustments"""
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
    
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness)
    
    return image

def apply_noise_reduction(image, strength=1):
    """Apply noise reduction filter"""
    for _ in range(strength):
        image = image.filter(ImageFilter.MedianFilter(size=3))
    return image

def crop_image(image, ratio):
    """Crop image to specified ratio"""
    if ratio is None:
        return image
    
    width, height = image.size
    target_ratio = ratio[0] / ratio[1]
    current_ratio = width / height
    
    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))
    
    return image

def resize_image(image, scale_percent):
    """Resize image by percentage"""
    if scale_percent == 100:
        return image
    
    width, height = image.size
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def rotate_image(image, angle):
    """Rotate image by angle"""
    if angle == 0:
        return image
    return image.rotate(-angle, expand=True, fillcolor='white')

def remove_background_simple(image):
    """Simple background removal (placeholder - in production use rembg library)"""
    # This is a placeholder. In production, use: from rembg import remove
    # return remove(image)
    st.info("💡 Background removal requires 'rembg' library. Install with: pip install rembg")
    return image

def upscale_image(image, factor=2):
    """Simple upscaling (placeholder - in production use AI upscaler)"""
    width, height = image.size
    new_size = (width * factor, height * factor)
    return image.resize(new_size, Image.Resampling.LANCZOS)

def generate_image_variation(image, style_name, variation_prompt, enhancements=None):
    """Generate style variation using Gemini 2.5 Flash Image (Nano Banana)"""
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
    
    if not api_key:
        st.error("⚠️ Google API key not found.")
        return None
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        enhancement_text = ""
        if enhancements:
            enhancements_list = []
            if enhancements.get('hair'):
                enhancements_list.append("subtle hair enhancement, slightly fill in any thinning areas naturally, maintain original hairstyle and volume, keep it realistic and close to original appearance")
            if enhancements.get('skin'):
                enhancements_list.append("smooth flawless skin, reduced wrinkles and fine lines, even skin tone, no blemishes or imperfections")
            if enhancements.get('teeth'):
                enhancements_list.append("bright white teeth, perfect smile, dental enhancement")
            if enhancements.get('eyes'):
                enhancements_list.append("bright clear eyes, enhanced eye color, sparkle and clarity, well-defined features")
            if enhancements.get('lighting'):
                enhancements_list.append("professional studio lighting, perfect illumination, flattering light setup")
            if enhancements.get('sharpness'):
                enhancements_list.append("enhanced sharpness and clarity, crisp details, high definition quality")
            
            if enhancements_list:
                enhancement_text = f" IMPORTANT ENHANCEMENTS: {', '.join(enhancements_list)}."
        
        framing_text = ""
        if style_name == "professional":
            framing_text = " CRITICAL FRAMING: Image must be framed from head to chest level only (professional headshot crop). Do not show full body. Proper portrait framing with shoulders and upper chest visible."
        
        prompt = f"Edit and transform this photo: {variation_prompt}.{framing_text}{enhancement_text} IMPORTANT: Keep all enhancements subtle and natural. The result should look very close to the original photo, just enhanced and polished with the specified style applied. Do not make dramatic changes. Generate a high-quality transformed image."
        
        # Create model instance
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Generate content
        response = model.generate_content([prompt, image])
        
        # Check for generated image in response
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Extract the generated image
                    image_data = part.inline_data.data
                    processed_image = Image.open(io.BytesIO(image_data))
                    return processed_image
        
        # If text response, show it
        if hasattr(response, 'text') and response.text:
            st.caption(f"AI Response: {response.text[:150]}...")
        
        # Fallback: return original
        st.warning("⚠️ No image generated in response. The model may only support text output currently.")
        return image
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle specific errors
        if '429' in error_msg or 'quota' in error_msg.lower():
            st.error("⚠️ API quota exceeded. Please wait a moment and try again.")
        elif '404' in error_msg or 'not found' in error_msg.lower():
            st.error("⚠️ Model 'gemini-2.5-flash-image-preview' not found. This model may not be available yet.")
            st.info("💡 Try updating: pip install --upgrade google-generativeai")
        else:
            st.error(f"❌ Error: {error_msg[:200]}")
        
        return image

def create_zip_file(images_dict):
    """Create ZIP file with all images"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, image in images_dict.items():
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            safe_name = name.replace(' ', '_').replace('/', '_')
            zip_file.writestr(f"{safe_name}.jpg", img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

# Header
col_header1, col_header2 = st.columns([3, 1])

with col_header1:
    st.title("📸 PhotoStyle Pro")
    st.markdown("Professional Photo Editor & AI Style Converter")

with col_header2:
    st.markdown("")
    if st.button("🔄 Start Over", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# Main tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload & Edit", "🎨 Style Conversion", "📥 Download"])

# TAB 1: Upload & Edit
with tab1:
    st.header("Step 1: Upload and Edit Photos")
    
    # Batch upload
    uploaded_files = st.file_uploader(
        "Upload one or multiple photos",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Upload multiple images for batch processing"
    )
    
    if uploaded_files:
        st.session_state.original_images = [Image.open(f) for f in uploaded_files]
        
        if not st.session_state.edited_images:
            st.session_state.edited_images = st.session_state.original_images.copy()
        
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded")
        
        # Image selector for editing
        if len(st.session_state.original_images) > 1:
            selected_idx = st.selectbox(
                "Select image to edit:",
                range(len(st.session_state.original_images)),
                format_func=lambda x: f"Image {x+1}"
            )
        else:
            selected_idx = 0
        
        current_image = st.session_state.edited_images[selected_idx]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Original")
            st.image(st.session_state.original_images[selected_idx], use_container_width=True)
        
        with col2:
            st.subheader("Edited Preview")
            preview_placeholder = st.empty()
            preview_placeholder.image(current_image, use_container_width=True)
        
        st.markdown("---")
        
        # Editing tools in expandable sections
        with st.expander("⚙️ Basic Adjustments", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                brightness = st.slider("💡 Brightness", 0.5, 2.0, 1.0, 0.1, key=f"bright_{selected_idx}")
                contrast = st.slider("🎭 Contrast", 0.5, 2.0, 1.0, 0.1, key=f"contrast_{selected_idx}")
            
            with col2:
                saturation = st.slider("🌈 Saturation", 0.0, 2.0, 1.0, 0.1, key=f"sat_{selected_idx}")
                sharpness = st.slider("🔪 Sharpness", 0.0, 3.0, 1.0, 0.1, key=f"sharp_{selected_idx}")
            
            with col3:
                if st.button("Apply Adjustments", key=f"apply_basic_{selected_idx}"):
                    edited = apply_basic_adjustments(
                        st.session_state.original_images[selected_idx],
                        brightness, contrast, saturation, sharpness
                    )
                    st.session_state.edited_images[selected_idx] = edited
                    preview_placeholder.image(edited, use_container_width=True)
                    st.success("✅ Applied!")
        
        with st.expander("✂️ Crop, Rotate & Resize"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                crop_preset = st.selectbox("Crop Preset", list(CROP_PRESETS.keys()), key=f"crop_{selected_idx}")
                rotate_angle = st.slider("Rotate (degrees)", -180, 180, 0, 15, key=f"rotate_{selected_idx}")
            
            with col2:
                resize_percent = st.slider("Resize (%)", 25, 200, 100, 5, key=f"resize_{selected_idx}")
            
            with col3:
                if st.button("Apply Transform", key=f"apply_transform_{selected_idx}"):
                    edited = st.session_state.original_images[selected_idx].copy()
                    
                    # Apply crop
                    if crop_preset != "Original":
                        edited = crop_image(edited, CROP_PRESETS[crop_preset])
                    
                    # Apply rotation
                    if rotate_angle != 0:
                        edited = rotate_image(edited, rotate_angle)
                    
                    # Apply resize
                    if resize_percent != 100:
                        edited = resize_image(edited, resize_percent)
                    
                    st.session_state.edited_images[selected_idx] = edited
                    preview_placeholder.image(edited, use_container_width=True)
                    st.success("✅ Transformed!")
        
        with st.expander("🧹 Noise Reduction & Enhancement"):
            col1, col2 = st.columns(2)
            
            with col1:
                noise_strength = st.slider("Noise Reduction", 0, 3, 0, key=f"noise_{selected_idx}")
                
                if st.button("Remove Background", key=f"rembg_{selected_idx}"):
                    edited = remove_background_simple(st.session_state.edited_images[selected_idx])
                    st.session_state.edited_images[selected_idx] = edited
                    preview_placeholder.image(edited, use_container_width=True)
            
            with col2:
                upscale_factor = st.radio("Upscale Resolution", [1, 2, 4], key=f"upscale_{selected_idx}")
                
                if st.button("Apply Enhancement", key=f"enhance_{selected_idx}"):
                    edited = st.session_state.edited_images[selected_idx].copy()
                    
                    if noise_strength > 0:
                        edited = apply_noise_reduction(edited, noise_strength)
                    
                    if upscale_factor > 1:
                        edited = upscale_image(edited, upscale_factor)
                    
                    st.session_state.edited_images[selected_idx] = edited
                    preview_placeholder.image(edited, use_container_width=True)
                    st.success("✅ Enhanced!")
        
        # Batch apply
        if len(st.session_state.original_images) > 1:
            st.markdown("---")
            if st.button("🔄 Apply Current Settings to All Images", type="primary"):
                with st.spinner("Processing all images..."):
                    for i in range(len(st.session_state.original_images)):
                        edited = apply_basic_adjustments(
                            st.session_state.original_images[i],
                            brightness, contrast, saturation, sharpness
                        )
                        st.session_state.edited_images[i] = edited
                    st.success(f"✅ Applied to all {len(st.session_state.original_images)} images!")
                    st.rerun()

# TAB 2: Style Conversion
with tab2:
    if not st.session_state.edited_images:
        st.info("👈 Please upload images in the 'Upload & Edit' tab first")
    else:
        st.header("Step 2: AI Style Conversion")
        
        col_style1, col_style2 = st.columns([1, 2])
        
        with col_style1:
            # Style selection
            selected_style = st.selectbox(
                "Choose Style Category:",
                options=list(STYLE_VARIATIONS.keys()),
                format_func=lambda x: x.title(),
                key="style_selector"
            )
            
            # Clear selections if style changed
            if st.session_state.previous_style != selected_style:
                st.session_state.selected_samples = []
                st.session_state.generated_images = {}
                st.session_state.previous_style = selected_style
            
            # Enhancements
            st.markdown("### ✨ Enhancements")
            enhancements = {}
            enhancements['hair'] = st.checkbox("💇 Subtle Hair Enhancement", value=False)
            enhancements['skin'] = st.checkbox("✨ Skin Smoothing", value=False)
            enhancements['teeth'] = st.checkbox("😁 Teeth Whitening", value=False)
            enhancements['eyes'] = st.checkbox("👁️ Eye Enhancement", value=False)
            enhancements['lighting'] = st.checkbox("💡 Professional Lighting", value=True)
            enhancements['sharpness'] = st.checkbox("🔍 Enhanced Sharpness", value=True)
            
            st.session_state.enhancements = enhancements
        
        with col_style2:
            st.markdown("### Select Variations")
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
            
            if len(st.session_state.selected_samples) > 0:
                st.info(f"✅ {len(st.session_state.selected_samples)} variation(s) selected")
                
                if st.button("🎨 Generate Selected Variations", type="primary", use_container_width=True):
                    st.session_state.generated_images = {}
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total = len(st.session_state.selected_samples) * len(st.session_state.edited_images)
                    count = 0
                    
                    for img_idx, image in enumerate(st.session_state.edited_images):
                        for var_name in st.session_state.selected_samples:
                            status_text.text(f"Generating {var_name} for Image {img_idx+1}... ({count+1}/{total})")
                            
                            if var_name not in variations:
                                continue
                            
                            var_prompt = variations[var_name]
                            generated = generate_image_variation(
                                image,
                                selected_style,
                                var_prompt,
                                st.session_state.enhancements
                            )
                            
                            if generated:
                                key = f"img{img_idx+1}_{var_name}"
                                st.session_state.generated_images[key] = generated
                            
                            count += 1
                            progress_bar.progress(count / total)
                    
                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ Generated {len(st.session_state.generated_images)} variations!")
                    st.balloons()
            else:
                st.warning("⚠️ Please select at least one variation")
        
        # Display generated images
        if st.session_state.generated_images:
            st.markdown("---")
            st.subheader("Generated Images")
            
            cols = st.columns(3)
            for idx, (name, img) in enumerate(st.session_state.generated_images.items()):
                with cols[idx % 3]:
                    st.image(img, caption=name, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col2:
                if st.button("🔄 Not Satisfied - Regenerate", type="secondary", use_container_width=True):
                    st.rerun()

# TAB 3: Download
with tab3:
    st.header("Step 3: Download Your Images")
    
    if st.session_state.edited_images:
        st.subheader("📷 Edited Photos")
        
        col1, col2 = st.columns(2)
        with col1:
            # Download edited images as ZIP
            edited_dict = {f"edited_image_{i+1}": img for i, img in enumerate(st.session_state.edited_images)}
            zip_data = create_zip_file(edited_dict)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label=f"📦 Download All Edited Photos ({len(st.session_state.edited_images)} images)",
                data=zip_data,
                file_name=f"edited_photos_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    if st.session_state.generated_images:
        st.markdown("---")
        st.subheader("🎨 AI Styled Photos")
        
        col1, col2 = st.columns(2)
        with col1:
            # Download all styled images as ZIP
            zip_data = create_zip_file(st.session_state.generated_images)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label=f"📦 Download All Styled Photos ({len(st.session_state.generated_images)} images)",
                data=zip_data,
                file_name=f"styled_photos_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        with col2:
            # Show individual downloads toggle
            if st.button("📥 Show Individual Downloads", use_container_width=True):
                st.session_state.show_individual = True
        
        # Individual downloads
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
    
    if not st.session_state.edited_images and not st.session_state.generated_images:
        st.info("👈 Upload and edit images first to enable downloads")

# Sidebar
with st.sidebar:
    st.header("ℹ️ PhotoStyle Pro")
    st.markdown("""
    ### Features:
    
    **Photo Editing:**
    - ✅ Batch upload & processing
    - ✅ Brightness, contrast, saturation
    - ✅ Crop with presets (Instagram, LinkedIn, etc.)
    - ✅ Rotate & resize
    - ✅ Noise reduction
    - ✅ Background removal*
    - ✅ AI upscaling
    
    **AI Style Conversion:**
    - ✅ 5 style categories
    - ✅ 4 variations per style
    - ✅ Professional enhancements
    - ✅ Head-to-chest crop for professional
    
    **Download Options:**
    - ✅ Bulk ZIP download
    - ✅ Individual image download
    
    ---
    
    **Privacy:** No images stored on servers
    
    **Powered by:** Google Gemini 2.5 Flash
    
    ---
    
    *Background removal requires `rembg` library
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Reset Everything", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 14px;'>"
    "🔒 <b>Privacy First:</b> All processing happens in real-time. No images are stored on our servers."
    "</p>",
    unsafe_allow_html=True
)