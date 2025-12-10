st.markdown("---")
    
    # Download prompts documentation
    st.subheader("📄 Prompt Reference")
    st.caption("Allimport streamlit as st
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
if 'working_images' not in st.session_state:
    st.session_state.working_images = []
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
if 'custom_background' not in st.session_state:
    st.session_state.custom_background = None

# Style variations
STYLE_VARIATIONS = {
    "passport": {
        "US Passport": "official US passport photo style, neutral expression, plain white background, head to shoulders visible, centered composition, even lighting, no shadows, professional government document photo",
        "Indian Passport": "official Indian passport photo style, neutral expression, plain white background, 80% face coverage, ears visible, centered composition, even lighting, professional government document photo",
        "UK Passport": "official UK passport photo style, neutral expression, plain light grey background, head to shoulders visible, centered composition, even lighting, no shadows, professional government document photo",
        "EU Passport": "official European Union passport photo style, neutral expression, plain light background, head to shoulders visible, centered composition, even lighting, professional government document photo"
    },
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

def get_prompts_reference_content():
    """Return the complete prompts reference document"""
    return """# PhotoStyle Pro - Complete AI Prompts Reference

**Application:** PhotoStyle Pro  
**AI Model:** Google Gemini 2.5 Flash Image Preview  
**Version:** 1.0 | December 2024

---

## 🛂 PASSPORT PHOTOS

### US Passport
official US passport photo style, neutral expression, plain white background, head to shoulders visible, centered composition, even lighting, no shadows, professional government document photo

### Indian Passport
official Indian passport photo style, neutral expression, plain white background, 80% face coverage, ears visible, centered composition, even lighting, professional government document photo

### UK Passport
official UK passport photo style, neutral expression, plain light grey background, head to shoulders visible, centered composition, even lighting, no shadows, professional government document photo

### EU Passport
official European Union passport photo style, neutral expression, plain light background, head to shoulders visible, centered composition, even lighting, professional government document photo

---

## 💼 PROFESSIONAL PHOTOS

### Corporate Executive
professional corporate executive headshot framed from head to chest level, dark suit, confident expression, modern office background, studio lighting, sharp focus, professional portrait crop

### Creative Professional
professional creative industry headshot framed from head to chest level, smart casual attire, approachable expression, bright modern workspace, natural lighting, professional portrait crop

### LinkedIn Classic
classic professional LinkedIn profile photo framed from head to chest level, business formal attire, neutral background, professional studio portrait, proper headshot framing

### Business Casual
professional business casual style headshot framed from head to chest level, relaxed yet polished, contemporary setting, friendly professional demeanor, proper portrait crop

---

## 🎉 FUN PHOTOS

### Vibrant Pop Art
fun vibrant pop art style, bold bright colors, playful energy, comic book aesthetic, dynamic composition

### Cheerful Cartoon
fun cheerful cartoon illustration style, cute animated look, happy colors, whimsical playful mood

### Festival Vibes
fun festival party vibes, colorful energetic atmosphere, celebration mood, joyful expression, confetti and lights

### Retro Fun
fun retro 80s style, neon colors, playful vintage aesthetic, energetic disco vibes

---

## 🎨 ARTISTIC PHOTOS

### Oil Painting
artistic oil painting masterpiece, rich textures, classical art style, museum quality, painterly brushstrokes

### Watercolor Dream
artistic watercolor painting, soft flowing colors, dreamy ethereal quality, delicate artistic touch

### Digital Art
artistic digital illustration, modern creative style, vibrant artistic interpretation, unique visual design

### Impressionist
artistic impressionist style, loose brushwork, play of light, artistic color palette, Monet-inspired

---

## 📼 VINTAGE PHOTOS

### 1970s Film
vintage 1970s film photography, warm tones, nostalgic film grain, classic retro aesthetic

### Sepia Classic
vintage sepia tone photograph, antique timeless look, historical photography style

### Polaroid Nostalgia
vintage polaroid style, instant film aesthetic, faded colors, nostalgic retro charm

### Black & White Classic
vintage black and white photography, classic film noir style, dramatic contrast, timeless elegance

---

## 🔮 MODERN PHOTOS

### Minimalist Chic
modern minimalist style, clean lines, contemporary aesthetic, simple sophisticated look

### High Fashion
modern high fashion editorial, sleek polished style, contemporary magazine quality

### Urban Contemporary
modern urban contemporary style, city vibes, trendy modern aesthetic, sharp details

### Tech Forward
modern tech-forward style, futuristic clean look, innovative contemporary design

---

## ✨ ENHANCEMENTS

**Hair:** subtle hair enhancement, slightly fill in any thinning areas naturally, maintain original hairstyle and volume

**Skin Smoothing:** smooth flawless skin, reduced wrinkles and fine lines, even skin tone

**Skin Tone Adjustments:**
- Much Darker: deeper, richer skin tone with warm undertones
- Darker: slightly deeper skin tone maintaining natural look
- Lighter: slightly lighter skin tone maintaining natural look
- Much Lighter: lighter, brighter skin tone with luminous quality

**Teeth:** bright white teeth, perfect smile, dental enhancement

**Eyes:** bright clear eyes, enhanced eye color, sparkle and clarity

**Lighting:** professional studio lighting, perfect illumination

**Sharpness:** enhanced sharpness and clarity, crisp details, high definition quality

---

## 🎯 SPECIAL FRAMING

**Passport Photos:**
CRITICAL PASSPORT REQUIREMENTS: Image must show head and top of shoulders only. Face must be centered, looking directly at camera. Neutral expression (no smile). Plain background (white or light grey). No shadows on face or background. Both ears should be visible. Face should occupy 70-80% of frame. Professional government document photo standard. Remove any accessories like hats or sunglasses.

**Professional Photos:**
CRITICAL FRAMING: Image must be framed from head to chest level only (professional headshot crop). Do not show full body. Proper portrait framing with shoulders and upper chest visible.

---

## 🖼️ CUSTOM BACKGROUND

CUSTOM BACKGROUND: Replace the background with the style and setting from the provided custom background image. Keep the person/subject from the original photo but place them in the new background environment. Blend naturally and maintain proper lighting and perspective.

---

## 📋 FINAL PROMPT STRUCTURE

Edit and transform this photo: [STYLE]. [FRAMING]. [ENHANCEMENTS]. [BACKGROUND]. IMPORTANT: Keep all enhancements subtle and natural. The result should look very close to the original photo, just enhanced and polished. Generate a high-quality transformed image.

---

**Total Variations:** 24 (6 categories × 4 variations)  
**Enhancements:** 8 options  
**Model:** gemini-2.5-flash-image-preview  
**Application:** PhotoStyle Pro

---
*End of Document*
"""
    """Check if rembg is installed"""
    try:
        import rembg
        return True
    except ImportError:
        return False

def upscale_image(image, factor=2):
    """Simple upscaling (placeholder - in production use AI upscaler)"""
    width, height = image.size
    new_size = (width * factor, height * factor)
    return image.resize(new_size, Image.Resampling.LANCZOS)

def generate_image_variation(image, style_name, variation_prompt, enhancements=None, custom_background=None):
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
            if enhancements.get('remove_grey'):
                enhancements_list.append("restore natural hair color, remove all grey or white hair completely, vibrant youthful hair color, maintain original natural hair tone, cover grey naturally")
            if enhancements.get('physique'):
                enhancements_list.append("maintain good physique with fit athletic body, toned appearance, healthy body composition, natural fitness look, well-proportioned body shape")
            if enhancements.get('skin'):
                enhancements_list.append("smooth flawless skin, reduced wrinkles and fine lines, even skin tone, no blemishes or imperfections")
            
            # Skin tone adjustment
            skin_tone = enhancements.get('skin_tone', 'Natural')
            if skin_tone != 'Natural':
                tone_map = {
                    'Much Darker': 'deeper, richer skin tone with warm undertones, naturally darker complexion',
                    'Darker': 'slightly deeper skin tone, subtly darker complexion maintaining natural look',
                    'Lighter': 'slightly lighter skin tone, subtly brighter complexion maintaining natural look',
                    'Much Lighter': 'lighter, brighter skin tone with luminous quality, naturally lighter complexion'
                }
                enhancements_list.append(f"adjust skin tone: {tone_map[skin_tone]}, ensure natural appearance and avoid unrealistic changes")
            
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
        elif style_name == "passport":
            framing_text = " CRITICAL PASSPORT REQUIREMENTS: Image must show head and top of shoulders only. Face must be centered, looking directly at camera. Neutral expression (no smile). Plain background (white or light grey). No shadows on face or background. Both ears should be visible. Face should occupy 70-80% of frame. Professional government document photo standard. Remove any accessories like hats or sunglasses."
        
        # Custom background handling
        background_text = ""
        if custom_background is not None:
            background_text = " CUSTOM BACKGROUND: Replace the background with the style and setting from the provided custom background image. Keep the person/subject from the original photo but place them in the new background environment. Blend naturally and maintain proper lighting and perspective."
            
            # Create prompt with custom background
            prompt = f"Edit and transform this photo: {variation_prompt}.{framing_text}{enhancement_text}{background_text} IMPORTANT: Keep the subject from the first image but replace the background with the environment from the second image. Keep all enhancements subtle and natural. Generate a high-quality transformed image."
            
            # Create model instance
            model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
            
            # Generate content with both images
            response = model.generate_content([prompt, image, "Custom background reference:", custom_background])
        else:
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
        # Initialize images on first upload or when count changes
        current_count = len(uploaded_files)
        previous_count = len(st.session_state.original_images)
        
        if current_count != previous_count:
            st.session_state.original_images = [Image.open(f).copy() for f in uploaded_files]
            st.session_state.edited_images = [img.copy() for img in st.session_state.original_images]
            st.session_state.working_images = [img.copy() for img in st.session_state.original_images]
        
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
        
        # Make sure we have a working image for the selected index
        if selected_idx >= len(st.session_state.working_images):
            st.error("Error: Image index out of range. Please refresh the page.")
            st.stop()
        
        current_image = st.session_state.working_images[selected_idx]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Original")
            st.image(st.session_state.original_images[selected_idx], use_container_width=True)
        
        with col2:
            st.subheader("Live Preview (All Edits)")
            preview_placeholder = st.empty()
            preview_placeholder.image(current_image, use_container_width=True)
        
        st.markdown("---")
        
        # Editing tools in expandable sections
        with st.expander("⚙️ Basic Adjustments", expanded=True):
            st.caption("Adjust sliders and changes apply instantly")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                brightness = st.slider("💡 Brightness", 0.5, 2.0, 1.0, 0.1, key=f"bright_{selected_idx}")
                contrast = st.slider("🎭 Contrast", 0.5, 2.0, 1.0, 0.1, key=f"contrast_{selected_idx}")
            
            with col2:
                saturation = st.slider("🌈 Saturation", 0.0, 2.0, 1.0, 0.1, key=f"sat_{selected_idx}")
                sharpness = st.slider("🔪 Sharpness", 0.0, 3.0, 1.0, 0.1, key=f"sharp_{selected_idx}")
            
            with col3:
                # Apply adjustments in real-time
                temp_image = apply_basic_adjustments(
                    st.session_state.edited_images[selected_idx],
                    brightness, contrast, saturation, sharpness
                )
                preview_placeholder.image(temp_image, use_container_width=True)
            
            with col4:
                if st.button("✅ Save Adjustments", key=f"save_basic_{selected_idx}", type="primary"):
                    st.session_state.working_images[selected_idx] = temp_image
                    st.session_state.edited_images[selected_idx] = temp_image
                    st.success("✅ Saved!")
                    st.rerun()
                
                if st.button("↩️ Reset to Original", key=f"reset_{selected_idx}"):
                    st.session_state.working_images[selected_idx] = st.session_state.original_images[selected_idx].copy()
                    st.session_state.edited_images[selected_idx] = st.session_state.original_images[selected_idx].copy()
                    st.success("↩️ Reset!")
                    st.rerun()
        
        with st.expander("✂️ Crop, Rotate & Resize"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                crop_preset = st.selectbox("Crop Preset", list(CROP_PRESETS.keys()), key=f"crop_{selected_idx}")
                rotate_angle = st.slider("Rotate (degrees)", -180, 180, 0, 15, key=f"rotate_{selected_idx}")
            
            with col2:
                resize_percent = st.slider("Resize (%)", 25, 200, 100, 5, key=f"resize_{selected_idx}")
            
            with col3:
                if st.button("🔄 Preview Transform", key=f"preview_transform_{selected_idx}"):
                    temp_edited = st.session_state.working_images[selected_idx].copy()
                    
                    # Apply crop
                    if crop_preset != "Original":
                        temp_edited = crop_image(temp_edited, CROP_PRESETS[crop_preset])
                    
                    # Apply rotation
                    if rotate_angle != 0:
                        temp_edited = rotate_image(temp_edited, rotate_angle)
                    
                    # Apply resize
                    if resize_percent != 100:
                        temp_edited = resize_image(temp_edited, resize_percent)
                    
                    preview_placeholder.image(temp_edited, use_container_width=True)
                
                if st.button("✅ Apply Transform", key=f"apply_transform_{selected_idx}", type="primary"):
                    temp_edited = st.session_state.working_images[selected_idx].copy()
                    
                    # Apply crop
                    if crop_preset != "Original":
                        temp_edited = crop_image(temp_edited, CROP_PRESETS[crop_preset])
                    
                    # Apply rotation
                    if rotate_angle != 0:
                        temp_edited = rotate_image(temp_edited, rotate_angle)
                    
                    # Apply resize
                    if resize_percent != 100:
                        temp_edited = resize_image(temp_edited, resize_percent)
                    
                    st.session_state.working_images[selected_idx] = temp_edited
                    st.session_state.edited_images[selected_idx] = temp_edited
                    preview_placeholder.image(temp_edited, use_container_width=True)
                    st.success("✅ Transform applied!")
        
        with st.expander("🧹 Noise Reduction & Enhancement"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                noise_strength = st.slider("Noise Reduction", 0, 3, 0, key=f"noise_{selected_idx}")
            
            with col2:
                upscale_factor = st.radio("Upscale Resolution", [1, 2, 4], key=f"upscale_{selected_idx}")
            
            with col3:
                if st.button("🔄 Preview Enhancement", key=f"preview_enhance_{selected_idx}"):
                    temp_edited = st.session_state.working_images[selected_idx].copy()
                    
                    if noise_strength > 0:
                        temp_edited = apply_noise_reduction(temp_edited, noise_strength)
                    
                    if upscale_factor > 1:
                        temp_edited = upscale_image(temp_edited, upscale_factor)
                    
                    preview_placeholder.image(temp_edited, use_container_width=True)
                
                if st.button("✅ Apply Enhancement", key=f"enhance_{selected_idx}", type="primary"):
                    temp_edited = st.session_state.working_images[selected_idx].copy()
                    
                    if noise_strength > 0:
                        temp_edited = apply_noise_reduction(temp_edited, noise_strength)
                    
                    if upscale_factor > 1:
                        temp_edited = upscale_image(temp_edited, upscale_factor)
                    
                    st.session_state.working_images[selected_idx] = temp_edited
                    st.session_state.edited_images[selected_idx] = temp_edited
                    preview_placeholder.image(temp_edited, use_container_width=True)
                    st.success("✅ Enhanced!")
        
        # Batch apply
        if len(st.session_state.original_images) > 1:
            st.markdown("---")
            if st.button("🔄 Apply Current Image Settings to All Images", type="primary"):
                with st.spinner("Processing all images..."):
                    for i in range(len(st.session_state.original_images)):
                        if i != selected_idx:  # Skip current image as it's already edited
                            edited = apply_basic_adjustments(
                                st.session_state.working_images[i],
                                brightness, contrast, saturation, sharpness
                            )
                            st.session_state.working_images[i] = edited
                            st.session_state.edited_images[i] = edited
                    st.success(f"✅ Applied to all {len(st.session_state.original_images)} images!")
                    st.rerun()

# TAB 2: Style Conversion
with tab2:
    if not st.session_state.edited_images:
        st.info("👈 Please upload images in the 'Upload & Edit' tab first")
    else:
        st.header("Step 2: AI Style Conversion")
        
        # Custom Background Upload (Full Width - Above Columns)
        st.markdown("### 🖼️ Custom Background (Optional)")
        st.caption("Upload a background image to replace the original background in all generated variations")
        
        custom_bg_file = st.file_uploader(
            "Choose background image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image to use as the background. Your subject will be placed in this environment.",
            key="custom_background_uploader"
        )
        
        if custom_bg_file is not None:
            st.session_state.custom_background = Image.open(custom_bg_file)
            col_bg1, col_bg2 = st.columns([1, 3])
            with col_bg1:
                st.image(st.session_state.custom_background, caption="Custom Background", use_container_width=True)
            with col_bg2:
                st.success("✅ Custom background loaded! This will be used for all generated variations.")
                if st.button("❌ Clear Custom Background", key="clear_custom_bg"):
                    st.session_state.custom_background = None
                    st.rerun()
        else:
            st.session_state.custom_background = None
        
        st.markdown("---")
        
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
            
            st.markdown("---")
            
            # Enhancements
            st.markdown("### ✨ Enhancements")
            enhancements = {}
            enhancements['hair'] = st.checkbox("💇 Subtle Hair Enhancement", value=False)
            enhancements['remove_grey'] = st.checkbox("🎨 Remove Grey Hair", value=False)
            enhancements['physique'] = st.checkbox("💪 Good Physique", value=False)
            enhancements['skin'] = st.checkbox("✨ Skin Smoothing", value=False)
            
            # Skin tone adjustment slider
            skin_tone_adjust = st.select_slider(
                "🎨 Skin Tone Adjustment",
                options=["Much Darker", "Darker", "Natural", "Lighter", "Much Lighter"],
                value="Natural",
                help="Adjust skin tone while maintaining natural appearance"
            )
            enhancements['skin_tone'] = skin_tone_adjust
            
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
                    
                    # Show message about custom background
                    if st.session_state.custom_background is not None:
                        st.info("🖼️ Using custom background for all variations")
                    
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
                                st.session_state.enhancements,
                                st.session_state.custom_background
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
            st.caption("💡 Tip: Right-click on any image to open in new tab or download directly")
            
            # Grid display with download buttons
            cols = st.columns(3)
            for idx, (name, img) in enumerate(st.session_state.generated_images.items()):
                with cols[idx % 3]:
                    # Display image name
                    st.markdown(f"**{name}**")
                    
                    # Convert to base64 for HTML display (no fullscreen button)
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=95)
                    img_byte_arr.seek(0)
                    
                    import base64
                    img_base64 = base64.b64encode(img_byte_arr.read()).decode()
                    
                    # Display using HTML (no fullscreen expansion)
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{img_base64}" style="width:100%; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">',
                        unsafe_allow_html=True
                    )
                    
                    # Individual download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = name.replace(' ', '_')
                    img_byte_arr.seek(0)
                    st.download_button(
                        label="⬇️ Download",
                        data=img_byte_arr,
                        file_name=f"{safe_name}_{timestamp}.jpg",
                        mime="image/jpeg",
                        key=f"download_gen_{idx}",
                        use_container_width=True
                    )
                    
                    st.markdown("")  # Spacing
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col2:
                if st.button("🔄 Not Satisfied - Regenerate", type="secondary", use_container_width=True):
                    # Clear current images and regenerate
                    st.session_state.generated_images = {}
                    
                    with st.spinner("Regenerating all variations..."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total = len(st.session_state.selected_samples) * len(st.session_state.edited_images)
                        count = 0
                        
                        for img_idx, image in enumerate(st.session_state.edited_images):
                            for var_name in st.session_state.selected_samples:
                                status_text.text(f"Regenerating {var_name} for Image {img_idx+1}... ({count+1}/{total})")
                                
                                if var_name not in variations:
                                    continue
                                
                                var_prompt = variations[var_name]
                                generated = generate_image_variation(
                                    image,
                                    selected_style,
                                    var_prompt,
                                    st.session_state.enhancements,
                                    st.session_state.custom_background
                                )
                                
                                if generated:
                                    key = f"img{img_idx+1}_{var_name}"
                                    st.session_state.generated_images[key] = generated
                                
                                count += 1
                                progress_bar.progress(count / total)
                        
                        status_text.empty()
                        progress_bar.empty()
                    
                    st.success(f"✅ Regenerated {len(st.session_state.generated_images)} variations!")
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
    - ✅ AI upscaling
    
    **AI Style Conversion:**
    - ✅ 6 style categories (Passport, Professional, Fun, Artistic, Vintage, Modern)
    - ✅ 24 total variations
    - ✅ Custom background replacement
    - ✅ 10 professional enhancements
    - ✅ Passport photo specifications
    - ✅ Physique & grey hair removal
    
    **Download Options:**
    - ✅ Bulk ZIP download
    - ✅ Individual image download
    
    ---
    
    **Privacy:** No images stored on servers
    
    **Powered by:** Google Gemini 2.5 Flash
    """)
    
    st.markdown("---")
    
    # Download prompts documentation
    st.subheader("📄 Prompt Reference")
    
    prompts_doc = """# PhotoStyle Pro - Complete AI Prompts Reference

**Application:** PhotoStyle Pro - AI-Powered Photo Transformation  
**AI Model:** Google Gemini 2.5 Flash Image Preview (Nano Banana)  
**Document Version:** 1.0  

[Full documentation content - see artifact above]
"""
    
    st.download_button(
        label="📥 Download All Prompts (MD)",
        data=open("prompts_reference.md", "r").read() if os.path.exists("prompts_reference.md") else "# Prompts Reference\n\nSee artifact for full content",
        file_name="PhotoStyle_Pro_Prompts_Reference.md",
        mime="text/markdown",
        help="Download complete prompt reference document",
        use_container_width=True
    )
    
    st.caption("💡 Contains all 24 style variations, enhancements, and usage guide")
    
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