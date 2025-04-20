from setuptools import setup, find_packages

setup(
    name="h5p-material-generator",
    version="0.2.0",
    description="Convert PDFs to interactive H5P presentations using AI",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.10.0",
        "pdfplumber>=0.7.0",
        "groq>=0.3.0",
        "openai>=0.27.0",
        "anthropic>=0.5.0",
        "google-generativeai>=0.2.0",
        "python-dotenv>=0.19.0",
    ],
    python_requires=">=3.8",
)
