#!/usr/bin/env python3
"""
标准化 Multi-species-fruit-flower 数据集结构
根据标准化数据集结构规范进行重组
"""
import json
import csv
import shutil
import random
from pathlib import Path
from PIL import Image

# 类别映射（标准化为复数形式）
CATEGORIES = {
    'AppleA': ('apple', 'apples'),
    'AppleB': ('apple', 'apples'),
    'Peach': ('peach', 'peaches'),
    'Pear': ('pear', 'pears'),
}

# 原始目录映射（位于 data/original/ 目录下）
SOURCE_DIRS = {
    'AppleA': {
        'images': 'data/original/AppleA/FlowerImages',
        'labels': 'data/original/AppleA_Labels_1/AppleA_Labels',
        'img_suffix': '.JPG',
        'label_rule': lambda img: img[-7:-4].lstrip('0') + '.png',  # IMG_0394.JPG -> 394.png
    },
    'AppleB': {
        'images': 'data/original/AppleB_1/AppleB',
        'labels': 'data/original/AppleB_Labels_1/AppleB_Labels',
        'img_suffix': '.bmp',
        'label_rule': lambda img: Path(img).stem + '.png',
    },
    'Peach': {
        'images': 'data/original/Peach_1/PeachSelected',
        'labels': 'data/original/PeachLabels_1/PeachLabels',
        'img_suffix': '.bmp',
        'label_rule': lambda img: Path(img).stem + '.png',
    },
    'Pear': {
        'images': 'data/original/Pear_1/Pear',
        'labels': 'data/original/PearLabels_2/PearLabels',
        'img_suffix': '.bmp',
        'label_rule': lambda img: Path(img).stem + '.png',
    },
}

def create_directory_structure(root: Path):
    """创建标准化目录结构"""
    categories = {}
    for cat_name, (singular, plural) in CATEGORIES.items():
        # 使用复数形式作为目录名
        cat_dir = root / plural
        for subdir in ['csv', 'json', 'images', 'segmentations', 'sets']:
            (cat_dir / subdir).mkdir(parents=True, exist_ok=True)
        categories[cat_name] = {
            'singular': singular,
            'plural': plural,
            'dir': cat_dir
        }
    return categories

def create_labelmap(category_dir: Path, singular: str):
    """创建 labelmap.json"""
    labelmap = [
        {
            "object_id": 0,
            "label_id": 0,
            "keyboard_shortcut": "0",
            "object_name": "background"
        },
        {
            "object_id": 1,
            "label_id": 1,
            "keyboard_shortcut": "1",
            "object_name": singular
        }
    ]
    labelmap_path = category_dir / 'labelmap.json'
    labelmap_path.write_text(json.dumps(labelmap, indent=2, ensure_ascii=False), encoding='utf-8')

def convert_bbox_y_from_bottom_left(bbox, img_height):
    """将bbox的y坐标从底部原点转换为顶部原点（COCO格式）"""
    x, y_bottom, w, h = bbox
    y_top = img_height - (y_bottom + h)
    return [x, y_top, w, h]

def create_csv_annotation(csv_path: Path, annotations: list):
    """创建 CSV 标注文件"""
    rows = []
    for idx, ann in enumerate(annotations):
        bbox = ann.get('bbox', [])
        if len(bbox) == 4:
            rows.append({
                'item': idx,
                'x': bbox[0],
                'y': bbox[1],
                'width': bbox[2],
                'height': bbox[3],
                'label': 1
            })
    
    if rows:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['item', 'x', 'y', 'width', 'height', 'label'])
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text('#item,x,y,width,height,label\n', encoding='utf-8')

def create_json_annotation(json_path: Path, image_info: dict, annotations: list, category: dict):
    """创建 JSON 标注文件（只包含该图像相关的类别）"""
    annotation_data = {
        "info": {
            "description": "Multi-species fruit flower dataset",
            "version": "1.0",
            "year": 2018,
            "contributor": "Dias, Philipe A.; Tabb, Amy; Medeiros, Henry",
            "source": "original",
            "license": {
                "name": "Creative Commons Attribution 4.0 International",
                "url": "https://creativecommons.org/licenses/by/4.0/"
            }
        },
        "images": [image_info],
        "annotations": annotations,
        "categories": [category]  # 只包含该图像相关的类别
    }
    
    json_path.write_text(json.dumps(annotation_data, indent=2, ensure_ascii=False), encoding='utf-8')

