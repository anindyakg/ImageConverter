import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import zipfile
from datetime import datetime
import numpy as np
from PIL import ImageOps

# Import authentication
from simple_auth import SimpleAuthenticator

# Page config
st.set_page_config(
    page_title="Photo Style Converter Pro",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# AUTHENTICATION
# ============================================
# Initialize authenticator
auth = SimpleAuthenticator(credentials_file='users.json')

# Require authentication - if not logged in, show login page
if not auth.require_authentication():
    st.stop()

# Show user info in sidebar (will be added at the end)
# auth.show_user_info(location='sidebar')

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
if 'model_photo' not in st.session_state:
    st.session_state.model_photo = None
if 'detected_ages' not in st.session_state:
    st.session_state.detected_ages = {}
if 'uploader_key' not in st.session_state:
    import time
    st.session_state.uploader_key = int(time.time())

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

def convert_to_rgb(image):
    """Convert image to RGB mode for JPEG compatibility"""
    if image.mode == 'RGBA':
        # Create white background and paste image with alpha mask
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        return rgb_image
    elif image.mode not in ('RGB', 'L'):
        # Convert any other mode to RGB
        return image.convert('RGB')
    return image

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

def check_rembg_available():
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

def generate_model_clone(input_image, model_photo):
    """Generate a new photo of the person from input image, modeled after the reference photo
    
    Uses a descriptive approach to preserve identity while copying attributes
    """
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
    
    if not api_key:
        st.error("⚠️ Google API key not found.")
        return None
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Prompt with strong negative instructions
        prompt = """Create a photo composite by following these instructions:

STEP 1 - IDENTIFY THE PERSON (IMAGE 1):
The first image shows the person whose identity must be preserved. Study their:
- Face shape, eyes, nose, mouth, chin, eyebrows
- Hair color, style, and length
- Skin tone and age
- All unique facial characteristics

STEP 2 - IDENTIFY ATTRIBUTES TO COPY (IMAGE 2):
The second image is just a STYLE REFERENCE. Extract only these attributes:
- Clothing and outfit
- Body pose and stance
- Facial expression type (smile, neutral, etc.)
- Background setting
- Lighting and photography style
- Camera angle

STEP 3 - GENERATE THE OUTPUT:
Create a photorealistic image where:

✅ KEEP (from IMAGE 1):
- The EXACT same face as IMAGE 1
- Same facial structure and features as IMAGE 1
- Same hair as IMAGE 1
- Same skin tone as IMAGE 1
- Person must be IDENTIFIABLE as the person from IMAGE 1

✅ APPLY (from IMAGE 2):
- Wear the same clothes as IMAGE 2
- Same body pose as IMAGE 2
- Same type of expression as IMAGE 2
- Similar background as IMAGE 2
- Same lighting style as IMAGE 2

❌ DO NOT (Critical Restrictions):
- DO NOT use the face from IMAGE 2
- DO NOT copy facial features from IMAGE 2
- DO NOT change the person's identity from IMAGE 1
- DO NOT make the person from IMAGE 1 look like the person from IMAGE 2
- DO NOT perform a face swap
- DO NOT blend the two faces together
- The output face MUST match IMAGE 1, NOT IMAGE 2

FINAL CHECK:
Ask yourself: "Can I recognize this as the same person from IMAGE 1?"
If NO, you have failed. The face MUST be from IMAGE 1.

Think of this as: Photographing the person from IMAGE 1 while they wear the outfit from IMAGE 2, strike the pose from IMAGE 2, and have a similar expression to IMAGE 2.

Generate a high-quality, photorealistic image."""
        
        # Create model instance
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Configure safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]
        
        # Generate with very explicit labeling
        response = model.generate_content(
            [
                prompt,
                "IMAGE 1 - THE PERSON (Use this person's face in the output. This face must be preserved exactly):",
                input_image,
                "IMAGE 2 - STYLE REFERENCE ONLY (Copy clothes, pose, expression. DO NOT use this person's face):",
                model_photo
            ],
            safety_settings=safety_settings
        )
        
        # Check for generated image in response
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Extract the generated image
                    image_data = part.inline_data.data
                    processed_image = Image.open(io.BytesIO(image_data))
                    # Convert to RGB
                    processed_image = convert_to_rgb(processed_image)
                    return processed_image
        
        # If no image returned, show error
        st.error("⚠️ AI did not generate an image. Try again or use a different model photo.")
        return None
        
    except Exception as e:
        st.error(f"❌ Clone generation error: {str(e)}")
        return None

