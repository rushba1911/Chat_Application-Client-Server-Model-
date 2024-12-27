import os
import shutil
import random
from PIL import Image

# Paths to the original dataset folder and new folders for train/validation/test
dataset_dir = 'C:/garbage-dataset'  # Replace with the actual dataset path
train_dir = 'C:/Users/HP/Documents/Smart-Sort/Dataset/train'
validation_dir = 'C:/Users/HP/Documents/Smart-Sort/Dataset/validation'
test_dir = 'C:/Users/HP/Documents/Smart-Sort/Dataset/test'  # Added test directory

# Define the target directories for Recyclable and Non-Recyclable in train, validation, and test
recyclable_train_dir = os.path.join(train_dir, 'recyclable')
non_recyclable_train_dir = os.path.join(train_dir, 'non-recyclable')  # Updated to lowercase for consistency
recyclable_val_dir = os.path.join(validation_dir, 'recyclable')
non_recyclable_val_dir = os.path.join(validation_dir, 'non-recyclable')  # Updated to lowercase for consistency
recyclable_test_dir = os.path.join(test_dir, 'recyclable')
non_recyclable_test_dir = os.path.join(test_dir, 'non-recyclable')  # Updated to lowercase for consistency

# Create the directories if they don't exist
os.makedirs(recyclable_train_dir, exist_ok=True)
os.makedirs(non_recyclable_train_dir, exist_ok=True)
os.makedirs(recyclable_val_dir, exist_ok=True)
os.makedirs(non_recyclable_val_dir, exist_ok=True)
os.makedirs(recyclable_test_dir, exist_ok=True)
os.makedirs(non_recyclable_test_dir, exist_ok=True)

# List of recyclable categories
recyclable_categories = ['cardboard', 'glass', 'metal', 'paper', 'plastic']

# List of non-recyclable categories
non_recyclable_categories = ['battery', 'biological', 'clothes', 'shoes', 'trash']

# Allowed image extensions
valid_extensions = ('.jpg', '.jpeg', '.png')

# Function to check dataset quality by validating images
def is_valid_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify the integrity of the image
        return True
    except Exception:
        return False

# Function to check class balance and suggest balancing strategies
def check_class_balance(train_dir):
    class_counts = {}
    for category in os.listdir(train_dir):
        category_path = os.path.join(train_dir, category)
        if os.path.isdir(category_path):
            class_counts[category] = len(os.listdir(category_path))
    print(f"Class distribution in training set: {class_counts}")
    # Add data augmentation or oversampling here if needed to balance classes

# Function to organize the dataset
def organize_dataset(dataset_dir, train_dir, validation_dir, test_dir, train_split=0.6, validation_split=0.2):
    for category in os.listdir(dataset_dir):
        category_path = os.path.join(dataset_dir, category)

        if os.path.isdir(category_path):
            # Determine the target folder based on category
            if category in recyclable_categories:
                target_category = 'recyclable'
            elif category in non_recyclable_categories:
                target_category = 'non-recyclable'  # Updated to lowercase for consistency
            else:
                continue  # Skip unknown categories

            # Get all valid image files in the category folder
            images = [
                f for f in os.listdir(category_path)
                if f.lower().endswith(valid_extensions) and is_valid_image(os.path.join(category_path, f))
            ]

            # Shuffle the images and split into train/validation/test
            random.shuffle(images)
            train_split_index = int(len(images) * train_split)
            validation_split_index = int(len(images) * (train_split + validation_split))

            train_images = images[:train_split_index]
            validation_images = images[train_split_index:validation_split_index]
            test_images = images[validation_split_index:]

            # Move images to the appropriate train, validation, and test folders
            for image_name in train_images:
                shutil.move(os.path.join(category_path, image_name), os.path.join(train_dir, target_category, image_name))

            for image_name in validation_images:
                shutil.move(os.path.join(category_path, image_name), os.path.join(validation_dir, target_category, image_name))

            for image_name in test_images:
                shutil.move(os.path.join(category_path, image_name), os.path.join(test_dir, target_category, image_name))

            print(f"Moved {len(train_images)} images to {target_category} training folder.")
            print(f"Moved {len(validation_images)} images to {target_category} validation folder.")
            print(f"Moved {len(test_images)} images to {target_category} test folder.")

    # Check class balance in training data
    check_class_balance(train_dir)

# Run the function to organize the data
organize_dataset(dataset_dir, train_dir, validation_dir, test_dir)

print("Dataset has been organized into train, validation, and test sets.")
