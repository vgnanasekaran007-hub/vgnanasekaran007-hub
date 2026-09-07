#!/usr/bin/env python3
"""
dotify.py - Convert photographs into SVG dot-matrix portraits.

Usage:
  python scripts/dotify.py me.png -o assets/portrait --cols 100 --equalize --detail 0.5 --color
"""

import argparse
import sys
import os
from PIL import Image, ImageOps, ImageEnhance

def process_image(input_path, output_path, cols=100, equalize=False, detail=0.5, color=False, bg_color=None):
    if not os.path.exists(input_path):
        print(f"Error: Input image '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path).convert("RGBA")
    orig_w, orig_h = img.size
    aspect_ratio = orig_h / orig_w

    rows = int(cols * aspect_ratio)

    # Work on a copy for color sampling
    img_resized = img.resize((cols, rows), Image.Resampling.LANCZOS)
    
    # Grayscale image for luminance processing
    gray = ImageOps.grayscale(img_resized.convert("RGB"))
    
    if equalize:
        gray = ImageOps.equalize(gray)
        # Boost contrast slightly after equalization for crisp detail
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.15)

    # Grid parameters
    cell_size = 10.0  # standard cell dimension in SVG user units
    svg_w = cols * cell_size
    svg_h = rows * cell_size
    max_radius = (cell_size / 2.0) * 0.94

    # Detail exponent tuning: lower detail -> sharper cutoff, higher detail -> softer response
    # detail = 0.5 gives a balanced gamma (~0.85) to retain facial details without noise
    gamma = 1.5 - (detail * 0.9)

    # Determine SVG output filename
    out_file = output_path
    if not out_file.lower().endswith(".svg"):
        out_file = out_file + ".svg"
    
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    svg_elements = []
    if bg_color:
        svg_elements.append(f'  <rect width="100%" height="100%" fill="{bg_color}" />')

    pixels_gray = gray.load()
    pixels_color = img_resized.load()

    for y in range(rows):
        for x in range(cols):
            lum = pixels_gray[x, y] / 255.0  # 0.0 to 1.0
            r_c, g_c, b_c, a_c = pixels_color[x, y]

            # If pixel is transparent, skip
            if a_c < 25:
                continue

            # Ignore extremely dark background noise
            if lum < 0.04:
                continue

            # Apply gamma / detail response
            norm_lum = lum ** gamma
            radius = max_radius * norm_lum

            if radius < 0.35:
                continue

            cx = (x + 0.5) * cell_size
            cy = (y + 0.5) * cell_size

            if color:
                fill_str = f"rgb({r_c},{g_c},{b_c})"
            else:
                fill_str = "#ffffff"

            svg_elements.append(
                f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="{fill_str}" />'
            )

    svg_content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" width="100%" height="auto" style="max-width: 500px; display: block; margin: 0 auto;">',
        *svg_elements,
        '</svg>'
    ]

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_content))

    print(f"Successfully generated dot-matrix SVG portrait: {out_file}")
    print(f"Grid size: {cols}x{rows} ({len(svg_elements)} dots rendered)")

def main():
    parser = argparse.ArgumentParser(description="Convert an image into an SVG dot-matrix portrait.")
    parser.add_argument("input", help="Path to input image (e.g., me.png)")
    parser.add_argument("-o", "--output", default="assets/portrait", help="Output path prefix or .svg file (default: assets/portrait)")
    parser.add_argument("--cols", type=int, default=100, help="Number of matrix columns (default: 100)")
    parser.add_argument("--equalize", action="store_true", help="Apply histogram equalization for preserving details")
    parser.add_argument("--detail", type=float, default=0.5, help="Detail weight between 0.0 and 1.0 (default: 0.5)")
    parser.add_argument("--color", action="store_true", help="Use original image colors for dots")
    parser.add_argument("--bg", type=str, default=None, help="Optional background color for SVG (e.g. #0d1117)")

    args = parser.parse_args()
    process_image(
        input_path=args.input,
        output_path=args.output,
        cols=args.cols,
        equalize=args.equalize,
        detail=args.detail,
        color=args.color,
        bg_color=args.bg
    )

if __name__ == "__main__":
    main()