def generate_image_variation(image, style_name, variation_prompt, enhancements=None, custom_background=None, preserve_age=True, target_age=None, detected_age=None):
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
            if enhancements.get('remove_grey_hair'):
                enhancements_list.append("restore natural hair color by removing all grey/white hair, convert grey hair to natural darker color that matches the person's original hair color, maintain realistic hair texture and appearance, keep hairstyle unchanged")
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
        
        # Age transformation handling
        age_text = ""
        if preserve_age and detected_age:
            age_text = f" The person should appear to be approximately {detected_age} years old, maintaining the same age appearance as in the original photo."
        elif not preserve_age and target_age and target_age != "Same Age (No Change)":
            age_map = {
                "Child (5-12 years)": "Transform the person to appear as a child (5-12 years old) with youthful, childlike features and smooth skin",
                "Teenager (13-19 years)": "Transform the person to appear as a teenager (13-19 years old) with adolescent features and youthful appearance",
                "Young Adult (20-30 years)": "Transform the person to appear as a young adult (20-30 years old) with mature but youthful features",
                "Adult (31-45 years)": "Transform the person to appear as an adult (31-45 years old) with fully mature features",
                "Middle Age (46-60 years)": "Transform the person to appear middle-aged (46-60 years old) with some visible aging signs",
                "Senior (61-75 years)": "Transform the person to appear as a senior (61-75 years old) with clear aging signs and grey hair",
                "Elderly (76+ years)": "Transform the person to appear elderly (76+ years old) with pronounced aging features and white hair"
            }
            if target_age in age_map:
                age_text = f" {age_map[target_age]}."
        
        framing_text = ""
        if style_name == "professional":
            framing_text = " Frame from head to chest (professional headshot). Include shoulders and upper chest."
        elif style_name == "passport":
            framing_text = " Passport photo format: head and top of shoulders only, face centered, neutral expression, plain background."
        
        # Custom background handling
        background_text = ""
        if custom_background is not None:
            background_text = " Replace the background with the environment from the custom background image provided."
            
            # Check if model photo is provided
            model_photo_text = ""
            has_model_photo = st.session_state.model_photo is not None
            
            if has_model_photo:
                model_photo_text = " Match the style, lighting, color grading, and overall aesthetic of the reference model photo provided."
            
            # Create prompt with custom background
            prompt = f"Transform this photo: {variation_prompt}.{framing_text}{age_text}{enhancement_text}{background_text}{model_photo_text} Keep changes natural and subtle. Generate high-quality image."
            
            # Create model instance
            model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
            
            # Configure safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
            
            # Generate content with images (include model photo if available)
            content_parts = [prompt, image, "Custom background reference:", custom_background]
            if has_model_photo:
                content_parts.extend(["Style reference (model photo):", st.session_state.model_photo])
            
            response = model.generate_content(
                content_parts,
                safety_settings=safety_settings
            )
        else:
            # Check if model photo is provided
            model_photo_text = ""
            has_model_photo = st.session_state.model_photo is not None
            
            if has_model_photo:
                model_photo_text = " Match the style, lighting, color grading, and overall aesthetic of the reference model photo provided."
            
            prompt = f"Transform this photo: {variation_prompt}.{framing_text}{age_text}{enhancement_text}{model_photo_text} Keep changes subtle and natural. Generate high-quality image."
            
            # Create model instance
            model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
            
            # Configure safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
            
            # Generate content (include model photo if available)
            content_parts = [prompt, image]
            if has_model_photo:
                content_parts.extend(["Style reference (model photo):", st.session_state.model_photo])
            
            response = model.generate_content(content_parts, safety_settings=safety_settings)
        
        # Check for generated image in response
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Extract the generated image
                    image_data = part.inline_data.data
                    processed_image = Image.open(io.BytesIO(image_data))
                    # Convert to RGB to avoid RGBA/JPEG issues
                    processed_image = convert_to_rgb(processed_image)
                    return processed_image
        
        # Safe text response handling
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            st.caption(f"AI Response: {part.text[:150]}...")
                            break
                elif hasattr(candidate, 'finish_reason'):
                    st.warning(f"⚠️ Generation blocked. Reason: {candidate.finish_reason}")
        except Exception as e:
            st.warning(f"⚠️ Could not process response: {str(e)}")
        
        # Fallback: return original
        st.warning("⚠️ No image generated. Returning original photo.")
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

