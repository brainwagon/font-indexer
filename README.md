## The "Too Many Typefonts" collection...


While cleaning my office, I found an old "shareware" CDROM from Chestnut CDROMs, probably 
dating back to the 1990s. Chestnut CDROMs was a publisher of shareware and freeware CDROMs,
and this disk held a bunch of TrueType fonts. From the CDROM liner, it's unclear as to
what the copyright status of these fonts might be. It appears that Chestnut New Media
went out of business in the 1990s, and so any legal claims on this collection is probably
tenuous at best. That being said, I have no knowledge of the legality of using any of these
fonts, and no permission to redistribute the font collection is granted.

I've used gemini-cli to write a simple program to create an index of these font files. Feel 
free to use (and redistribute) the font-indexer.py file under the condition of the LICENSE.

A recent change has been made to correct a font rendering issue in both scripts, where characters were being cut off. The rendering logic has been updated to ensure full characters, including ascenders and descenders, are displayed correctly.

### `font-indexer.py`

This script indexes TrueType and OpenType fonts in a specified directory, generates an HTML file with rendered previews of each font.

**Usage:**

```bash
python font-indexer.py [--font-dir FONT_DIRECTORY] [--output-dir OUTPUT_DIRECTORY] [--html-file HTML_FILENAME] [--font-size FONT_SIZE] [--text TEXT_TO_RENDER] [--slow-check] [-n NUMBER_OF_FONTS]
```

**Arguments:**

*   `--font-dir FONT_DIRECTORY`: Directory to search for TrueType and OpenType fonts. Defaults to the current directory (`.`).
*   `--output-dir OUTPUT_DIRECTORY`: The directory to save rendered font images. Defaults to `renders`.
*   `--html-file HTML_FILENAME`: The name of the output HTML file. Defaults to `index.html`.
*   `--font-size FONT_SIZE`: The font size to use for rendering. Defaults to `24`.
*   `--text TEXT_TO_RENDER`: The text to render for each font. Defaults to 'The quick brown fox jumps over the lazy dog.'.
*   `--slow-check`: Perform a slower, more thorough check for font quality issues.
*   `-n NUMBER_OF_FONTS`, `--number NUMBER_OF_FONTS`: Limit the total number of fonts to process.

**Example:**

```bash
python font-indexer.py --font-dir /path/to/my/fonts -n 50
```

### `font-renderer.py`

This script renders text using a specified font and saves it as a PNG image. It also provides functionality to inspect character and glyph metrics.

**Usage:**

```bash
python font-renderer.py --font FONT_PATH [--font-size SIZE] [--text TEXT] [-o OUTPUT_PATH] [--preview] [--inspect CHAR] [--inspect-glyph-bbox CHAR]
```

**Arguments:**

*   `--font FONT_PATH`: **(Required)** The path to the font file to use.
*   `--font-size SIZE`: The font size to use for rendering. Defaults to `24`.
*   `--text TEXT`: The text to render. Defaults to `'The quick brown fox jumps over the lazy dog.'`.
*   `-o OUTPUT_PATH`, `--output OUTPUT_PATH`: The output filename for the rendered image. Defaults to `output.png`.
*   `--preview`: If set, previews the output image using `eog` (Eye of GNOME).
*   `--inspect CHAR`: Inspects the advance width and units per em of a specific character in the font.
*   `--inspect-glyph-bbox CHAR`: Inspects the bounding box (xMin, yMin, xMax, yMax) of a specific glyph in the font.

**Examples:**

Render text to an image:

```bash
python font-renderer.py --font "path/to/YourFont.ttf" --text "Hello World" -o hello.png
```

Render text with a specific size and preview:

```bash
python font-renderer.py --font "path/to/YourFont.ttf" --font-size 48 --text "Large Text" --preview
```

Inspect character metrics:

```bash
python font-renderer.py --font "path/to/YourFont.ttf" --inspect A
```

Inspect glyph bounding box:

```bash
python font-renderer.py --font "path/to/YourFont.ttf" --inspect-glyph-bbox G
```