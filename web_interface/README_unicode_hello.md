# Unicode Art Hello Application

A Python application that displays the word "Hello" using visually appealing Unicode/ASCII art, centered in the console.

## Features

- 🎨 Beautiful Unicode art text rendering
- 🖥️ Cross-platform compatibility (Windows, Linux, macOS)
- 📐 Automatic console centering
- 🔧 Robust encoding handling for different terminals
- ⚡ No user input required - runs automatically

## Requirements

- Python 3.6 or higher
- `pyfiglet` library for generating Unicode art

## Installation

1. **Clone or download the script**:
   ```bash
   # If part of a larger project
   cd /path/to/your/project
   
   # Or download just the unicode_hello.py file
   ```

2. **Install dependencies**:
   ```bash
   pip install pyfiglet
   ```

   Or if you have a requirements file:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Simply run the Python script:

```bash
python unicode_hello.py
```

Or make it executable and run directly (Unix/Linux/macOS):

```bash
chmod +x unicode_hello.py
./unicode_hello.py
```

## Example Output

```
                    __ __       __ __      
                   / // /___   / // /_____ 
                  / // // _ \ / // // / _ \
                 / // //  __// // // /  __/
                /_//_/ \___//_//_//_/\___/ 
```

## Cross-Platform Compatibility

The application handles encoding issues automatically:

- **Windows**: Sets UTF-8 code page for proper Unicode display
- **Unix/Linux/macOS**: Configures stdout encoding for Unicode support
- **All platforms**: Graceful fallback to default fonts if specified font is unavailable

## Customization

You can modify the script to:

- Change the font style by modifying the `font` parameter in `create_unicode_art()`
- Adjust the message by changing the text passed to `create_unicode_art()`
- Modify spacing and centering behavior in the `main()` function

### Available Fonts

Some popular `pyfiglet` fonts include:
- `slant` (default)
- `big`
- `block`
- `bubble`
- `digital`
- `lean`
- `small`

## Troubleshooting

### Import Error
If you see `ImportError: No module named 'pyfiglet'`:
```bash
pip install pyfiglet
```

### Encoding Issues
If Unicode characters don't display correctly:
1. Ensure your terminal supports UTF-8
2. On Windows, try running from Command Prompt or PowerShell
3. Update your terminal/console application

### Font Not Found
If you get a font error, the script will automatically fall back to the default font.

## License

This project is open source and available under standard terms.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.