def detect_age_from_image(image):
    """Detect approximate age from image using Gemini Vision"""
    try:
        # Use the same API key as image generation
        api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            st.warning("⚠️ Google API key not found for age detection")
            return None
        
        genai.configure(api_key=api_key)
        
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        
        # Convert to RGB for JPEG compatibility
        image = convert_to_rgb(image)
        
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Create model instance
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        prompt = """Analyze this photo and estimate the person's age. Respond with ONLY a number representing the estimated age in years. 
        For example, if the person appears to be in their early 30s, respond with just: 32
        If there are multiple people, estimate the age of the primary/central person.
        Be as accurate as possible based on facial features, skin texture, and overall appearance."""
        
        # Upload image
        uploaded_file = genai.upload_file(img_byte_arr, mime_type="image/jpeg")
        
        # Configure safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]
        
        # Generate response
        response = model.generate_content([prompt, uploaded_file], safety_settings=safety_settings)
        
        # Clean up uploaded file
        genai.delete_file(uploaded_file.name)
        
        # Safely extract age from response
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            age_text = part.text.strip()
                            # Extract first number found
                            import re
                            age_match = re.search(r'\d+', age_text)
                            if age_match:
                                return int(age_match.group())
        except:
            pass
        
        return None
        
    except Exception as e:
        st.warning(f"Could not detect age: {str(e)}")
        return None

def get_age_range(age):
    """Convert age to age range category"""
    if age is None:
        return "Unknown"
    
    if age < 5:
        return "Infant (0-4 years)"
    elif age <= 12:
        return "Child (5-12 years)"
    elif age <= 19:
        return "Teenager (13-19 years)"
    elif age <= 30:
        return "Young Adult (20-30 years)"
    elif age <= 45:
        return "Adult (31-45 years)"
    elif age <= 60:
        return "Middle Age (46-60 years)"
    elif age <= 75:
        return "Senior (61-75 years)"
    else:
        return "Elderly (76+ years)"

