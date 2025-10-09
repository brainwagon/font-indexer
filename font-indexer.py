import os
import argparse
import markdown
import warnings
import logging
import sys
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*is a bogus value.*")
logging.getLogger('fontTools').setLevel(logging.ERROR)


def get_font_info(font_path):
    """Extracts information from a TTF font file."""
    try:
        font = TTFont(font_path)
        names = {}
        for record in font['name'].names:
            names[record.nameID] = record.toUnicode()
        
        return {
            'family': names.get(1, 'N/A'),
            'style': names.get(2, 'N/A'),
            'full_name': names.get(4, 'N/A'),
            'version': names.get(5, 'N/A'),
            'copyright': names.get(0, 'N/A'),
        }
    except Exception as e:
        print(f"Error reading {font_path}: {e}")
        return None

def render_text(text, font_path, image_path, size):
    """Renders text using a given font and saves it as an image."""
    try:
        font = ImageFont.truetype(font_path, size)
        
        # Get font metrics for accurate height calculation
        ascent, descent = font.getmetrics()

        # Create a dummy image to calculate the text width
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        
        # Get the bounding box of the text to determine width
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except TypeError:
            # Fallback for older Pillow versions
            text_width, _ = draw.textsize(text, font=font)

        # Add padding around the text
        padding = 10
        img_width = text_width + (2 * padding)
        # Calculate image height using font's global ascent and descent
        img_height = ascent + abs(descent) + (2 * padding)

        img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Position text: (x, y) where y is the top of the text.
        # The top of the text should be at `padding` to leave space for ascenders.
        draw.text((padding, padding), text, font=font, fill='black')
        img.save(image_path, 'PNG')
        return True
    except Exception as e:
        print(f"Error rendering text with {font_path}: {e}")
        return False

def find_fonts(directory):
    """Finds all TTF fonts in a directory."""
    fonts = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.ttf'):
                fonts.append(os.path.join(root, file))
    return fonts

def has_required_chars(font_path):
    """Checks if a font has all required characters (A-Z, a-z, 0-9)."""
    try:
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        if not cmap:
            return False

        required_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        for char in required_chars:
            if ord(char) not in cmap:
                return False
        return True
    except Exception as e:
        print(f"Could not check characters for {font_path}: {e}")
        return False

def check_font_metrics(font_path):
    """Checks for common font metric issues."""
    try:
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        if not cmap:
            return False, "No cmap table found"

        hmtx = font['hmtx']
        units_per_em = font['head'].unitsPerEm
        
        required_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        alphanumeric_widths = []
        for char in required_chars:
            if ord(char) not in cmap:
                continue
            glyph_name = cmap[ord(char)]
            advance_width, _ = hmtx[glyph_name]
            alphanumeric_widths.append(advance_width)

            if advance_width == 0:
                return False, f"Character '{char}' has zero width"
            
            if advance_width > (units_per_em * 10):
                return False, f"Character '{char}' has excessively large width"

        if not alphanumeric_widths:
            return False, "No alphanumeric characters found"

        # Check for space character issues
        if ord(' ') not in cmap:
            return False, "No space character"

        average_width = sum(alphanumeric_widths) / len(alphanumeric_widths)
        space_glyph_name = cmap[ord(' ')]
        space_advance_width, _ = hmtx[space_glyph_name]

        if space_advance_width > (average_width * 3):
            return False, "Space character is excessively wide"

        return True, ""
    except Exception as e:
        return False, f"Could not check metrics: {e}"

def slow_check_font(font_path, size=24):
    """Renders a test string with and without spaces to check for kerning issues."""
    try:
        font = ImageFont.truetype(font_path, size)
        test_string_with_spaces = "A B C D E"
        test_string_no_spaces = "ABCDE"

        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        try:
            width_with_spaces = draw.textbbox((0, 0), test_string_with_spaces, font=font)[2]
            width_no_spaces = draw.textbbox((0, 0), test_string_no_spaces, font=font)[2]
            space_width = draw.textbbox((0,0), " ", font=font)[2]
        except TypeError:
            width_with_spaces = draw.textsize(test_string_with_spaces, font=font)[0]
            width_no_spaces = draw.textsize(test_string_no_spaces, font=font)[0]
            space_width = draw.textsize(" ", font=font)[0]

        # A rough heuristic: if the difference in width is more than 4 times the width of a single space
        # this suggests a kerning issue.
        if (width_with_spaces - width_no_spaces) > (space_width * 4):
            return False, "Potential kerning issue"

        return True, ""
    except Exception as e:
        return False, f"Could not perform slow check: {e}"

