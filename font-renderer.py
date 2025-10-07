
import argparse
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

def render_text(text, font_path, image_path, size):
    """Renders text using a given font and saves it as an image."""
    try:
        font = ImageFont.truetype(font_path, size)
        
        # Create a dummy image to calculate the text size
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        
        # Get the bounding box of the text
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except TypeError:
            # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)

        img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        draw.text((10, 10), text, font=font, fill='black')
        img.save(image_path, 'PNG')
        return True
    except Exception as e:
        print(f"Error rendering text with {font_path}: {e}")
        return False

from fontTools.ttLib import TTFont

def inspect_char_metrics(font_path, char):
    """Inspects the metrics of a character in a font file."""
    try:
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        if not cmap or ord(char) not in cmap:
            print(f"Character '{char}' not found in font.")
            return

        glyph_name = cmap[ord(char)]
        hmtx = font['hmtx']
        advance_width, _ = hmtx[glyph_name]
        units_per_em = font['head'].unitsPerEm

        print(f"Metrics for character '{char}' in {os.path.basename(font_path)}:")
        print(f"  Advance Width: {advance_width}")
        print(f"  Units Per Em: {units_per_em}")

    except Exception as e:
        print(f"Could not inspect metrics for {font_path}: {e}")

def inspect_glyph_bbox(font_path, char):
    """Inspects the bounding box of a glyph in a font file."""
    try:
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        if not cmap or ord(char) not in cmap:
            print(f"Character '{char}' not found in font.")
            return

        glyph_name = cmap[ord(char)]
        glyph = font['glyf'][glyph_name]
        glyph.recalcBounds(font['glyf'])
        print(f"Glyph bounding box for character '{char}' in {os.path.basename(font_path)}:")
        print(f"  xMin: {glyph.xMin}")
        print(f"  yMin: {glyph.yMin}")
        print(f"  xMax: {glyph.xMax}")
        print(f"  yMax: {glyph.yMax}")

    except Exception as e:
        print(f"Could not inspect glyph bounding box for {font_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Render text with a specified font.')
    parser.add_argument('--font-size', type=int, default=24,
                        help='The font size to use for rendering.')
    parser.add_argument('--text', type=str, default='The quick brown fox jumps over the lazy dog.',
                        help='The text to render.')
    parser.add_argument('--font', type=str, required=True,
                        help='The path to the font file to use.')
    parser.add_argument('-o', '--output', type=str, default='output.png',
                        help='The output filename.')
    parser.add_argument('--preview', action='store_true',
                        help='Preview the output image using eog.')
    parser.add_argument('--inspect', type=str, help='Inspect the metrics of a specific character in the font.')
    parser.add_argument('--inspect-glyph-bbox', type=str, help='Inspect the bounding box of a specific glyph in the font.')
    args = parser.parse_args()

    if args.inspect:
        inspect_char_metrics(args.font, args.inspect)
        return
    
    if args.inspect_glyph_bbox:
        inspect_glyph_bbox(args.font, args.inspect_glyph_bbox)
        return

    if not os.path.exists(args.font):
        print(f"Error: Font file not found at {args.font}")
        return

    if render_text(args.text, args.font, args.output, args.font_size):
        print(f"Successfully rendered text to {args.output}")
        if args.preview:
            try:
                subprocess.run(['eog', args.output])
            except FileNotFoundError:
                print("eog not found. Please install it to use the --preview feature.")

if __name__ == '__main__':
    main()
