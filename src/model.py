import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, SubsetRandomSampler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")   # headless backend — saves to file instead of opening a window
import os
from spells import SPELLS

NUM_CLASSES = len(SPELLS)
INPUT_SIZE  = 64
# Inverse of SPELLS: index → class name, for readable labels
CLASS_NAMES = [SPELLS[i] for i in range(NUM_CLASSES)]


# ------------------------
# Model Definition
# ------------------------

class RuneCNN(nn.Module):

    def __init__(self, input_size=INPUT_SIZE):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        # Derive flat size from input_size so it's always correct
        conv_out  = input_size // (2 ** 3)
        flat_size = 128 * conv_out * conv_out

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, NUM_CLASSES),
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        return x


# ------------------------
# Internal helpers
# ------------------------

def _get_transform():
    return transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.ToTensor(),
    ])


def _train_one_fold(model, train_loader, epochs, criterion, device):
    """Train model for one fold. Returns the trained model."""
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    model.train()

    for epoch in range(epochs):
        total_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"    Epoch {epoch + 1}/{epochs}  loss={total_loss:.4f}")

    return model


def _evaluate_fold(model, val_loader, device):
    """
    Run inference on a validation fold.
    Returns (all_labels, all_preds) as flat numpy arrays.
    """
    model.eval()
    all_labels, all_preds = [], []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            outputs = model(images)
            preds   = torch.argmax(outputs, dim=1).cpu().numpy()
            all_labels.extend(labels.numpy())
            all_preds.extend(preds)

    return np.array(all_labels), np.array(all_preds)


# ------------------------
# Confusion matrix output
# ------------------------

def _save_confusion_matrix(cm, class_names, fold, output_dir):
    """Save a labelled confusion matrix PNG for one fold (or the aggregate)."""
    fig, ax = plt.subplots(figsize=(14, 12))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, xticks_rotation=45, colorbar=True)
    title = "Aggregate Confusion Matrix" if fold == "aggregate" else f"Fold {fold} Confusion Matrix"
    ax.set_title(title, fontsize=14)
    plt.tight_layout()

    fname = os.path.join(output_dir, f"confusion_matrix_{fold}.png")
    plt.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"    Saved: {fname}")


# ------------------------
# Training  (with k-fold CV)
# ------------------------

def train_model(dataset_path, epochs=10, batch_size=32, k_folds=5, output_dir="eval"):
    """
    Train RuneCNN with stratified k-fold cross-validation.

    After all folds:
      - Prints per-fold accuracy and mean ± std
      - Prints an aggregate classification report (precision/recall/F1 per class)
      - Saves per-fold confusion matrix PNGs to output_dir/
      - Saves an aggregate confusion matrix PNG
      - Retrains a final model on the full dataset and saves it as rune_cnn.pth

    Args:
        dataset_path (str)  — path to ImageFolder-structured dataset
        epochs       (int)  — training epochs per fold
        batch_size   (int)  — mini-batch size
        k_folds      (int)  — number of CV folds (default 5)
        output_dir   (str)  — directory to write evaluation plots
    """
    os.makedirs(output_dir, exist_ok=True)
    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    criterion = nn.CrossEntropyLoss()

    transform = _get_transform()
    dataset   = datasets.ImageFolder(dataset_path, transform=transform)
    labels    = np.array([s[1] for s in dataset.samples])

    print(f"\n{'='*55}")
    print(f" K-Fold Cross Validation  (k={k_folds}, epochs={epochs})")
    print(f" Dataset: {len(dataset)} samples  |  Classes: {NUM_CLASSES}")
    print(f" Device:  {device}")
    print(f"{'='*55}\n")

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)
    fold_accuracies = []
    aggregate_labels, aggregate_preds = [], []

    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(labels)), labels), start=1):
        print(f"── Fold {fold}/{k_folds}  "
              f"(train={len(train_idx)}, val={len(val_idx)}) ──")

        train_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=SubsetRandomSampler(train_idx),
        )
        val_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=SubsetRandomSampler(val_idx),
        )

        model = RuneCNN().to(device)
        model = _train_one_fold(model, train_loader, epochs, criterion, device)

        fold_labels, fold_preds = _evaluate_fold(model, val_loader, device)
        accuracy = (fold_labels == fold_preds).mean() * 100
        fold_accuracies.append(accuracy)

        print(f"    Fold {fold} accuracy: {accuracy:.2f}%\n")

        # Per-fold confusion matrix
        cm = confusion_matrix(fold_labels, fold_preds, labels=list(range(NUM_CLASSES)))
        _save_confusion_matrix(cm, CLASS_NAMES, fold, output_dir)

        aggregate_labels.extend(fold_labels)
        aggregate_preds.extend(fold_preds)

    # ── Summary ──────────────────────────────────────────────
    aggregate_labels = np.array(aggregate_labels)
    aggregate_preds  = np.array(aggregate_preds)

    mean_acc = np.mean(fold_accuracies)
    std_acc  = np.std(fold_accuracies)

    print(f"\n{'='*55}")
    print(f" Cross-Validation Results")
    print(f"{'='*55}")
    for i, acc in enumerate(fold_accuracies, 1):
        print(f"  Fold {i}: {acc:.2f}%")
    print(f"\n  Mean accuracy : {mean_acc:.2f}%")
    print(f"  Std  accuracy : {std_acc:.2f}%")
    print(f"{'='*55}\n")

    print("Aggregate Classification Report:")
    print(classification_report(
        aggregate_labels,
        aggregate_preds,
        target_names=CLASS_NAMES,
        digits=3,
    ))

    # Aggregate confusion matrix
    agg_cm = confusion_matrix(aggregate_labels, aggregate_preds, labels=list(range(NUM_CLASSES)))
    _save_confusion_matrix(agg_cm, CLASS_NAMES, "aggregate", output_dir)

    # ── Final model — retrain on full dataset ─────────────────
    print("Retraining final model on full dataset...")
    final_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    final_model  = RuneCNN().to(device)
    final_model  = _train_one_fold(final_model, final_loader, epochs, criterion, device)

    torch.save(final_model.state_dict(), "rune_cnn.pth")
    print("Model saved to rune_cnn.pth")


# ------------------------
# Model Loader
# ------------------------

def load_model():
    model = RuneCNN()
    model.load_state_dict(torch.load("rune_cnn.pth", map_location="cpu"))
    model.eval()
    return model


# ------------------------
# Prediction
# ------------------------

def predict(model, img, conf_threshold=0.6, margin_threshold=0.25):
    tensor = torch.tensor(img, dtype=torch.float32)
    tensor = tensor.permute(0, 3, 1, 2)

    with torch.no_grad():
        output = model(tensor)

    probs = torch.softmax(output, dim=1)
    top2  = torch.topk(probs, 2)

    top_prob    = top2.values[0][0].item()
    second_prob = top2.values[0][1].item()
    margin      = top_prob - second_prob

    if top_prob < conf_threshold or margin < margin_threshold:
        return None

    print("top:", top_prob, " second:", second_prob, " margin:", margin)
    return probs.numpy()