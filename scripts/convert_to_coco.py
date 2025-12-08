#!/usr/bin/env python3
"""
Convert Multi-species-fruit-flower dataset annotations to COCO JSON format.
Based on the standardized dataset structure specification.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

def read_split_list(split_file: Path) -> List[str]:
    """Read image base names (without extension) from a split file."""
    if not split_file.exists():
        return []
    lines = [line.strip() for line in split_file.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]

def image_size(image_path: Path) -> Tuple[int, int]:
    """Return (width, height) for an image path using PIL."""
    with Image.open(image_path) as img:
        return img.width, img.height

def parse_csv_boxes(csv_path: Path) -> List[Dict]:
    """Parse a single CSV file and return bounding boxes."""
    if not csv_path.exists():
        return []
    
    boxes = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row.get('x', 0))
                y = float(row.get('y', 0))
                width = float(row.get('width', 0))
                height = float(row.get('height', 0))
                label = int(row.get('label', 1))
                
                if width > 0 and height > 0:
                    boxes.append({
                        'bbox': [x, y, width, height],
                        'area': width * height,
                        'category_id': label
                    })
            except (ValueError, KeyError):
                continue
    
    return boxes

def collect_annotations_for_split(
    category_root: Path,
    split: str,
    category_name: str,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Collect COCO dictionaries for images, annotations, and categories."""
    images_dir = category_root / "images"
    annotations_dir = category_root / "csv"
    sets_dir = category_root / "sets"
    
    split_file = sets_dir / f"{split}.txt"
    image_stems = set(read_split_list(split_file))
    
    if not image_stems:
        # Fall back to all images if no split file
        image_stems = {p.stem for p in images_dir.glob("*.jpg")}
        image_stems.update({p.stem for p in images_dir.glob("*.JPG")})
        image_stems.update({p.stem for p in images_dir.glob("*.bmp")})
        image_stems.update({p.stem for p in images_dir.glob("*.BMP")})
    
    images: List[Dict] = []
    anns: List[Dict] = []
    
    # Get category name from labelmap
    labelmap_path = category_root / "labelmap.json"
    if labelmap_path.exists():
        with open(labelmap_path, 'r') as f:
            labelmap = json.load(f)
        category_obj = next((item for item in labelmap if item['object_id'] > 0), None)
        if category_obj:
            category_name_singular = category_obj['object_name']
        else:
            category_name_singular = category_name[:-1] if category_name.endswith('s') else category_name
    else:
        category_name_singular = category_name[:-1] if category_name.endswith('s') else category_name
    
    categories: List[Dict] = [
        {"id": 1, "name": category_name_singular, "supercategory": category_name_singular}
    ]
    
    image_id_counter = 1
    ann_id_counter = 1
    
    for stem in sorted(image_stems):
        img_path = None
        for ext in ['.jpg', '.JPG', '.bmp', '.BMP', '.png', '.PNG']:
            potential_path = images_dir / f"{stem}{ext}"
            if potential_path.exists():
                img_path = potential_path
                break
        
        if not img_path or not img_path.exists():
            continue
        
        width, height = image_size(img_path)
        images.append({
            "id": image_id_counter,
            "file_name": f"{category_name}/images/{img_path.name}",
            "width": width,
            "height": height,
        })
        
        csv_path = annotations_dir / f"{stem}.csv"
        for box in parse_csv_boxes(csv_path):
            anns.append({
                "id": ann_id_counter,
                "image_id": image_id_counter,
                "category_id": box['category_id'],
                "bbox": box['bbox'],
                "area": box['area'],
                "iscrowd": 0,
            })
            ann_id_counter += 1
        
        image_id_counter += 1
    
    return images, anns, categories

def build_coco_dict(
    images: List[Dict],
    anns: List[Dict],
    categories: List[Dict],
    description: str,
    url: str,
    year: int,
) -> Dict:
    """Build a complete COCO dict from components."""
    return {
        "info": {
            "year": year,
            "version": "1.0.0",
            "description": description,
            "url": url,
        },
        "images": images,
        "annotations": anns,
        "categories": categories,
        "licenses": [],
    }

def convert(
    root: Path,
    out_dir: Path,
    categories: List[str],
    splits: List[str],
) -> None:
    """Convert selected categories and splits to COCO JSON files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for category in categories:
        category_root = root / category
        
        if not category_root.exists():
            print(f"Warning: Category directory {category} not found, skipping")
            continue
        
        for split in splits:
            images, anns, cat_list = collect_annotations_for_split(
                category_root, split, category
            )
            desc = f"Multi-species fruit flower {category} {split} split"
            url = "https://doi.org/10.15482/USDA.ADC/1423466"
            coco = build_coco_dict(images, anns, cat_list, desc, url, 2018)
            out_path = out_dir / f"{category}_instances_{split}.json"
            out_path.write_text(json.dumps(coco, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Generated: {out_path} ({len(images)} images, {len(anns)} annotations)")

def main():
    parser = argparse.ArgumentParser(description="Convert Multi-species-fruit-flower annotations to COCO JSON")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Dataset root directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for COCO JSON files (default: <root>/annotations)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Category names to convert (default: all categories)",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        choices=["train", "val", "test"],
        help="Dataset splits to generate (default: train val test)",
    )
    
    args = parser.parse_args()
    
    if args.out is None:
        args.out = args.root / "annotations"
    
    # If categories not specified, find all category directories
    if args.categories is None:
        args.categories = [
            d.name for d in args.root.iterdir()
            if d.is_dir() and not d.name.startswith('.') and 
            d.name not in ['scripts', 'annotations', 'data', 'docs', 'extra', 
                          'AppleA', 'AppleA_Labels_1', 'AppleALabels_Train',
                          'AppleB_1', 'AppleB_Labels_1',
                          'Peach_1', 'PeachLabels_1',
                          'Pear_1', 'PearLabels_2']
        ]
    
    convert(
        root=args.root,
        out_dir=args.out,
        categories=args.categories,
        splits=args.splits,
    )

if __name__ == "__main__":
    main()

