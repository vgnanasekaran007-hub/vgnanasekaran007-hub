#!/usr/bin/env python3
"""
dotify.py - Convert photographs into animated SVG dot-matrix portraits.

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

    # Downsample image for matrix grid sampling
    img_resized = img.resize((cols, rows), Image.Resampling.LANCZOS)
    
    # Grayscale image for luminance processing
    gray = ImageOps.grayscale(img_resized.convert("RGB"))
    
    if equalize:
        gray = ImageOps.equalize(gray)
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.15)

    # Grid dimension setup
    cell_size = 10.0
    padding = 8.0
    grid_w = cols * cell_size
    grid_h = rows * cell_size
    svg_w = grid_w + (padding * 2.0)
    svg_h = grid_h + (padding * 2.0)
    max_radius = (cell_size / 2.0) * 0.94

    gamma = 1.5 - (detail * 0.9)

    out_file = output_path
    if not out_file.lower().endswith(".svg"):
        out_file = out_file + ".svg"
    
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    # Keyframe animation styles matching the specified pattern
    max_total_delay = 2.500
    delay_step = max_total_delay / max(1, rows - 1)

    css_rules = [
        "@keyframes rv{from{opacity:0}to{opacity:1}}",
        ".rw{animation:rv 0.45s ease-out both}"
    ]
    for r in range(rows):
        d = r * delay_step
        css_rules.append(f".r{r}{{animation-delay:{d:.3f}s}}")

    style_block = f"<style>{''.join(css_rules)}</style>"

    pixels_gray = gray.load()
    pixels_color = img_resized.load()

    row_groups = []
    total_dots = 0

    for y in range(rows):
        row_circles = []
        for x in range(cols):
            lum = pixels_gray[x, y] / 255.0
            r_c, g_c, b_c, a_c = pixels_color[x, y]

            if a_c < 25 or lum < 0.04:
                continue

            norm_lum = lum ** gamma
            radius = max_radius * norm_lum

            if radius < 0.35:
                continue

            cx = (x + 0.5) * cell_size
            cy = (y + 0.5) * cell_size

            if color:
                fill_str = f"#{r_c:02x}{g_c:02x}{b_c:02x}"
            else:
                fill_str = "#ffffff"

            row_circles.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.2f}" fill="{fill_str}"/>'
            )
            total_dots += 1

        if row_circles:
            group_str = f'    <g class="rw r{y}">\n      ' + "".join(row_circles) + '\n    </g>'
            row_groups.append(group_str)

    bg_rect = f'  <rect width="100%" height="100%" fill="{bg_color}"/>\n' if bg_color else ""

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" width="{svg_w:.1f}" height="{svg_h:.1f}" role="img" aria-label="dot-matrix portrait">
{style_block}
{bg_rect}  <g transform="translate({padding:.1f},{padding:.1f})">
''' + "\n".join(row_groups) + '''
  </g>
</svg>'''

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"Successfully generated animated dot-matrix SVG portrait: {out_file}")
    print(f"Grid size: {cols}x{rows} ({total_dots} dots rendered)")

def main():
    parser = argparse.ArgumentParser(description="Convert an image into an animated SVG dot-matrix portrait.")
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
