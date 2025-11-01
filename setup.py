from setuptools import setup, find_packages

setup(
    name="evoagent",
    version="0.1.0",
    description="Production-ready competitive AI evolution framework (DeepSeek-R1 vs Qwen2.5-Coder)",
    author="ftshortt",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        # Duplicated in requirements.txt for runtime environments
        "neo4j>=5.26.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.6",
        "pydantic>=2.9.2",
        "python-dotenv>=1.0.1",
        "prometheus-client>=0.21.0",
        "prometheus-fastapi-instrumentator>=6.1.0",
        "docker>=7.1.0",
        "requests>=2.32.0",
    ],
    python_requires=">=3.11",
)
