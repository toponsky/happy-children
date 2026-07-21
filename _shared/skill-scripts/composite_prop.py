#!/usr/bin/env python3
"""Composite a prop reference image onto a scene, with optional old-prop removal.
Usage: python3 composite_prop.py <prop.png> <scene.png> [options]

This solves the problem of making the same prop (glasses, bag, etc.) appear 
consistently across multiple scene images when Flux txt2img can't guarantee 
prop shape/color consistency.
"""

from PIL import Image, ImageFilter
import numpy as np
import argparse, sys

def crop_to_prop(img_path):
    """Crop white-background prop image to tight bounding box, make background transparent."""
    img = Image.open(img_path).convert('RGBA')
    arr = np.array(img)
    
    # Find non-white pixels
    non_white = (arr[:,:,0] < 230) | (arr[:,:,1] < 230) | (arr[:,:,2] < 230)
    rows = np.any(non_white, axis=1)
    cols = np.any(non_white, axis=0)
    if not rows.any():
        print(f"ERROR: No non-white pixels found in {img_path}", file=sys.stderr)
        sys.exit(1)
    
    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]
    
    # Add padding
    pad = 20
    ymin = max(0, ymin - pad)
    ymax = min(arr.shape[0], ymax + pad)
    xmin = max(0, xmin - pad)
    xmax = min(arr.shape[1], xmax + pad)
    
    # Crop and make white background transparent
    cropped = arr[ymin:ymax, xmin:xmax]
    white = (cropped[:,:,0] > 230) & (cropped[:,:,1] > 230) & (cropped[:,:,2] > 230)
    cropped[white, 3] = 0
    
    return Image.fromarray(cropped, 'RGBA')

def composite(scene_path, prop_path, out_path, 
              prop_width=200, rotation=-20, 
              pos_x=None, pos_y=None,
              blur_old_region=False, blur_radius=15):
    """
    Composite prop onto scene.
    
    Args:
        scene_path: Path to scene image
        prop_path: Path to prop reference image (white background)
        out_path: Output path
        prop_width: Desired width of prop in scene (pixels)
        rotation: Rotation angle (negative = counter-clockwise)
        pos_x, pos_y: Position in scene. If None, auto-center at bottom.
        blur_old_region: If True, blur area where old prop might be before pasting
        blur_radius: Gaussian blur radius for old prop removal
    """
    scene = Image.open(scene_path).convert('RGBA')
    prop = crop_to_prop(prop_path)
    
    # Scale prop
    scale = prop_width / prop.size[0]
    new_w, new_h = int(prop.size[0] * scale), int(prop.size[1] * scale)
    prop_scaled = prop.resize((new_w, new_h), Image.LANCZOS)
    prop_scaled = prop_scaled.rotate(rotation, expand=True, resample=Image.BICUBIC)
    
    gw, gh = prop_scaled.size
    sw, sh = scene.size
    
    # Auto-position if not specified
    if pos_x is None:
        pos_x = (sw - gw) // 2
    if pos_y is None:
        pos_y = sh - gh - 200  # Bottom area
    
    # Optional: blur old prop area
    if blur_old_region:
        scene_arr = np.array(scene)
        y1 = max(0, pos_y - 10)
        y2 = min(sh, pos_y + gh + 10)
        x1 = max(0, pos_x - 10)
        x2 = min(sw, pos_x + gw + 10)
        region = scene_arr[y1:y2, x1:x2].copy()
        blurred = np.array(Image.fromarray(region).filter(ImageFilter.GaussianBlur(radius=blur_radius)))
        scene_arr[y1:y2, x1:x2] = blurred
        scene = Image.fromarray(scene_arr, 'RGBA')
    
    # Feathered paste
    # Light blur on alpha for soft edges
    prop_arr = np.array(prop_scaled).astype(np.float32)
    alpha = prop_arr[:,:,3].copy()
    alpha_img = Image.fromarray(alpha.astype(np.uint8))
    alpha_blur = alpha_img.filter(ImageFilter.GaussianBlur(radius=2))
    prop_arr[:,:,3] = np.array(alpha_blur)
    prop_feathered = Image.fromarray(prop_arr.astype(np.uint8), 'RGBA')
    
    scene.paste(prop_feathered, (pos_x, pos_y), prop_feathered)
    scene.convert('RGB').save(out_path)
    
    print(f"Composite: prop {gw}x{gh} at ({pos_x},{pos_y}), scene {sw}x{sh}")
    print(f"Saved: {out_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Composite prop onto scene')
    parser.add_argument('prop', help='Prop reference image (white background)')
    parser.add_argument('scene', help='Scene image')
    parser.add_argument('-o', '--output', default='composited.png', help='Output path')
    parser.add_argument('-w', '--width', type=int, default=200, help='Prop width in pixels')
    parser.add_argument('-r', '--rotate', type=float, default=-20, help='Rotation angle')
    parser.add_argument('-x', type=int, help='X position')
    parser.add_argument('-y', type=int, help='Y position')
    parser.add_argument('--blur-old', action='store_true', 
                       help='Blur area to remove old prop before pasting')
    parser.add_argument('--blur-radius', type=int, default=15, 
                       help='Blur radius for old prop removal')
    
    args = parser.parse_args()
    composite(args.scene, args.prop, args.output,
             prop_width=args.width, rotation=args.rotate,
             pos_x=args.x, pos_y=args.y,
             blur_old_region=args.blur_old, blur_radius=args.blur_radius)
