# app.py
import streamlit as st
import os
import logging # Import logging
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple
from streamlit.runtime.uploaded_file_manager import UploadedFile # Import UploadedFile type

from h5p_generator.config import ERROR_MESSAGES, DB_PATH, AVAILABLE_MODELS, DEFAULT_MODELS, TOKEN_LIMITS, API_KEYS
from h5p_generator.db_manager import DatabaseManager
from h5p_generator.api_clients import LLMClientFactory, LLMClientException, BaseLLMClient
from h5p_generator.h5p_builder import H5PBuilder, H5PContentValidationException
from h5p_generator.utils import extract_text_from_pdf

# Define Constants
NUM_SLIDES: int = 10

logger = logging.getLogger(__name__) # Add logger instance

# Initialize database
db_manager: DatabaseManager = DatabaseManager()

# --- Helper Functions ---

def generate_h5p_content(
    selected_api: str,
    api_key: str,
    pdf_file: UploadedFile,
    prompt_input: str,
    content_type: str,
    num_slides: int,
    model_id: Optional[str] = None
) -> Tuple[str, str]:
    """Generates H5P content from a PDF file using the specified parameters.

    Args:
        selected_api: The name of the LLM API provider.
        api_key: The API key for the selected provider.
        pdf_file: The uploaded PDF file.
        prompt_input: The base prompt for the LLM.
        content_type: The type of H5P activity to generate.
        num_slides: The number of slides/questions to generate.
        model_id: The specific model ID to use (optional, defaults based on provider).

    Returns:
        A tuple containing the file paths of the generated .h5p and .md files.

    Raises:
        LLMClientException: If there's an error during API interaction.
        ValueError: If PDF text extraction fails.
        H5PContentValidationException: If the LLM response structure is invalid.
        Exception: For other potential errors during processing.
    """
    # Create LLM client
    llm_client: BaseLLMClient = LLMClientFactory.create_client(selected_api, api_key, model=model_id)

    # Extract text from PDF
    success: bool
    result: str
    success, result = extract_text_from_pdf(pdf_file)
    if not success:
        raise ValueError(f"PDF extraction failed: {result}")

    pdf_text: str = result
    pdf_name: str = pdf_file.name.split(".")[0]

    # Build the full prompt
    strict_json_instruction: str = (
        f"IMPORTANT: Your response MUST be ONLY the valid JSON list containing {num_slides} objects, "
        f"strictly formatted as requested. Do NOT include any other text, explanations, comments, "
        f"markdown formatting, or tags like <think> before or after the JSON data."
    )
    full_prompt: str = f"{prompt_input}\n\n{strict_json_instruction}\n\n"

    # Add content type specific instructions
    if content_type == "Multiple Choice":
        full_prompt += (
            f"From the following text, generate {num_slides} multiple-choice questions, each with 4 options and one correct answer. "
            f"Return the result as a JSON list of objects with 'question', 'options', and 'correct' keys. "
            f"Crucially, the value for the 'correct' key MUST be the exact text of one of the strings provided in the 'options' list for that question.\n\nText:\n{pdf_text}"
        )
    elif content_type == "Fill in the Blanks":
        full_prompt += (
            f"From the following text, generate {num_slides} fill-in-the-blanks sentences, each with one blank and its answer. "
            f"Return the result as a JSON list of objects with 'text' and 'answer' keys.\n\nText:\n{pdf_text}"
        )
    elif content_type == "True/False":
        full_prompt += (
            f"From the following text, generate {num_slides} true/false statements, each with a question and a correct answer (True or False). "
            f"Return the result as a JSON list of objects with 'question' and 'correct' keys.\n\nText:\n{pdf_text}"
        )
    elif content_type == "Text":
        full_prompt += (
            f"From the following text, generate {num_slides} concise text snippets for presentation slides, each summarizing a key point. "
            f"Return the result as a JSON list of objects with 'text' keys.\n\nText:\n{pdf_text}"
        )

    with st.spinner("Generating content..."):
        # Generate content using LLM
        content: List[Dict[str, Any]] = llm_client.generate_content(full_prompt)

        # --- Validate Content --- Start
        # Validate the structure AFTER generation and BEFORE building H5P
        temp_builder = H5PBuilder("validation_check", content_type)
        try:
            temp_builder._validate_content_data(content) # Use internal validation method
            st.success("LLM Response JSON structure looks valid!")
        except H5PContentValidationException as e:
            st.error(f"LLM Response Validation Error: {e}")
            st.json(content) # Show the invalid JSON
            logger.error(f"Invalid JSON received: {content}") # Log the invalid JSON
            raise # Stop further processing
        # --- Validate Content --- End

        st.write(f"Generated Content (first 2 of {len(content)}):", content[:2]) # Show length based on actual content

        # Create H5P package
        output_filename: str = f"{pdf_name}_{content_type.replace('/', '-')}_Presentation.h5p"
        with H5PBuilder(f"Course Presentation from {pdf_name}", content_type) as builder:
            h5p_file_path: str
            md_file_path: str
            h5p_file_path, md_file_path = builder.create_course_presentation(content, output_filename, num_slides)

            return h5p_file_path, md_file_path

