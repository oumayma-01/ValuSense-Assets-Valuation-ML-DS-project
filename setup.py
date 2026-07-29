from setuptools import setup, find_packages

setup(
    name="valusense",
    version="3.0",
    description="Intelligent Financial Asset Valuation Method Recommendation",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21",
        "pandas>=1.3",
        "scipy>=1.7",
        "scikit-learn>=1.0",
        "xgboost>=1.6",
        "shap>=0.40",
        "joblib>=1.1",
    ],
)
