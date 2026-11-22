# RSA & LSB Cipher / Decipher

A simple desktop app for encrypting text with RSA and hiding messages inside images using the LSB (Least Significant Bit) method. Made this as a school project to understand how asymmetric encryption and steganography work under the hood without relying on ready-made crypto libraries.

## What it does

- **RSA Encryption / Decryption**
  - Generates 1024-bit prime numbers from scratch (using trial division and the Miller-Rabin primality test).
  - Calculates the private key via the Extended Euclidean Algorithm.
  - Supports encrypting with your own public key (`e`) and modulus (`n`) if you already have them.

- **LSB Steganography**
  - Hides UTF-8 text (works with Cyrillic, Latin, numbers, etc.) in the least significant bits of RGB pixels.
  - Adds a 32-bit length header at the start so the decoder knows exactly where to stop reading.
  - Processes images in RAM (`io.BytesIO`) without saving temp files to disk and outputs lossless `PNG`.

## Stack

- Python 3
- Flask (backend & routing)
- Pillow (pixel manipulation)
- PyWebView (wraps the web interface into a desktop window)
- PyInstaller (building the `.exe`)

## How to run

Clone the repo and install the required libraries:

```bash
git clone https://github.com
cd rsa-lsb-cipher
pip install flask pillow pywebview
```

Start the app:

```bash
python app.py
```

## Building `.exe` (Windows)

If you want to pack it into a single executable file:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --icon="static/icon.ico" --add-data "templates;templates" --add-data "static;static" --name "RSA-LSB-Cipher" app.py
```

The output file will be in the `dist` folder.

## Keep in mind

For LSB steganography, only use lossless image formats like `PNG` or `BMP`. If you send an encoded image through a messenger that compresses photos into `JPEG`, the pixel values will change and the hidden text will be lost.