# UI Setup
st.title("H5P Material Generator")
st.write(f"Upload a PDF and generate a Course Presentation with {NUM_SLIDES} slides!")

# Sidebar - API Selection
api_options: List[str] = ["Groq", "OpenAI", "Claude", "Google Gemini"]
selected_api: str = st.sidebar.selectbox("Select API Provider", api_options)

# Check if API key exists in environment (via config.API_KEYS)
provider_key_lower = selected_api.lower().replace(" ", "_") # Match keys in config.py (e.g., 'google_gemini')
env_api_key = API_KEYS.get(provider_key_lower)

api_key: Optional[str] = None
if env_api_key:
    api_key = env_api_key
    st.sidebar.success(f"{selected_api} API key loaded from environment.")
else:
    st.sidebar.warning(f"{selected_api} API key not found in environment.")
    api_key = st.sidebar.text_input(
        f"Enter {selected_api} API Key",
        type="password",
        key=f"{selected_api}_key_input" # Change key to avoid conflict
    )

# Sidebar - Model Selection
st.sidebar.subheader("Model Selection")
selected_model_id: Optional[str] = None
provider_key = selected_api.lower() # Use lowercase key for dictionaries

if provider_key in AVAILABLE_MODELS:
    available_provider_models = AVAILABLE_MODELS[provider_key]
    default_model = DEFAULT_MODELS.get(provider_key)

    if len(available_provider_models) > 1:
        # Find index of default model, default to 0 if not found
        try:
            default_index = available_provider_models.index(default_model)
        except ValueError:
            default_index = 0

        selected_model_id = st.sidebar.selectbox(
            "Select Model",
            available_provider_models,
            index=default_index,
            key=f"{selected_api}_model_select"
        )
        st.sidebar.caption(f"Context Window: {TOKEN_LIMITS.get(selected_model_id, 'N/A') // 1000}k tokens")
    elif available_provider_models:
        selected_model_id = available_provider_models[0] # Only one model available
        st.sidebar.info(f"Using model: `{selected_model_id}`")
        st.sidebar.caption(f"Context Window: {TOKEN_LIMITS.get(selected_model_id, 'N/A') // 1000}k tokens")
    else:
        st.sidebar.warning("No models configured for this provider.")
else:
    st.sidebar.warning("Provider configuration not found.")

# Sidebar - Framework Management
st.sidebar.subheader("Prompt Frameworks")
frameworks: List[str] = ["None", "Custom"] + db_manager.get_all_frameworks()
framework_option: str = st.sidebar.selectbox("Choose a framework", frameworks, key="framework")