def create_zip_file(images_dict):
    """Create ZIP file with all images"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, image in images_dict.items():
            img_buffer = io.BytesIO()
            
            # Convert to RGB for JPEG compatibility
            image = convert_to_rgb(image)
            
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
    username = auth.get_username()
    st.markdown(f"Professional Photo Editor & AI Style Converter | Welcome, **{username}**! 👋")

with col_header2:
    st.markdown("")
    if st.button("🔄 Start Over", type="secondary", use_container_width=True):
        # Save authentication state before clearing
        is_authenticated = st.session_state.get('authenticated', False)
        current_username = st.session_state.get('username', None)
        current_login_time = st.session_state.get('login_time', None)
        
        # Only proceed if user is authenticated
        if is_authenticated:
            # Clear Streamlit cache
            st.cache_data.clear()
            st.cache_resource.clear()
            
            # Clear all session state
            st.session_state.clear()
            
            # Restore authentication state
            st.session_state.authenticated = True
            st.session_state.username = current_username
            st.session_state.login_time = current_login_time
            
            # Force new uploader key
            import time
            st.session_state.uploader_key = int(time.time())
            
            st.rerun()

st.markdown("---")

# Main tabs - add admin tab for admin users
if st.session_state.username == 'admin':
    tab1, tab2, tab3, tab_admin = st.tabs(["📤 Upload & Edit", "🎨 Style Conversion", "📥 Download", "👑 Admin Panel"])
else:
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Edit", "🎨 Style Conversion", "📥 Download"])

# TAB 1: Upload & Edit
with tab1:
    st.header("Step 1: Upload and Edit Photos")
    
    # Batch upload
    uploaded_files = st.file_uploader(
        "Upload one or multiple photos",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Upload multiple images for batch processing",
        key=f"main_uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_files:
        # Initialize images on first upload or when count changes
        current_count = len(uploaded_files)
        previous_count = len(st.session_state.original_images)
        
        if current_count != previous_count:
            # Open images and convert to RGB to avoid RGBA/JPEG issues
            st.session_state.original_images = [convert_to_rgb(Image.open(f)) for f in uploaded_files]
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
            key=f"custom_background_uploader_{st.session_state.uploader_key}"
        )
        
        if custom_bg_file is not None:
            st.session_state.custom_background = convert_to_rgb(Image.open(custom_bg_file))
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
        
        # Model Photo Upload (NEW FEATURE)
        st.markdown("### 🎭 Model Photo (Optional)")
        st.caption("Upload a reference photo to clone or apply its style to your images")
        
        model_photo_file = st.file_uploader(
            "Choose model/reference photo",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a photo to clone or use as style reference",
            key=f"model_photo_uploader_{st.session_state.uploader_key}"
        )
        
        if model_photo_file is not None:
            st.session_state.model_photo = convert_to_rgb(Image.open(model_photo_file))
            col_model1, col_model2 = st.columns([1, 3])
            with col_model1:
                st.image(st.session_state.model_photo, caption="Model Photo", use_container_width=True)
            with col_model2:
                # Add clone mode checkbox
                st.session_state.clone_mode = st.checkbox(
                    "🎯 **Clone Mode** - Recreate your photo based on model",
                    value=st.session_state.get('clone_mode', False),
                    help="Your face stays the same, but you'll wear the model's clothes, pose, and expression",
                    key="clone_mode_checkbox"
                )
                
                if st.session_state.clone_mode:
                    st.success("✅ **Clone Mode Active!**")
                    st.warning("**Your photo will be recreated with:**\n- ✅ **Your face** (preserved)\n- 👔 **Model's clothes** (copied)\n- 🧍 **Model's pose** (copied)\n- 😊 **Model's smile/expression** (copied)\n- 🎨 **Model's style** (copied)\n\n⚠️ All style categories will be bypassed!")
                else:
                    st.success("✅ Model photo loaded! Will apply style to your images.")
                    st.info("**Style Mode:**\n- Analyze model's style and characteristics\n- Apply similar lighting and color grading\n- Match overall aesthetic\n- Your original pose/clothes preserved")
                
                if st.button("❌ Clear Model Photo", key="clear_model_photo"):
                    st.session_state.model_photo = None
                    st.session_state.clone_mode = False
                    st.rerun()
        else:
            st.session_state.model_photo = None
            st.session_state.clone_mode = False
        
        st.markdown("---")
        
        # Age Detection and Control Section
        st.markdown("### 👤 Age Settings")
        
        # Initialize detection flag
        if 'detecting_age' not in st.session_state:
            st.session_state.detecting_age = False
        
        # Detect age button
        if st.button("🔍 Detect Age from Photos", use_container_width=True):
            st.session_state.detecting_age = True
            st.rerun()
        
        # Process detection if flag is set
        if st.session_state.detecting_age:
            detected_count = 0
            
            with st.spinner("Analyzing age from photos..."):
                for idx, image in enumerate(st.session_state.edited_images):
                    detected_age = detect_age_from_image(image)
                    if detected_age:
                        st.session_state.detected_ages[idx] = detected_age
                        detected_count += 1
            
            # Reset flag
            st.session_state.detecting_age = False
            
            # Show result message
            if detected_count > 0:
                st.success(f"✅ Age detected for {detected_count} photo(s)")
            else:
                st.error("❌ Could not detect age from any photos. Please check your API key.")
        
        # Display detected ages
        if st.session_state.detected_ages:
            st.markdown("---")
            st.markdown("**🎂 Detected Ages:**")
            for idx, age in st.session_state.detected_ages.items():
                age_range = get_age_range(age)
                st.info(f"**Photo {idx+1}:** ~{age} years old ({age_range})")
            st.markdown("---")

        
        # Age transformation options
        col_age_opt1, col_age_opt2 = st.columns(2)
        
        with col_age_opt1:
            preserve_age = st.checkbox(
                "✅ Preserve Original Age",
                value=True,
                help="Generated images will maintain the same age as the original photo"
            )
        
        with col_age_opt2:
            if not preserve_age:
                target_age = st.selectbox(
                    "🎂 Transform to Age Range:",
                    options=[
                        "Same Age (No Change)",
                        "Child (5-12 years)",
                        "Teenager (13-19 years)", 
                        "Young Adult (20-30 years)",
                        "Adult (31-45 years)",
                        "Middle Age (46-60 years)",
                        "Senior (61-75 years)",
                        "Elderly (76+ years)"
                    ],
                    index=0,
                    help="Transform the person to a different age range"
                )
            else:
                target_age = None
        
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
            enhancements['remove_grey_hair'] = st.checkbox("💇 Remove Grey Hair", value=False)
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
            
            # Clone Mode Button (if model photo and clone mode enabled)
            if st.session_state.get('clone_mode', False) and st.session_state.model_photo is not None:
                st.markdown("---")
                st.markdown("### 🎯 Clone Model Attributes")
                st.info("**Clone Mode Active:** Your person will be recreated wearing the model's clothes, in the model's pose, with the model's smile/expression")
                
                if st.button("🎯 Generate with Model Attributes", type="primary", use_container_width=True, key="generate_clones"):
                    st.session_state.generated_images = {}
                    
                    st.warning("🎯 Recreating your person with model's attributes...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total = len(st.session_state.edited_images)
                    
                    for img_idx, image in enumerate(st.session_state.edited_images):
                        status_text.text(f"Applying model attributes to Image {img_idx+1}... ({img_idx+1}/{total})")
                        
                        # Generate clone with special prompt
                        generated = generate_model_clone(
                            image,
                            st.session_state.model_photo
                        )
                        
                        if generated:
                            key = f"img{img_idx+1}_model_clone"
                            st.session_state.generated_images[key] = generated
                        
                        progress_bar.progress((img_idx + 1) / total)
                    
                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ Generated {len(st.session_state.generated_images)} photos with model attributes!")
                    st.balloons()
            
            # Normal variation generation (only if NOT in clone mode)
            elif len(st.session_state.selected_samples) > 0:
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
                            
                            # Get age parameters
                            detected_age = st.session_state.detected_ages.get(img_idx)
                            
                            generated = generate_image_variation(
                                image,
                                selected_style,
                                var_prompt,
                                st.session_state.enhancements,
                                st.session_state.custom_background,
                                preserve_age,
                                target_age,
                                detected_age
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
                    
                    # Convert to RGB for JPEG compatibility
                    display_img = convert_to_rgb(img)
                    
                    display_img.save(img_byte_arr, format='JPEG', quality=95)
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
                                
                                # Get age parameters
                                detected_age = st.session_state.detected_ages.get(img_idx)
                                
                                generated = generate_image_variation(
                                    image,
                                    selected_style,
                                    var_prompt,
                                    st.session_state.enhancements,
                                    st.session_state.custom_background,
                                    preserve_age,
                                    target_age,
                                    detected_age
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
                
                # Convert to RGB for JPEG compatibility
                download_img = convert_to_rgb(img)
                
                download_img.save(img_buffer, format='JPEG', quality=95)
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

# TAB 4: Admin Panel (only visible to admin)
if st.session_state.username == 'admin':
    with tab_admin:
        st.header("👑 Admin Panel - User Management")
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: white; margin: 0;'>🔧 Administrator Tools</h3>
            <p style='color: #f0f0f0; margin: 5px 0 0 0; font-size: 0.9em;'>
                Create and manage user accounts with time-bound or permanent access
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Two columns for admin functions
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("➕ Create New User")
            
            with st.form("create_user_form"):
                new_username = st.text_input("Username", placeholder="e.g., trial_user1")
                new_password = st.text_input("Password", type="password", placeholder="Secure password")
                
                account_type = st.radio(
                    "Account Type",
                    ["Temporary (Trial)", "Permanent"],
                    help="Trial accounts expire after specified hours"
                )
                
                if account_type == "Temporary (Trial)":
                    trial_minutes = st.number_input(
                        "Trial Duration (minutes)",
                        min_value=10,
                        max_value=43200,  # 30 days max
                        value=120,  # Default 2 hours = 120 minutes
                        step=10,  # 10-minute increments
                        help="How many minutes until account expires (increments of 10 minutes)"
                    )
                    trial_hours = trial_minutes / 60  # Convert to hours for the function
                else:
                    trial_hours = None
                
                submit_create = st.form_submit_button("✅ Create User", use_container_width=True, type="primary")
                
                if submit_create:
                    if not new_username or not new_password:
                        st.error("❌ Please provide both username and password")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        try:
                            if account_type == "Temporary (Trial)":
                                success, message, expiry = auth.add_trial_user(
                                    new_username, 
                                    new_password, 
                                    trial_hours=trial_hours
                                )
                            else:
                                success, message, expiry = auth.add_user(
                                    new_username, 
                                    new_password, 
                                    expiry_hours=None
                                )
                            
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ Error creating user: {str(e)}")
        
        with col_right:
            st.subheader("⏰ Extend User Account")
            
            # Get list of users with expiry
            users_with_expiry = []
            try:
                for username in auth.credentials.keys():
                    try:
                        info = auth.get_account_info(username)
                        if info and info['has_expiry'] and not info['is_expired']:
                            users_with_expiry.append(username)
                    except Exception as e:
                        # Skip users with format issues
                        continue
            except Exception as e:
                st.error(f"Error loading users: {str(e)}")
            
            if users_with_expiry:
                with st.form("extend_user_form"):
                    extend_username = st.selectbox(
                        "Select User to Extend",
                        users_with_expiry,
                        help="Only shows users with active trial accounts"
                    )
                    
                    # Show current expiry
                    if extend_username:
                        try:
                            user_info = auth.get_account_info(extend_username)
                            st.info(f"**Current Status:**\n\n"
                                   f"⏰ Time remaining: {user_info['time_remaining']}\n\n"
                                   f"📅 Expires: {user_info['expiry_time']}")
                        except Exception as e:
                            st.warning(f"Could not load user info: {str(e)}")
                    
                    extend_minutes = st.number_input(
                        "Additional Minutes",
                        min_value=10,
                        max_value=10080,  # 7 days max
                        value=120,  # Default 2 hours
                        step=10,  # 10-minute increments
                        help="How many minutes to add to current expiration (increments of 10 minutes)"
                    )
                    extend_hours = extend_minutes / 60  # Convert to hours
                    
                    submit_extend = st.form_submit_button("⏰ Extend Account", use_container_width=True, type="primary")
                    
                    if submit_extend:
                        try:
                            success, message = auth.extend_account(extend_username, extend_hours)
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ Error extending account: {str(e)}")
            else:
                st.info("ℹ️ No active trial accounts to extend")
        
        st.markdown("---")
        
        # User list section
        st.subheader("👥 All Users")
        
        # Get all users
        all_users = []
        try:
            for username in auth.credentials.keys():
                try:
                    info = auth.get_account_info(username)
                    if info:
                        all_users.append(info)
                except Exception as e:
                    # Skip users with issues and show warning
                    st.warning(f"⚠️ Could not load info for user '{username}': {str(e)}")
                    continue
        except Exception as e:
            st.error(f"Error loading user list: {str(e)}")
        
        if all_users:
            # Create a table view
            st.markdown("**Active Users:**")
            
            for user_info in all_users:
                with st.expander(f"👤 {user_info['username']}", expanded=False):
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.markdown(f"**Account Type:**")
                        if user_info['has_expiry']:
                            st.markdown("🕐 Temporary (Trial)")
                        else:
                            st.markdown("✨ Permanent")
                    
                    with col_info2:
                        st.markdown(f"**Status:**")
                        if user_info['is_expired']:
                            st.markdown("❌ **EXPIRED**")
                        elif user_info['has_expiry']:
                            st.markdown(f"✅ Active ({user_info['time_remaining']} left)")
                        else:
                            st.markdown("✅ Active (No expiry)")
                    
                    if user_info['has_expiry']:
                        st.markdown(f"**Expiry Date:** {user_info['expiry_time']}")
                    else:
                        st.markdown(f"**Expiry Date:** Never")
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("📊 Quick Statistics")
        
        try:
            total_users = len(auth.credentials)
            trial_users = len([u for u in all_users if u['has_expiry']])
            permanent_users = total_users - trial_users
            expired_users = len([u for u in all_users if u['is_expired']])
            active_trial_users = len([u for u in all_users if u['has_expiry'] and not u['is_expired']])
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Total Users", total_users)
            
            with col_stat2:
                st.metric("Active Trials", active_trial_users)
            
            with col_stat3:
                st.metric("Permanent", permanent_users)
            
            with col_stat4:
                st.metric("Expired", expired_users)
        except Exception as e:
            st.error(f"Error calculating statistics: {str(e)}")
        
        st.markdown("---")
        st.info("💡 **Tip:** Trial accounts automatically expire and users will see an error message when trying to log in after expiration.")

# Sidebar
with st.sidebar:
    # Show authenticated user info
    auth.show_user_info(location='sidebar')
    
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
    - ✅ 4 variations per style
    - ✅ Custom background replacement
    - ✅ Professional enhancements
    - ✅ Remove grey hair option
    - ✅ AI age detection
    - ✅ Age preservation or transformation
    - ✅ Passport photo specifications
    - ✅ Head-to-chest crop for professional
    
    **Download Options:**
    - ✅ Bulk ZIP download
    - ✅ Individual image download
    
    ---
    
    **Privacy:** No images stored on servers
    
    **Powered by:** Google Gemini 2.5 Flash
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Reset Everything", use_container_width=True, type="primary"):
        # Save authentication state before clearing
        is_authenticated = st.session_state.get('authenticated', False)
        current_username = st.session_state.get('username', None)
        current_login_time = st.session_state.get('login_time', None)
        
        # Only proceed if user is authenticated
        if is_authenticated:
            # Clear Streamlit cache
            st.cache_data.clear()
            st.cache_resource.clear()
            
            # Clear all session state
            st.session_state.clear()
            
            # Restore authentication state
            st.session_state.authenticated = True
            st.session_state.username = current_username
            st.session_state.login_time = current_login_time
            
            # Force new uploader key
            import time
            st.session_state.uploader_key = int(time.time())
            
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 14px;'>"
    "🔒 <b>Privacy First:</b> All processing happens in real-time. No images are stored on our servers."
    "</p>",
    unsafe_allow_html=True
)