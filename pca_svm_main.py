"""
Main script for training PCA + kernel SVM
"""

# Imports
import time

import joblib

from load_data_common import load_train_matrices, load_test_matrices
from models.models import fit_channel_pca, fit_channel_rpca, fit_svm
from utils import reshape_matrix_flat, reshape_matrix_channels


USE_RPCA = True  # set false for PCA
method_str = "rpca" if USE_RPCA else "pca"
pca_method = fit_channel_rpca if USE_RPCA else fit_channel_pca
print(f"Running experiments for {method_str.upper()} with SVM")


PCA_MODEL_SAVE_PATH = f"models/saved_models/{method_str}.pt"
SVM_MODEL_SAVE_PATH = f"models/saved_models/{method_str}_svm.pt"
PCA_LOAD_SAVED_MODEL = False
SVM_LOAD_SAVED_MODEL = False

assert not SVM_LOAD_SAVED_MODEL or PCA_LOAD_SAVED_MODEL, "if SVM is loaded, PCA should also be loaded"

NUM_PCA_COMPONENTS = 100 // 3


# Load data
print("Loading training data.")
t0 = time.time()
train_image_matrix, train_label_matrix = load_train_matrices()
train_image_matrix = reshape_matrix_channels(train_image_matrix)
print(f"Loaded data in {time.time() - t0:.2f} seconds.")

# Fit PCA if desired
if PCA_LOAD_SAVED_MODEL:
    print(f"Loading saved {method_str.upper()}.")
    pca_model = joblib.load(PCA_MODEL_SAVE_PATH)
else:
    print(f"Fitting {method_str.upper()} model.")
    pca_model = pca_method(train_image_matrix, num_components=NUM_PCA_COMPONENTS, verbose=2)
    joblib.dump(pca_model, PCA_MODEL_SAVE_PATH)

# eigenfingers = pca_model.get_eigenfingers()
# print(eigenfingers.shape)
# print(eigenfingers)
# raise NotImplementedError

print(f"Transforming training data using {method_str.upper()} model.")
t0 = time.time()
reduced_image_matrix = pca_model.transform(train_image_matrix)
print(f"Done, took {time.time() - t0:.2f} seconds.")

# Fit SVM if desired
if SVM_LOAD_SAVED_MODEL:
    print("Loading saved SVM model.")
    svm_model = joblib.load(SVM_MODEL_SAVE_PATH)
    print("Done loading, computing training accuracy...")
    t0 = time.time()
    print(f"Training accuracy: {svm_model.score(reduced_image_matrix, train_label_matrix):.4f}")
    print(f"(Took {time.time() - t0:.2f} seconds)")
else:
    print("Training SVM model.")
    svm_model = fit_svm(reduced_image_matrix, train_label_matrix, gamma='scale', C=15.0, verbose=1)
    joblib.dump(svm_model, SVM_MODEL_SAVE_PATH)


# Load test data
print("Loading test data.")
t0 = time.time()
test_matrices = load_test_matrices()
print(f"Loaded data in {time.time() - t0:.2f} seconds.")


# Test on test data
print("Running accuracy tests...")
dataset_names = sorted(test_matrices.keys())
for ds_name in dataset_names:
    test_image_matrix, test_label_matrix = test_matrices[ds_name]
    reduced_test_image_matrix = pca_model.transform(reshape_matrix_channels(test_image_matrix))
    flat_reduced_matrix = reduced_test_image_matrix
    print(f"{ds_name} accuracy: {svm_model.score(flat_reduced_matrix, test_label_matrix):.4f}")

print("Done.")