st.sidebar.subheader("Manage Frameworks")
with st.sidebar.expander("Add New Framework"):
    new_name: str = st.text_input("Framework Name")
    new_prompt: str = st.text_area("Framework Prompt")
    if st.button("Add Framework") and new_name and new_prompt:
        success: bool = db_manager.add_framework(new_name, new_prompt)
        if success:
            st.success(f"Added '{new_name}' successfully!")
            st.experimental_rerun()
        else:
            st.error(ERROR_MESSAGES["framework_exists"].format(name=new_name))

existing_frameworks: List[str] = db_manager.get_all_frameworks()
if existing_frameworks:
    framework_to_delete: str = st.sidebar.selectbox("Select framework to delete", existing_frameworks, key="delete_framework")
    if st.sidebar.button("Delete Framework") and framework_to_delete:
        success: bool = db_manager.delete_framework(framework_to_delete)
        if success:
            st.sidebar.success(f"Deleted '{framework_to_delete}' successfully!")
            st.experimental_rerun()
        else:
            st.sidebar.error(ERROR_MESSAGES["framework_delete_failed"].format(name=framework_to_delete))

# Main UI
pdf_file: Optional[st.runtime.uploaded_file_manager.UploadedFile] = st.file_uploader("Upload a PDF", type=["pdf"])
content_type: str = st.selectbox("Choose Activity Type for Slides",
                           ["Multiple Choice", "Fill in the Blanks", "True/False", "Text"])

default_prompt: str = "Generate clear, concise questions based on the provided text."
if framework_option == "Custom":
    prompt_input: str = st.text_area("Leading Prompt for LLM", value=default_prompt, height=100)
else:
    prompt_input = db_manager.get_prompt_by_name(framework_option) if framework_option != "None" else default_prompt
    if framework_option != "None" and framework_option != "Custom":
        st.info(f"Using framework: {framework_option}")
        st.code(prompt_input)

generate_button: bool = st.button("Generate Course Presentation")

# Content Generation
if generate_button and pdf_file and api_key:
    try:
        # Ensure a model is selected before proceeding
        if not selected_model_id:
            st.error("Please select a valid model for the chosen API provider.")
        else:
            h5p_file_path, md_file_path = generate_h5p_content(
                selected_api=selected_api,
                api_key=api_key,
                pdf_file=pdf_file,
                prompt_input=prompt_input,
                content_type=content_type,
                num_slides=NUM_SLIDES,
                model_id=selected_model_id
            )

            # Store in session state for download
            st.session_state["h5p_file"] = h5p_file_path
            st.session_state["md_file"] = md_file_path

    except H5PContentValidationException as e:
        # Error already displayed in generate_h5p_content, just log maybe?
        logger.error(f"Caught H5P Content Validation Error: {e}") # Log validation error
    except (LLMClientException, ValueError) as e: # Catch specific exceptions
        st.error(f"{ERROR_MESSAGES['generation_error_prefix']} {e}")
        logger.error(f"{ERROR_MESSAGES['generation_error_prefix']} {e}") # Log other client/value errors
    except Exception as e:
        st.error(f"{ERROR_MESSAGES['unexpected_error_prefix']} {e}")
        logger.exception("An unexpected error occurred during content generation") # Log unexpected errors with traceback

# Display Download Buttons if Files Exist
if "h5p_file" in st.session_state and "md_file" in st.session_state:
    h5p_file_path: str = st.session_state["h5p_file"]
    md_file_path: str = st.session_state["md_file"]

    if os.path.exists(h5p_file_path) and os.path.exists(md_file_path):
        col1, col2 = st.columns(2)
        with col1:
            with open(h5p_file_path, "rb") as f:
                st.download_button("Download H5P Course Presentation", f, file_name=os.path.basename(h5p_file_path))
        with col2:
            with open(md_file_path, "rb") as f:
                st.download_button("Download Questions Markdown", f, file_name=os.path.basename(md_file_path))
