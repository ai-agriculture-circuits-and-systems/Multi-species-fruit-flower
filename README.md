# Multi-species Fruit Flower Detection Dataset

A dataset of flower images from apple, peach, and pear species, including both original images and corresponding ground truth masks and object detection annotation files. The dataset is designed for research in flower detection and segmentation in orchard environments.

## Dataset Overview

This dataset contains four main groups of fruit flower images and their corresponding ground truth and detection annotation files. The images were collected under various conditions to support robust algorithm development.

### Species and Sets
- **AppleA**: High-resolution images of apple flowers
- **AppleB**: Additional apple flower images
- **Peach**: Images of peach flowers
- **Pear**: Images of pear flowers

## Directory Structure

The dataset is organized as follows:

```
.
├── AppleA/FlowerImages/           # AppleA flower images (.JPG)
├── AppleA_Labels_1/AppleA_Labels/ # AppleA ground truth masks (.png)
├── AppleB_1/AppleB/               # AppleB flower images (.bmp)
├── AppleB_Labels_1/AppleB_Labels/ # AppleB ground truth masks (.png)
├── Peach_1/PeachSelected/         # Peach flower images (.bmp)
├── PeachLabels_1/PeachLabels/     # Peach ground truth masks (.png)
├── Pear_1/Pear/                   # Pear flower images (.bmp)
├── PearLabels_2/PearLabels/       # Pear ground truth masks (.png)
└── generate_coco_json.py          # Script to generate detection JSONs
```

- **Image folders** contain the original flower images for each species.
- **Label folders** contain binary mask images, where white pixels represent flower regions and black pixels represent background.
- For each image, a detection annotation JSON file is generated in the same directory as the image, with the same base name.

## Annotation JSON File Explanation

Each image has a corresponding JSON annotation file (COCO-like format) describing detected flower bounding boxes. The JSON structure is as follows:

```
{
  "info": { ... },
  "images": [
    {
      "id": <unique image id>,
      "width": <image width>,
      "height": <image height>,
      "file_name": <image file name>,
      "size": <file size in bytes>,
      "format": <file format>,
      "url": "",
      "hash": "",
      "status": "success"
    }
  ],
  "annotations": [
    {
      "id": <unique annotation id>,
      "image_id": <image id>,
      "category_id": <category id>,
      "segmentation": [],
      "area": <area of bbox>,
      "bbox": [x, y, width, height]
    },
    ...
  ],
  "categories": [
    {
      "id": <category id>,
      "name": <category name>,
      "supercategory": <supercategory name>
    }
  ]
}
```

- **images**: Metadata for the image.
- **annotations**: Each detected flower (from the mask) is represented by a bounding box (`bbox`), with coordinates `[x, y, width, height]` (origin at the bottom-left corner). If no mask is available, this array is empty.
- **categories**: Category and supercategory information for the image.

## How to Generate Detection Annotations

Run the provided script to generate JSON annotation files for all images:

```
python generate_coco_json.py
```

## Applications

- Flower detection and segmentation
- Multi-species flower identification
- Precision agriculture and orchard management
- Robustness testing in uncontrolled environments

## Citation

If you use this dataset, please cite:

Dias, Philipe A.; Tabb, Amy; Medeiros, Henry (2018). Data from: Multi-species fruit flower detection using a refined semantic segmentation network. Ag Data Commons. https://doi.org/10.15482/USDA.ADC/1423466

## Contact

For questions about the dataset, please contact:
- Amy Tabb (amy.tabb@ars.usda.gov)