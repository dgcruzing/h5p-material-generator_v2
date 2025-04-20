# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Predefined question frameworks with detailed prompts:
  - Bloom's Taxonomy
  - Socratic Method
  - Simple Recall
  - Problem Solving
  - Critical Analysis
- Framework descriptions shown in UI when selected
- Support for both predefined and custom frameworks
- Improved multiple choice question handling in H5P presentations
- Clean text formatting for questions (removed HTML tags)
- Better download controls with file type indicators
- Question preview toggle functionality
- Proper MIME types for downloads
- Two-step download process for H5P packages to improve reliability
- Download button with `on_click="ignore"` to prevent unnecessary app reruns
- Visual improvements to download buttons including primary styling and icons
- Support for latest Streamlit 1.43.0 features

### Changed
- Improved UI organization with better section separation
- Enhanced download section with descriptive captions
- Better error handling for file operations
- Updated download functionality to use Streamlit's new download button features
- Improved user feedback during download process
- Enhanced multiple choice question formatting in H5P presentations
- Better handling of question options and correct answers
- Moved download buttons outside form to comply with Streamlit's form restrictions
- Improved session state management for file downloads

### Fixed
- Multiple choice options now properly displayed in H5P presentations
- HTML tags removed from question text
- Download button functionality
- Markdown preview formatting
- Issue with app rerunning unnecessarily when downloading packages
- Improved file cleanup after download completion
- Fixed multiple choice options not showing in H5P presentations
- Corrected answer handling in multiple choice questions
- Fixed download buttons not working inside forms
- Resolved state management issues during downloads

### Technical Details
- Implemented `on_click="ignore"` for download buttons (Streamlit 1.43.0 feature)
- Added preparation step before download to ensure data consistency
- Updated button UI with material design icons
- Improved temporary file handling during download process
- Enhanced multiple choice question generation with proper option handling
- Added support for both dictionary-style and simple string options
- Improved feedback system for multiple choice questions
- Implemented session state for maintaining file paths between reruns

### Next Steps
- Implement package persistence in database
- Add functionality to Existing Packages section
- Enable package management (edit, delete, etc.)
- Add package metadata storage
- Implement package versioning
- Add package search and filtering
- Enable package sharing functionality
- Add package templates management
- Implement package backup and restore
- Add package analytics and usage tracking

## [0.1.0] - 2024-03-23

### Initial Release
- Basic H5P package generation
- PDF text extraction
- Multiple question types support:
  - Multiple Choice
  - Fill in the Blanks
  - True/False
  - Text
- LLM integration with multiple providers:
  - Groq
  - OpenAI
  - Claude
  - Google Gemini
- Markdown export of generated questions
- Basic framework management 
## [0.1.1] - 2024-04-18
- **Model Selection:** Added a dropdown in the sidebar to select specific models for API providers that have multiple options available (initially for Groq).
- **Configuration:** Added `AVAILABLE_MODELS` and updated `TOKEN_LIMITS` in `config.py` to support model selection.
- **Development:** Added `ruff` for code formatting and linting.
- **Logging:** Added more detailed logging for LLM responses and error handling.
- **H5P Libraries:** Updated `preloadedDependencies` in `h5p.json` to use versions compatible with the included library folders in `content_types`.
- **Groq Model:** Updated the default Groq model from the deprecated `mixtral-8x7b-32768` to `mistral-saba-24b`.
- **Prompts:** Refined LLM prompts for stricter JSON-only output and clearer requirements for specific content types (e.g., Multiple Choice `correct` field).
- **H5P Packaging:** Resolved issue where generated `.h5p` files were missing required library folders, making them unusable. The builder now correctly copies libraries from the `content_types` directory.
- **JSON Parsing:** Fixed JSON parsing errors from LLM responses (especially Groq) by adding cleaning logic for markdown fences and improving prompt instructions.
- **Indentation Errors:** Resolved multiple `IndentationError` issues caused by leading whitespace in Python files within `h5p_generator`.
- **API Key Handling:** Corrected logic to properly use API keys from the `.env` file when available, instead of always requiring manual input.
- **Multiple Choice Format:** Fixed validation error where the `correct` field in multiple choice JSON was not correctly formatted as the option text.