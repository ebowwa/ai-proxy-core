from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-proxy-core",
    version="0.1.7",
    author="ebowwa",
    description="Minimal, reusable AI service handlers for Gemini and other LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ebowwa/ai-proxy-core",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-genai>=0.1.0",
        "pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ]
    }
)