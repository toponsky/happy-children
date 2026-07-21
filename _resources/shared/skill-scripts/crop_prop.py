#!/usr/bin/env python3
"""Crop and transparentize a white-background prop reference image.
Usage: python3 crop_prop.py <input.png> <output.png> [--size WIDTH] [--pos X Y] [--rotate DEG] [--scene SCENE.png]
"""
import sys, argparse
from PIL import Image
import numpy as np

def crop_to_prop(img_path, output_path):
    """Crop to tight bounding box of non-white pixels, make white transparent."""
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img)
    
    non_white = (arr[:,:,0] < 230) | (arr[:,:,1] < 230) | (arr[:,:,2] < 230)
    if not non_white.any():
        print("ERROR: no non-white pixels found")
        sys.exit(1)
    
    rows = np.any(non_white, axis=1)
    cols = np.any(non_white, axis=0)
    ymin, ymax = int(np.where(rows)[0][0]), int(np.where(rows)[0][-1])
    xmin, xmax = int(np.where(cols)[0][0]), int(np.where(cols)[0][-1])
    
    pad = 20
    ymin = max(0, ymin - pad)
    ymax = min(arr.shape[0], ymax + pad)
    xmin = max(0, xmin - pad)
    xmax = min(arr.shape[1], xmax + pad)
    
    cropped = arr[ymin:ymax, xmin:xmax]
    
    # Make near-white pixels transparent
    white = (cropped[:,:,0] > 230) & (cropped[:,:,1] > 230) & (cropped[:,:,2] > 230)
    cropped[white, 3] = 0
    
    out = Image.fromarray(cropped, "RGBA")
    out.save(output_path)
    print(f"Cropped: {xmax-xmin}x{ymax-ymin} -> {output_path}")
    return out.size

def composite(scene_path, prop_path, output_path, size, pos, rotate):
    """Paste prop onto scene."""
    scene = Image.open(scene_path).convert("RGBA")
    prop = Image.open(prop_path)
    
    # Scale
    scale = size / prop.size[0]
    new_w, new_h = int(prop.size[0] * scale), int(prop.size[1] * scale)
    prop = prop.resize((new_w, new_h), Image.LANCZOS)
    
    # Rotate
    if rotate:
        prop = prop.rotate(rotate, expand=True, resample=Image.BICUBIC)
    
    # Paste
    scene.paste(prop, pos, prop)
    scene.convert("RGB").save(output_path)
    print(f"Composited: {prop.size} at {pos} -> {output_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Input prop image (white background)")
    p.add_argument("output", help="Output path")
    p.add_argument("--size", type=int, help="Target width in pixels (for compositing)")
    p.add_argument("--pos", nargs=2, type=int, help="Paste position X Y (for compositing)")
    p.add_argument("--rotate", type=float, default=0, help="Rotation degrees")
    p.add_argument("--scene", help="Scene image to composite onto")
    
    args = p.parse_args()
    
    if args.scene and args.size and args.pos:
        composite(args.scene, args.input, args.output, args.size, tuple(args.pos), args.rotate)
    else:
        crop_to_prop(args.input, args.output)