def main():
    parser = argparse.ArgumentParser(description='Generate an HTML index of fonts.')
    parser.add_argument('--text', type=str, default='The quick brown fox jumps over the lazy dog.',
                        help='The text to render for each font.')
    parser.add_argument('--output-dir', type=str, default='renders',
                        help='The directory to save rendered images.')
    parser.add_argument('--html-file', type=str, default='index.html',
                        help='The name of the output HTML file.')
    parser.add_argument('--font-size', type=int, default=24,
                        help='The font size to use for rendering.')
    parser.add_argument('--slow-check', action='store_true',
                        help='Perform a slower, more thorough check for font quality issues.')
    parser.add_argument('--font-dir', type=str, default='.',
                        help='Directory to search for TrueType and OpenType fonts (default: current directory).')
    parser.add_argument('-n', '--number', type=int, default=None,
                        help='Limit the total number of files converted to the specified number.')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    fonts = find_fonts(args.font_dir)

    if args.number is not None:
        fonts = fonts[:args.number]

    total_processed_fonts = 0
    fonts_with_issues = 0
    table_rows = []

    font_iterator = sorted(fonts)
    if sys.stdout.isatty():
        font_iterator = tqdm(font_iterator, desc="Processing fonts", unit="font")

    for font_path in font_iterator:
        if not has_required_chars(font_path):
            if sys.stdout.isatty():
                tqdm.write(f"Skipping {os.path.basename(font_path)} (missing required characters)")
            continue

        info = get_font_info(font_path)
        if not info:
            continue

        metrics_ok, quality_reason = check_font_metrics(font_path)
        if args.slow_check and metrics_ok:
            metrics_ok, reason = slow_check_font(font_path, args.font_size)
            if not metrics_ok:
                quality_reason = reason

        quality_icon = '&#9989;' if metrics_ok else '&#10060;'
        title_attr = f'title="{quality_reason}"' if not metrics_ok else ''

        relative_font_path = os.path.relpath(font_path)
        image_name = os.path.basename(font_path) + '.png'
        image_path = os.path.join(args.output_dir, image_name)
        
        if render_text(args.text, font_path, image_path, args.font_size):
            total_processed_fonts += 1
            if not metrics_ok:
                fonts_with_issues += 1
            
            table_rows.append('<tr>')
            table_rows.append(f'<td class="font-name-col">{info["full_name"]}</td>')
            table_rows.append(f'<td class="filename-col">{os.path.basename(font_path)}</td>')
            table_rows.append(f'<td>{info["style"]}</td>')
            table_rows.append(f'<td {title_attr}>{quality_icon}</td>')
            table_rows.append(f'<td class="render-col"><img src="{image_path}" alt="Render of {info["full_name"]}"></td>')
            table_rows.append(f'<td><a href="{relative_font_path}"><i class=\'bx bx-download\'></i></a></td>')
            table_rows.append('</tr>')

    with open(args.html_file, 'w') as f:
        f.write('<html><head><title>Font Index</title>')
        f.write('<link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">')
        f.write('<style>')
        f.write('body { font-family: sans-serif; margin: 2em; }')
        f.write('table { border-collapse: collapse; width: 100%; }')
        f.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        f.write('th { background-color: #f2f2f2; cursor: pointer; }')
        f.write('img { max-width: 100%; height: auto; }')
        f.write('#readme { background-color: #f9f9f9; border: 1px solid #eee; padding: 1em; margin-bottom: 2em; }')
        f.write('.font-name-col, .filename-col { max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }')
        f.write('.render-col { width: auto; }')
        f.write('</style>')
        f.write('</head><body>')
        f.write('<h1>Font Index</h1>')

        f.write(f'<p>Total fonts processed: {total_processed_fonts}</p>')
        f.write(f'<p>Fonts with quality issues (&#10060;): {fonts_with_issues}</p>')

        if os.path.exists('README.md'):
            with open('README.md', 'r') as readme_file:
                markdown_content = readme_file.read()
                html_content = markdown.markdown(markdown_content)
                f.write(f'<div id="readme">{html_content}</div>')

        f.write('<p>The <b>Quality</b> column indicates whether a font has passed a series of quality checks. A green checkmark (&#9989;) indicates that the font has passed all checks. A red \'x\' (&#10060;) indicates that the font may have issues, such as missing characters or inconsistent kerning, which can cause problems when rendering text.</p>')

        f.write(f'<p>Rendering the text: "{args.text}"</p>')
        f.write('<table id="fontTable">')
        f.write('<thead><tr><th class="font-name-col" onclick="sortTable(0)">Font Name</th><th class="filename-col" onclick="sortTable(1)">Filename</th><th onclick="sortTable(2)">Style</th><th onclick="sortTable(3)">Quality</th><th class="render-col">Render</th><th></th></tr></thead>')
        f.write('<tbody>')
        f.write('\n'.join(table_rows))
        f.write('</tbody>')
        f.write('</table>')
        f.write('''
<script>
const sortDirections = {};

function sortTable(n) {
    const table = document.getElementById("fontTable");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    
    const dir = sortDirections[n] === 'asc' ? 'desc' : 'asc';
    sortDirections[n] = dir;

    rows.sort((a, b) => {
        const x = a.cells[n].innerText.toLowerCase();
        const y = b.cells[n].innerText.toLowerCase();
        
        if (x < y) {
            return dir === 'asc' ? -1 : 1;
        }
        if (x > y) {
            return dir === 'asc' ? 1 : -1;
        }
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
}
</script>
        ''')
        f.write('</body></html>')

if __name__ == '__main__':
    main()