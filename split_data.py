import os
import random
import shutil
from sklearn.model_selection import train_test_split

# Source paths
source_dir = "model/data"
dest_dir = "model/data/processed"

# Split ratios
train_ratio = 0.7
val_ratio = 0.15
test_ratio = 0.15

print("🚀 Splitting dataset...")

# Process each class
for class_name in ['Stroke', 'NonStroke']:
    # Get all files
    class_path = os.path.join(source_dir, class_name)
    if not os.path.exists(class_path):
        print(f"⚠️  {class_path} not found, skipping...")
        continue
        
    files = [f for f in os.listdir(class_path) 
             if f.endswith(('.jpg', '.png', '.jpeg', '.JPG', '.PNG'))]
    random.shuffle(files)
    
    print(f"\n📂 {class_name}: {len(files)} images")
    
    # Calculate split points
    total = len(files)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    # Split
    train_files = files[:train_end]
    val_files = files[train_end:val_end]
    test_files = files[val_end:]
    
    # Determine destination class name
    dest_class = 'normal' if class_name == 'NonStroke' else 'stroke'
    
    # Copy files
    for f in train_files:
        src = os.path.join(class_path, f)
        dst = os.path.join(dest_dir, 'train', dest_class, f)
        shutil.copy2(src, dst)
    
    for f in val_files:
        src = os.path.join(class_path, f)
        dst = os.path.join(dest_dir, 'validation', dest_class, f)
        shutil.copy2(src, dst)
    
    for f in test_files:
        src = os.path.join(class_path, f)
        dst = os.path.join(dest_dir, 'test', dest_class, f)
        shutil.copy2(src, dst)
    
    print(f"  → Train: {len(train_files)}")
    print(f"  → Validation: {len(val_files)}")
    print(f"  → Test: {len(test_files)}")

print("\n✅ Dataset split complete!")
print("\n📁 Final structure:")
print("model/data/processed/")
print("  ├── train/")
print("  │   ├── normal/     ← Normal faces for training")
print("  │   └── stroke/     ← Stroke faces for training")
print("  ├── validation/")
print("  │   ├── normal/     ← Normal faces for validation")
print("  │   └── stroke/     ← Stroke faces for validation")
print("  └── test/")
print("      ├── normal/     ← Normal faces for testing")
print("      └── stroke/     ← Stroke faces for testing")
