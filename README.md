# Jet Flavor Tagging with Deep Neural Networks

This repository contains the code and resources for my Bachelor's thesis: **"Classificazione di Jet in Fisica delle Alte Energie con Deep Neural Networks"**. The project explores binary classification of jet flavors in high-energy physics using Feed-Forward Neural Networks (FFNN) and Long Short-Term Memory (LSTM) architectures.

## Overview
Jet flavor tagging is a critical task in high-energy physics experiments, particularly for the identification of quarks like bottom (b-quarks). This project leverages deep learning techniques to classify jets based on simulation data, providing insights into particle interactions observed at experiments like LHC.

Key features:
- Implementation of FFNN and LSTM models.
- Handling and preprocessing of a large dataset (~11 million samples).
- Optimization of model hyperparameters.
- Analysis of results through statistical and graphical evaluations.

## Features
1. **Dataset Processing**:
   - Conversion of JSON data into compressed `.npz` format for efficient loading.
   - Reshaping and normalizing the dataset for neural network training.

2. **Model Architectures**:
   - **Feed-Forward Neural Network (FFNN)**:
     - Deep architecture with multiple layers and dropout regularization.
     - Optimized for binary classification tasks.
   - **Long Short-Term Memory (LSTM)**:
     - Incorporates sequential dependencies for jet feature analysis.
     - Utilizes tailored hidden layers and dropout configurations.

3. **Hyperparameter Optimization**:
   - Automated grid search for tuning layer dimensions, dropout rates, and hidden dimensions.

4. **Training and Evaluation**:
   - Training with PyTorch and evaluation using metrics like CrossEntropy Loss and AUROC.
   - Model saving for best and last checkpoints.

## Results
- **FFNN** achieved an AUROC of **0.91** with optimized hyperparameters.
- **LSTM** exhibited robust performance with comparable metrics, showcasing its ability to handle sequential data.


## Requirements
- Python 3.x
- PyTorch
- NumPy
- Pandas
- Matplotlib
- scikit-learn
- torchmetrics
- Google Colab (optional for execution)

Install dependencies:
```bash
pip install -r requirements.txt