def process_images(root: Path, categories: dict):
    """处理图像和标注文件"""
    image_files = {}
    
    # 先收集所有类别到标准目录的映射
    category_to_dir = {}
    for cat_name, cat_info in categories.items():
        plural = cat_info['plural']
        if plural not in category_to_dir:
            category_to_dir[plural] = []
        category_to_dir[plural].append(cat_name)
    
    for cat_name, cat_info in categories.items():
        source_cfg = SOURCE_DIRS[cat_name]
        source_img_dir = root / source_cfg['images']
        source_label_dir = root / source_cfg['labels']
        cat_dir = cat_info['dir']
        img_suffix = source_cfg['img_suffix']
        label_rule = source_cfg['label_rule']
        
        if not source_img_dir.exists():
            print(f"Warning: Source image directory {source_img_dir} not found, skipping {cat_name}")
            continue
        
        # 使用复数形式作为键（AppleA和AppleB都映射到apples）
        plural = cat_info['plural']
        if plural not in image_files:
            image_files[plural] = []
        
        cat_images = []
        
        # 处理图像文件
        for img_file in source_img_dir.glob(f'*{img_suffix}'):
            if not img_file.is_file():
                continue
            
            stem = img_file.stem
            
            # 检查文件是否已存在（避免AppleA和AppleB的文件名冲突）
            dest_img_path = cat_dir / 'images' / img_file.name
            if dest_img_path.exists():
                # 如果文件名冲突，添加前缀
                dest_img_path = cat_dir / 'images' / f"{cat_name}_{img_file.name}"
                stem = f"{cat_name}_{stem}"
            
            # 读取原始JSON（如果存在）
            json_file = source_img_dir / f"{img_file.stem}.json"
            orig_data = None
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    orig_data = json.load(f)
            
            # 获取图像信息
            with Image.open(img_file) as img:
                width, height = img.size
                img_format = img.format or img_suffix[1:].upper()
            
            file_size = img_file.stat().st_size
            
            # 复制图像到类别目录
            shutil.copy2(img_file, dest_img_path)
            
            # 处理标注
            annotations = []
            if orig_data and orig_data.get('annotations'):
                for ann in orig_data['annotations']:
                    bbox = ann.get('bbox', [])
                    if len(bbox) == 4:
                        # 检查bbox坐标系统（原始脚本使用bottom-left，需要转换为top-left）
                        # 如果y坐标很小（接近0），可能是从底部开始的
                        if bbox[1] < height / 2:  # 可能是bottom-left坐标
                            bbox = convert_bbox_y_from_bottom_left(bbox, height)
                        
                        annotations.append({
                            "id": ann.get('id', 0),
                            "image_id": orig_data['images'][0].get('id', 0),
                            "category_id": 1,
                            "segmentation": [],
                            "area": ann.get('area', bbox[2] * bbox[3]),
                            "bbox": bbox
                        })
            
            # 创建CSV标注
            csv_path = cat_dir / 'csv' / f"{stem}.csv"
            create_csv_annotation(csv_path, annotations)
            
            # 创建JSON标注
            json_image_info = {
                "id": orig_data['images'][0].get('id', 0) if orig_data else 0,
                "width": width,
                "height": height,
                "file_name": dest_img_path.name,
                "size": file_size,
                "format": img_format,
                "url": "",
                "hash": "",
                "status": "success"
            }
            
            json_category = {
                "id": 1,
                "name": cat_info['singular'],
                "supercategory": cat_info['singular']
            }
            
            json_path = cat_dir / 'json' / f"{stem}.json"
            create_json_annotation(json_path, json_image_info, annotations, json_category)
            
            # 复制分割掩码（如果存在）
            label_name = label_rule(img_file.name)
            label_path = source_label_dir / label_name
            if label_path.exists():
                dest_mask_path = cat_dir / 'segmentations' / label_name
                shutil.copy2(label_path, dest_mask_path)
            
            cat_images.append(stem)
            image_files[plural].append(stem)
        
        print(f"{cat_name} -> {plural}: {len(cat_images)} images processed")
    
    return image_files

