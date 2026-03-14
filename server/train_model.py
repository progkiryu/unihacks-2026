import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
import os
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

print("🚀 Setting up model training...")

# Check if MPS (Apple GPU) is available
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

# ============================================
# MODEL DEFINITION
# ============================================
class StrokeCNN(nn.Module):
    def __init__(self):
        super(StrokeCNN, self).__init__()
        
        # Block 1
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 32, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.dropout1 = nn.Dropout(0.25)
        
        # Block 2
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.conv4 = nn.Conv2d(64, 64, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.dropout2 = nn.Dropout(0.25)
        
        # Block 3
        self.conv5 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn5 = nn.BatchNorm2d(128)
        self.conv6 = nn.Conv2d(128, 128, 3, padding=1)
        self.bn6 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.dropout3 = nn.Dropout(0.25)
        
        # Block 4
        self.conv7 = nn.Conv2d(128, 256, 3, padding=1)
        self.bn7 = nn.BatchNorm2d(256)
        self.conv8 = nn.Conv2d(256, 256, 3, padding=1)
        self.bn8 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2, 2)
        self.dropout4 = nn.Dropout(0.25)
        
        # Calculate the size after convolutions
        # Input: 224x224, after 4 pooling layers: 224/16 = 14
        self.fc_input_size = 256 * 14 * 14
        
        # Classifier
        self.fc1 = nn.Linear(self.fc_input_size, 512)
        self.bn9 = nn.BatchNorm1d(512)
        self.dropout5 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(512, 128)
        self.bn10 = nn.BatchNorm1d(128)
        self.dropout6 = nn.Dropout(0.3)
        self.fc3 = nn.Linear(128, 1)
        
    def forward(self, x):
        # Block 1
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool1(x)
        x = self.dropout1(x)
        
        # Block 2
        x = torch.relu(self.bn3(self.conv3(x)))
        x = torch.relu(self.bn4(self.conv4(x)))
        x = self.pool2(x)
        x = self.dropout2(x)
        
        # Block 3
        x = torch.relu(self.bn5(self.conv5(x)))
        x = torch.relu(self.bn6(self.conv6(x)))
        x = self.pool3(x)
        x = self.dropout3(x)
        
        # Block 4
        x = torch.relu(self.bn7(self.conv7(x)))
        x = torch.relu(self.bn8(self.conv8(x)))
        x = self.pool4(x)
        x = self.dropout4(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Classifier
        x = torch.relu(self.bn9(self.fc1(x)))
        x = self.dropout5(x)
        x = torch.relu(self.bn10(self.fc2(x)))
        x = self.dropout6(x)
        x = torch.sigmoid(self.fc3(x))
        
        return x

# Create model
model = StrokeCNN().to(device)
print("✅ Model created!")

# ============================================
# DATA LOADING
# ============================================

# Data transforms with augmentation
transform_train = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.3),
    transforms.RandomRotation(5),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

transform_val = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Load datasets
print("\n📂 Loading training data...")
train_dataset = datasets.ImageFolder(
    root='../model/data/processed/train',
    transform=transform_train
)

print("📂 Loading validation data...")
val_dataset = datasets.ImageFolder(
    root='../model/data/processed/validation',
    transform=transform_val
)

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

print(f"✅ Training samples: {len(train_dataset)}")
print(f"✅ Validation samples: {len(val_dataset)}")
print(f"Classes: {train_dataset.classes}")  # Should be ['normal', 'stroke']

# ============================================
# CLASS WEIGHTS (for imbalance)
# ============================================

# Get all labels
train_labels = [label for _, label in train_dataset.samples]

# Compute weights
class_weights = compute_class_weight(
    'balanced',
    classes=np.unique(train_labels),
    y=train_labels
)
weights = torch.tensor(class_weights, dtype=torch.float).to(device)
print(f"\n📊 Class weights: Normal={weights[0]:.2f}, Stroke={weights[1]:.2f}")

# Loss function with class weights
criterion = nn.BCEWithLogitsLoss(pos_weight=weights[1].unsqueeze(0))

# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.0001)

# Learning rate scheduler
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)

# ============================================
# TRAINING LOOP
# ============================================

print("\n🎯 Starting training...")
num_epochs = 20
best_val_loss = float('inf')

for epoch in range(num_epochs):
    # Training phase
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device).float().unsqueeze(1)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        train_loss += loss.item()
        predicted = (torch.sigmoid(outputs) > 0.5).float()
        train_total += labels.size(0)
        train_correct += (predicted == labels).sum().item()
    
    avg_train_loss = train_loss / len(train_loader)
    train_acc = 100 * train_correct / train_total
    
    # Validation phase
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device).float().unsqueeze(1)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            predicted = (torch.sigmoid(outputs) > 0.5).float()
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()
    
    avg_val_loss = val_loss / len(val_loader)
    val_acc = 100 * val_correct / val_total
    
    # Update scheduler
    scheduler.step(avg_val_loss)
    
    # Save best model
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        torch.save(model.state_dict(), 'best_stroke_model.pth')
        print(f"💾 Saved best model (val_loss: {avg_val_loss:.4f})")
    
    print(f"Epoch [{epoch+1}/{num_epochs}] "
          f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
          f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.2f}%")

# Save final model
torch.save(model.state_dict(), 'stroke_model_final.pth')
print("\n✅ Training complete!")
print("💾 Final model saved as 'stroke_model_final.pth'")
print("💾 Best model saved as 'best_stroke_model.pth'")

# Quick test on a few validation samples
model.eval()
print("\n📊 Quick test on validation set:")
with torch.no_grad():
    images, labels = next(iter(val_loader))
    images, labels = images.to(device), labels.to(device)
    outputs = torch.sigmoid(model(images))
    
    for i in range(min(5, len(images))):
        pred = "Stroke" if outputs[i] > 0.5 else "Normal"
        actual = "Stroke" if labels[i] == 1 else "Normal"
        conf = outputs[i].item() * 100 if outputs[i] > 0.5 else (1 - outputs[i].item()) * 100
        print(f"  Sample {i+1}: Predicted={pred} ({conf:.1f}%), Actual={actual}")
