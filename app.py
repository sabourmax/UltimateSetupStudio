import streamlit as st
from google import genai
from PIL import Image

# --- Web App UI Setup ---
st.set_page_config(page_title="Ultimate Setup Studio", page_icon="🖥️", layout="wide")
st.title("🖥️ Ultimate Setup Studio")
st.markdown("**Created by Sajjad SABOUR**")
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
            "🧊 Mode 1: Simple 3D Model (Upgrades to Photoreal Studio Lighting)", 
            "📸 Mode 2: Existing Photo / Render (Enhances Commercial Realism)"
        ]
    )
    
    uploaded_file = st.file_uploader("2. Upload Product Image (Desk/Chair):", type=["jpg", "jpeg", "png"])
    
    desk_setup = st.text_input(
        "3. Desk Setup & Accessories (Optional):", 
        placeholder="e.g., Add a dual-monitor PC setup... (Leave empty to keep surfaces completely bare)"
    )
    
    environment = st.text_input(
        "4. Environment / Background (Optional):", 
        placeholder="e.g., A sunlit home office... (Leave empty for a clean minimal space)"
    )
    
    st.markdown("### 🧍 Character Injection (Optional)")
    uploaded_character = st.file_uploader("Upload Character Reference Image:", type=["jpg", "jpeg", "png"])
    character_details = st.text_input("Character Details & Pose:", placeholder="e.g., Sitting at the desk typing on a laptop, professional attire...")

with col2:
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

if st.button("Generate Master Prompt ✨", type="primary"):
    if not uploaded_file:
        st.warning("Please upload a primary product image first!")
    else:
        with st.spinner("Analyzing geometry and staging the environment..."):
            try:
                img = Image.open(uploaded_file)
                
                if selected_ar == "Match Uploaded Image":
                    final_ar_tag = get_closest_aspect_ratio_tag(img.width, img.height)
                    st.info(f"Detected image proportions. Appending aspect ratio: **{final_ar_tag}**.")
                else:
                    final_ar_tag = f"--ar {selected_ar}"

                # --- DYNAMIC INSTRUCTIONS ---
                
                # 1. Handle the Environment
                base_env = "The overall aesthetic MUST be a modern, minimal, and clean space designed to highlight the premium desk and accessories."
                if environment:
                    env_instruction = f"{base_env} Specifically, place the setup in this highly realistic environment: '{environment}', blending these details into the minimal baseline."
                else:
                    env_instruction = f"{base_env} Keep the background as a clean, empty, modern photography studio space."

                # 2. Handle the Desk Setup / Accessories
                if desk_setup:
                    setup_instruction = f"Add or modify the desk accessories with these specific items: '{desk_setup}'. Ensure they look like real physical objects."
                else:
                    setup_instruction = f"LEAVE SURFACES BARE. Do not add any extra clutter, laptops, keyboards, plants, or mugs to the desk surfaces. Keep the products exactly as empty as the reference image."

                # 3. Handle the Character
                char_instruction = ""
                if uploaded_character or character_details:
                    char_instruction = f"Add a highly realistic human character to the scene. "
                    if character_details:
                        char_instruction += f"Pose and details: '{character_details}'. "
                    if uploaded_character:
                        char_instruction += "Use the SECOND attached image as a visual reference for this character's appearance and face. "

                # 4. Handle Geometry & Realism (Forcing "Photo" over "Render")
                geometry_lock = "CRITICAL INSTRUCTION: Analyze the exact geometry of the primary product. You MUST strictly enforce keeping the exact same 3D structure, geometry, shapes, and design. Do not alter their core physical design."
                
                if "Mode 1" in input_mode:
                    mode_instruction = f"Focus on converting this simple 3D model into a breathtaking, ultra-realistic photograph captured with a high-end camera. Use true-to-life physical materials. It must look like a real photo, NOT a 3D render."
                else:
                    mode_instruction = f"Focus on enhancing the realism of this image to a high-end commercial photography standard. It must look like a real photo taken with a high-end real-world camera, NOT a 3D render."

                # Combine into the final instruction
                instruction = (
                    f"Act as a strict structural analyzer and expert commercial photography director for a premium desk company. Look at the attached image(s). "
                    f"{geometry_lock} "
                    f"{mode_instruction} "
                    f"{setup_instruction} "
                    f"{env_instruction} "
                    f"{char_instruction} "
                    f"Apply these camera and lighting settings: Lens: {selected_lens}, Depth of Field: {selected_dof}, Lighting: {selected_lighting}. "
                    f"Write a sparse, comma-separated Nano Banana prompt focused entirely on describing a photorealistic image, materials, staging, and lighting. DO NOT write conversational text or full sentences."
                )
                
                # Setup contents list (Instruction + Base Image)
                api_contents = [instruction, img]
                
                # If a character image is uploaded, append it so Gemini can see both
                if uploaded_character:
                    char_img = Image.open(uploaded_character)
                    api_contents.append(char_img)
                
                # Call the AI model
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=api_contents
                )
                
                # Save the generated prompt to session state
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
