# H5P Material Generator v2

This project generates interactive H5P learning content (initially True/False questions) from PDF documents using various Large Language Models (LLMs) via API calls. It provides a Streamlit interface for users to upload PDFs and configure the generation process.

## Features

*   Upload PDF documents.
*   Extract text content from PDFs.
*   Utilize different LLM providers (OpenAI, Anthropic, Groq, Google Gemini - configurable) to generate H5P questions based on the extracted text.
*   Generate H5P packages (.h5p files) containing the interactive content.
*   Simple Streamlit web interface.

## Prerequisites

*   Python 3.10+
*   pip (Python package installer)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dgcruzing/h5p-material-generator_v2.git
    cd h5p-material-generator_v2
    ```

2.  **Create and activate a virtual environment:**
    *   On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Copy the example environment file:
        ```bash
        # Windows
        copy .env.example .env

        # macOS/Linux
        cp .env.example .env
        ```
    *   Open the `.env` file in a text editor.
    *   Replace the placeholder values (`YOUR_..._API_KEY_HERE`) with your actual API keys for the LLM services you intend to use. You only need to provide keys for the services you will select in the Streamlit app.
    *   **Important:** Do not commit your `.env` file to Git. It is already included in `.gitignore`.

## Running the Application

Once the setup is complete, run the Streamlit application:

```bash
streamlit run app.py
```

This will start the web server, and you can access the application in your web browser at the local URL provided in the terminal (usually `http://localhost:8501`).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 