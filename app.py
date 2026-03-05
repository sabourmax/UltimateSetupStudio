import streamlit as st
from google import genai
from PIL import Image

# --- Web App UI Setup ---
st.set_page_config(page_title="Ultimate Setup Studio", page_icon="🖥️", layout="wide")
st.title("🖥️ Ultimate Setup Studio")
st.markdown("**Created by Sajjad SABOUR**")
st.markdown("*Version 0.3*")
st.write("Upload your product, dial in your staging, and generate a photorealistic Nano Banana prompt.")

st.divider()

# --- Initialize Session State for Editable Prompt ---
if "generated_prompt" not in st.session_state:
    st.session_state.generated_prompt = ""

# --- Setup the API Client ---
try:
    api_key = st.secrets["API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("API Key not found! Please add it to your Streamlit Settings > Secrets.")
    st.stop()

def get_closest_aspect_ratio_tag(width, height):
    ratio = width / height
    if ratio >= 1.5: return "--ar 16:9"
    elif ratio >= 1.1: return "--ar 4:3"
    elif ratio <= 0.6: return "--ar 9:16"
    elif ratio <= 0.9: return "--ar 3:4"
    else: return "--ar 1:1"

# ==========================================
# PRO CONTROLS & PROMPT GENERATION
# ==========================================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("### 📝 Core Settings")
    
    input_mode = st.radio(
        "1. Select Upload Mode:", 
        [
            "🧊 Mode 1: Simple 3D Model (Strict 1:1 Match, Upgrades Textures/Lighting)", 
            "📸 Mode 2: Existing Photo / Render (Advanced Staging & Environment)"
        ]
    )
    
    uploaded_file = st.file_uploader("2. Upload Product Image (Desk/Chair):", type=["jpg", "jpeg", "png"])
    
    desk_setup = st.text_input(
        "3. Desk Setup & Accessories (Optional):", 
        placeholder="e.g., Add a dual-monitor PC setup... (Leave empty to keep surfaces bare)"
    )

    # Initialize variables to avoid errors in Mode 1
    environment = ""
    uploaded_character = None
    character_details = ""
    
    # DYNAMIC UI: Only show Environment and Character controls in Mode 2
    if "Mode 2" in input_mode:
        environment = st.text_input(
            "4. Environment / Background (Optional):", 
            placeholder="e.g., A sunlit home office... (Leave empty for a clean minimal space)"
        )
        
        st.markdown("### 🧍 Character Injection (Optional)")
        uploaded_character = st.file_uploader("Upload Character Reference Image:", type=["jpg", "jpeg", "png"])
        character_details = st.text_input("Character Details & Pose:", placeholder="e.g., Sitting at the desk typing on a laptop, professional attire...")

with col2:
    # DYNAMIC UI: Only show Camera controls in Mode 2
    if "Mode 2" in input_mode:
        st.markdown("### ⚙️ Camera & Lighting Controls")
        
        selected_ar = st.selectbox(
            "Aspect Ratio:", 
            ["Match Uploaded Image", "16:9", "9:16", "4:3", "3:4", "1:1"]
        )
        
        selected_lens = st.selectbox(
            "Camera Lens:", 
            [
                "Let the AI decide",
                "14mm Ultra-Wide (Shows the whole room and desk setup)",
                "35mm Standard Cinematic (Natural human perspective)",
                "50mm Portrait (Focuses closely on the desk/chair)",
                "Macro Lens (Extreme close-up detail)"
            ]
        )
        
        selected_dof = st.selectbox(
            "Depth of Field (Bokeh):", 
            [
                "Let the AI decide",
                "Shallow DOF (Product is crisp, background office is blurry)",
                "Deep Focus / f/16 (Everything is perfectly in focus for catalogs)"
            ]
        )
        
        selected_lighting = st.selectbox(
            "Lighting Setup:",
            [
                "Let the AI decide",
                "Commercial Product Studio Lighting",
                "Cinematic Studio Lighting",
                "Volumetric Fog / God Rays",
                "Moody / Low Key Lighting",
                "Bright Natural Sunlight"
            ]
        )
    else:
        st.markdown("### 🔒 Mode 1 Active")
        st.info("**Strict 1:1 Match Enabled.**\n\nCamera lens, depth of field, background, and character controls are hidden. The AI is locked to explicitly match your reference image's camera angle and simple background.")
        # Set defaults for Mode 1 behind the scenes
        selected_ar = "Match Uploaded Image"
        selected_lens = "Standard product photography lens"
        selected_dof = "Deep Focus"
        selected_lighting = "Clean commercial studio lighting"

if st.button("Generate Master Prompt ✨", type="primary"):
    if not uploaded_file:
        st.warning("Please upload a primary product image first!")
    else:
        with st.spinner("Analyzing geometry and locking structure..."):
            try:
                img = Image.open(uploaded_file)
                
                if selected_ar == "Match Uploaded Image":
                    final_ar_tag = get_closest_aspect_ratio_tag(img.width, img.height)
                    st.info(f"Detected image proportions. Appending aspect ratio: **{final_ar_tag}**.")
                else:
                    final_ar_tag = f"--ar {selected_ar}"

                if "Mode 1" in input_mode:
                    # --- MODE 1: ULTRA-STRICT LOCKS ---
                    mandatory_prefix = "Ultra-realistic photograph, EXACT 1:1 GEOMETRY MATCH to reference, IDENTICAL CAMERA ANGLE AND PERSPECTIVE, SIMPLE BACKGROUND matching reference, ZERO new geometrical forms, "
                    
                    if desk_setup:
                        mandatory_prefix += f"adding ONLY these objects: {desk_setup}, "
                    else:
                        mandatory_prefix += "BARE SURFACES, absolutely ZERO added objects, NO extra clutter, NO props, "

                    instruction = (
                        f"Act as an expert commercial photography director. Analyze the attached 3D blockout.\n\n"
                        f"CRITICAL RULE: You MUST start your generated prompt EXACTLY with this phrase word-for-word:\n"
                        f"\"{mandatory_prefix}\"\n\n"
                        f"After typing that exact phrase, continue the prompt by describing the premium photorealistic materials of the existing desk/chair and clean studio lighting.\n"
                        f"DO NOT change the perspective or camera angle. DO NOT add a complex background. DO NOT add characters.\n"
                        f"Write everything as a sparse, comma-separated list of keywords. DO NOT write full sentences. DO NOT use the words 'render', '3D', or 'octane'."
                    )
                    api_contents = [instruction, img]

                else:
                    # --- MODE 2: CREATIVE STAGING ---
                    mandatory_prefix = "Ultra-realistic photograph, EXACT 1:1 GEOMETRY MATCH to reference, identical original 3D structure, ZERO new geometrical forms, "
                    
                    if desk_setup:
                        mandatory_prefix += f"adding ONLY these objects: {desk_setup}, "
                    else:
                        mandatory_prefix += "BARE SURFACES, absolutely ZERO added objects, NO extra clutter, NO props, "

                    base_env = "modern, minimal, clean commercial space"
                    if environment:
                        env_instruction = f"Environment: {environment} integrated into a {base_env}."
                    else:
                        env_instruction = f"Environment: clean, empty, {base_env} studio background."

                    char_instruction = ""
                    if uploaded_character or character_details:
                        char_instruction = f"Feature a highly realistic human character. "
                        if character_details:
                            char_instruction += f"Pose/Details: '{character_details}'. "
                        if uploaded_character:
                            char_instruction += "Match the character's face/appearance to the SECOND reference image. "

                    instruction = (
                        f"Act as an expert commercial photography director. Analyze the attached image(s).\n\n"
                        f"CRITICAL RULE: You MUST start your generated prompt EXACTLY with this phrase word-for-word:\n"
                        f"\"{mandatory_prefix}\"\n\n"
                        f"After typing that exact phrase, continue the prompt by describing the premium materials of the existing desk/chair, the lighting ({selected_lighting}), the camera lens ({selected_lens}), depth of field ({selected_dof}), and the environment ({env_instruction}).\n"
                        f"{char_instruction}\n"
                        f"Write everything as a sparse, comma-separated list of keywords. DO NOT write full sentences. DO NOT use the words 'render', '3D', or 'octane'. Describe it as a real physical photograph."
                    )
                    
                    api_contents = [instruction, img]
                    if uploaded_character:
                        char_img = Image.open(uploaded_character)
                        api_contents.append(char_img)
                
                # Model execution
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=api_contents
                )
                
                st.session_state.generated_prompt = f"{response.text.strip()} {final_ar_tag}"
                
            except Exception as e:
                st.error(f"Error generating prompt: {e}")

# --- EDITABLE PROMPT SECTION ---
if st.session_state.generated_prompt:
    st.divider()
    st.subheader("✏️ Review and Edit")
    
    edited_prompt = st.text_area("Tweak your Ultimate Setup prompt here:", value=st.session_state.generated_prompt, height=150)
    
    st.success("Ready! Click the copy icon in the top right corner of the box below:")
    st.code(edited_prompt, language="text")
