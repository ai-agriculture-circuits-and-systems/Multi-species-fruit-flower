import os
import cv2
import numpy as np
import json
import time
import random

# Configuration
CATEGORY_IDS = {
    'AppleA': 1000000000,
    'AppleB': 2000000000,
    'Peach': 3000000000,
    'Pear': 4000000000,
}

DATASETS = [
    {
        'img_dir': 'AppleA/FlowerImages',
        'label_dir': 'AppleA_Labels_1/AppleA_Labels',
        'category': 'AppleA',
        'supercategory': 'apple',
        'img_suffix': '.JPG',
        'label_rule': lambda img: img[-7:-4].lstrip('0') + '.png',  # IMG_0394.JPG -> 394.png
    },
    {
        'img_dir': 'AppleB_1/AppleB',
        'label_dir': 'AppleB_Labels_1/AppleB_Labels',
        'category': 'AppleB',
        'supercategory': 'apple',
        'img_suffix': '.bmp',
        'label_rule': lambda img: os.path.splitext(img)[0] + '.png',
    },
    {
        'img_dir': 'Peach_1/PeachSelected',
        'label_dir': 'PeachLabels_1/PeachLabels',
        'category': 'Peach',
        'supercategory': 'peach',
        'img_suffix': '.bmp',
        'label_rule': lambda img: os.path.splitext(img)[0] + '.png',
    },
    {
        'img_dir': 'Pear_1/Pear',
        'label_dir': 'PearLabels_2/PearLabels',
        'category': 'Pear',
        'supercategory': 'pear',
        'img_suffix': '.bmp',
        'label_rule': lambda img: os.path.splitext(img)[0] + '.png',
    },
]

INFO = {
    "description": "data",
    "version": "1.0",
    "year": 2025,
    "contributor": "search engine",
    "source": "no_augmentation",
    "license": {
        "name": "Creative Commons Attribution 4.0 International",
        "url": "https://creativecommons.org/licenses/by/4.0/"
    }
}

def gen_random_id():
    # Get last three digits of current timestamp
    tail = int(str(int(time.time()))[-3:])
    # Generate first 7 digits randomly (first digit not zero)
    front = random.randint(1000000, 9999999)
    return int(f"{front:07d}{tail:03d}")

def get_bboxes_from_mask(mask_path, img_h, img_w):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return []
    _, thresh = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bboxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # OpenCV origin is top-left, COCO is bottom-left, so convert y
        y_coco = img_h - (y + h)
        area = w * h
        bboxes.append({
            'bbox': [int(x), int(y_coco), int(w), int(h)],
            'area': int(area),
        })
    return bboxes

def process_dataset(cfg):
    img_dir = cfg['img_dir']
    label_dir = cfg['label_dir']
    category = cfg['category']
    supercategory = cfg['supercategory']
    img_suffix = cfg['img_suffix']
    label_rule = cfg['label_rule']
    category_id = CATEGORY_IDS[category]
    
    for img_name in os.listdir(img_dir):
        if not img_name.endswith(img_suffix):
            continue
        img_path = os.path.join(img_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Cannot read image: {img_path}")
            continue
        h, w = img.shape[:2]
        size = os.path.getsize(img_path)
        fmt = img_name.split('.')[-1].upper()
        label_name = label_rule(img_name)
        label_path = os.path.join(label_dir, label_name)
        bboxes = get_bboxes_from_mask(label_path, h, w) if os.path.exists(label_path) else []
        # Generate unique image_id
        image_id = gen_random_id()
        images = [{
            "id": image_id,
            "width": w,
            "height": h,
            "file_name": img_name,
            "size": size,
            "format": fmt,
            "url": "",
            "hash": "",
            "status": "success"
        }]
        annotations = []
        for bbox in bboxes:
            annotations.append({
                "id": gen_random_id(),
                "image_id": image_id,
                "category_id": category_id,
                "segmentation": [],
                "area": bbox['area'],
                "bbox": bbox['bbox']
            })
        categories = [{
            "id": category_id,
            "name": category,
            "supercategory": supercategory
        }]
        data = {
            "info": INFO,
            "images": images,
            "annotations": annotations,
            "categories": categories
        }
        json_name = os.path.splitext(img_name)[0] + '.json'
        json_path = os.path.join(img_dir, json_name)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Generated: {json_path}")

if __name__ == '__main__':
    for cfg in DATASETS:
        process_dataset(cfg) 