from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-proxy-core",
    version="0.3.3",
    author="ebowwa",
    description="Minimal, reusable AI service handlers for Gemini and other LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ebowwa/ai-proxy-core",
    packages=["ai_proxy_core", "ai_proxy_core.providers"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-genai>=0.1.0",
        "pillow>=10.0.0",
        "aiohttp>=3.8.0",  # For Ollama
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "telemetry": [
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "opentelemetry-exporter-otlp>=1.20.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
        "anthropic": [
            "anthropic>=0.18.0",
        ],
        "security": [
            "cryptography>=41.0.0",
            "keyring>=24.0.0",
        ],
        "vault": [
            "hvac>=1.0.0",
        ],
        "aws": [
            "boto3>=1.28.0",
        ],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "opentelemetry-exporter-otlp>=1.20.0",
            "cryptography>=41.0.0",
            "keyring>=24.0.0",
        ]
    }
)