def create_splits(root: Path, categories: dict, image_files: dict):
    """创建数据集划分文件"""
    # 读取原始划分文件（包含扩展名，位于 data/original/ 目录）
    train_file = root / 'data' / 'original' / 'train.txt'
    val_file = root / 'data' / 'original' / 'val_0.txt'
    
    train_images = set()
    val_images = set()
    
    if train_file.exists():
        train_images = set(line.strip() for line in train_file.read_text(encoding='utf-8').splitlines() if line.strip())
    if val_file.exists():
        val_images = set(line.strip() for line in val_file.read_text(encoding='utf-8').splitlines() if line.strip())
    
    # 为每个类别创建划分（使用复数形式作为键）
    for plural, stems in image_files.items():
        # 找到对应的类别目录
        cat_dir = None
        for cat_name, cat_info in categories.items():
            if cat_info['plural'] == plural:
                cat_dir = cat_info['dir']
                break
        if not cat_dir:
            continue
        
        sets_dir = cat_dir / 'sets'
        images_dir = cat_dir / 'images'
        
        # 获取实际图像文件名（带扩展名）
        actual_files = {}
        for stem in stems:
            for ext in ['.JPG', '.jpg', '.BMP', '.bmp', '.PNG', '.png']:
                img_file = images_dir / f"{stem}{ext}"
                if img_file.exists():
                    actual_files[stem] = img_file.name
                    break
        
        # 根据文件名匹配划分
        cat_train = []
        cat_val = []
        cat_test = []
        
        for stem in stems:
            file_name = actual_files.get(stem, stem)
            # 检查是否在原始划分文件中（支持带扩展名和不带扩展名的匹配）
            if file_name in train_images or stem in train_images:
                cat_train.append(stem)
            elif file_name in val_images or stem in val_images:
                cat_val.append(stem)
            else:
                cat_test.append(stem)
        
        # 如果没有划分，使用默认比例
        if not cat_train and not cat_val:
            random.seed(42)
            shuffled = stems.copy()
            random.shuffle(shuffled)
            total = len(shuffled)
            train_end = int(total * 0.7)
            val_end = train_end + int(total * 0.15)
            cat_train = shuffled[:train_end]
            cat_val = shuffled[train_end:val_end]
            cat_test = shuffled[val_end:]
        
        # 写入划分文件
        (sets_dir / 'train.txt').write_text('\n'.join(cat_train) + '\n', encoding='utf-8')
        (sets_dir / 'val.txt').write_text('\n'.join(cat_val) + '\n', encoding='utf-8')
        (sets_dir / 'test.txt').write_text('\n'.join(cat_test) + '\n', encoding='utf-8')
        (sets_dir / 'all.txt').write_text('\n'.join(stems) + '\n', encoding='utf-8')
        (sets_dir / 'train_val.txt').write_text('\n'.join(cat_train + cat_val) + '\n', encoding='utf-8')
        
        print(f"{plural}: train={len(cat_train)}, val={len(cat_val)}, test={len(cat_test)}, total={len(stems)}")

def main():
    root = Path(__file__).parent.parent
    
    print("Creating directory structure...")
    categories = create_directory_structure(root)
    
    print("Creating labelmaps...")
    for cat_name, cat_info in categories.items():
        create_labelmap(cat_info['dir'], cat_info['singular'])
    
    print("Processing images and annotations...")
    image_files = process_images(root, categories)
    
    print("Creating dataset splits...")
    create_splits(root, categories, image_files)
    
    print("\nStandardization complete!")
    total = sum(len(files) for files in image_files.values())
    print(f"Processed {total} images across {len(categories)} categories")

if __name__ == '__main__':
    main()

