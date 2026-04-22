import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import json
from spells import SPELLS

#MODEL_INPUT_SIZE = 64
NUM_CLASSES = len(SPELLS)


class RuneCNN(nn.Module):

    def __init__(self):
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
            nn.MaxPool2d(2)
        )

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(),
            nn.Linear(256, NUM_CLASSES)
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        return x


# ------------------------
# Training
# ------------------------

def train_model(dataset_path, epochs=10, batch_size=32):
    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.ToTensor()
    ])

    dataset = datasets.ImageFolder(dataset_path, transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = RuneCNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        total_loss = 0

        for images, labels in loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}: loss = {total_loss}")
    torch.save(model.state_dict(), "rune_cnn.pth")

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

    top2 = torch.topk(probs, 2)

    top_prob = top2.values[0][0].item()
    second_prob = top2.values[0][1].item()

    margin = top_prob - second_prob

    if top_prob < conf_threshold or margin < margin_threshold:
        return None
    
    print("top:", top_prob, " second:", second_prob, " margin:", margin)
    return probs.numpy()