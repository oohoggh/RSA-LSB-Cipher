import io
import os
import random
import sys
import threading

import webview
from flask import Flask, redirect, render_template, request, send_file, url_for
from PIL import Image

if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
else:
    base_dir = os.path.abspath(".")
    app = Flask(__name__)
icon_path = os.path.join(base_dir, "static", "icon.ico")


def NoD(a, b):
    r = None
    while r != 0:
        r = a % b
        a = b
        b = r
    return a


def findE(a):
    if a > 65537 and NoD(a, 65537) == 1:
        return 65537
    e = 3
    while NoD(a, e) != 1:
        e += 2
    return e


SMALL_PRIMES = [
    3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
    157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
    239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
    331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419,
    421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503,
    509, 521, 523, 541
]


def is_prime(n):
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # отсев
    for p in SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(16):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def find_d(e, phi):
    a, b = e, phi
    x0, x1 = 1, 0
    while b != 0:
        q = a // b
        a, b = b, a % b
        x0, x1 = x1, x0 - q * x1
    return x0 % phi


def TwoPrimeNumbers():
    p, q = 0, 0
    while not is_prime(p):
        p = random.getrandbits(1024) | (1 << (1024 - 1)) | 1
    while not is_prime(q) or q == p:
        q = random.getrandbits(1024) | (1 << (1024 - 1)) | 1
    return p, q


def RSADecrypt(enc, d, n):
    try:
        enc = int(enc)
        d = int(d)
        n = int(n)
        decrypted_value = pow(enc, d, n)
        byte_length = (decrypted_value.bit_length() + 7) // 8
        decrypted_bytes = decrypted_value.to_bytes(byte_length, "big")
        return decrypted_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return "Ошибка: неверные данные или ключ для расшифровки"


def RSAEncrypt(text):
    p, q = TwoPrimeNumbers()  # случайное простое число
    n = p * q  # модуль
    phi = (p - 1) * (q - 1)  # формула эйлера
    e = findE(phi)  # просто случаное открытое число. МЕНЬШЕ PHI
    d = find_d(e, phi)  # закрытый ключ

    text_bytes = text.encode("utf-8")  # тут мы превращаем буквы в набор байтов
    m = int.from_bytes(
        text_bytes, "big"
    )  # тут мы превращаем набор байтов в огромное число
    encryptText = pow(m, e, n)
    return encryptText, e, n, d


def text_in_bits(text):
    text_bytes = text.encode("utf-8")
    bits = ""
    for i in text_bytes:
        bits += format(i, "08b")
    return bits


def LSB_algoritm(image, text):
    img = Image.open(image).convert("RGB")
    pixels = img.load()
    original = f"{image.filename.rsplit('.', 1)[0]}.png"
    width, height = img.size
    textinbits = text_in_bits(text)
    fulltextinbits = format(len(textinbits), "032b") + textinbits
    if len(fulltextinbits) > width * height * 3:
        return "Картинка слишком маленькая.", None
    bit_index = 0
    for y in range(height):
        for x in range(width):
            if bit_index >= len(fulltextinbits):
                break
            r, g, b = pixels[x, y]
            channels = [r, g, b]
            for i in range(3):
                if bit_index < len(fulltextinbits):
                    bit = int(fulltextinbits[bit_index])

                    channels[i] = (channels[i] & 254) | bit

                    bit_index += 1
            pixels[x, y] = tuple(channels)
        if bit_index >= len(fulltextinbits):
            break
    return img, original


def LSB_decrypt(image):
    img = Image.open(image).convert("RGB")
    pixels = img.load()
    width, height = img.size
    bits = ""
    target_length = None
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for channel in (r, g, b):
                bits += str(channel & 1)
                if target_length is None and len(bits) == 32:
                    message_length = int(bits, 2)
                    target_length = 32 + message_length
                    if target_length > width * height * 3 or message_length == 0:
                        return "Скрытый текст не найден."
                if target_length is not None and len(bits) >= target_length:
                    break
            if target_length is not None and len(bits) >= target_length:
                break
        if target_length is not None and len(bits) >= target_length:
            break
    text_bits = bits[32:]
    byte_data = bytearray()
    for i in range(0, len(text_bits), 8):
        byte_chunk = text_bits[i : i + 8]
        byte_data.append(int(byte_chunk, 2))
    try:
        return byte_data.decode("utf-8")
    except UnicodeDecodeError:
        return (
            "Не удалось расшифровать сообщение (файл не содержит корректного текста)."
        )


data = {
    "enc_text": "",
    "open_key": "",
    "module": "",
    "secret_key": "",
    "dec_text": "",
    "enc_text_user": "",
    "secret_key_user": "",
    "module_user": "",
}


@app.route("/")
def redir():
    return redirect(url_for("encRSA"))


@app.route("/encRSA", methods=["GET", "POST"])
def encRSA():
    if request.method == "POST":
        text = request.form.get("normal_text", "")
        open_key = request.form.get("open_key", "").strip()
        module = request.form.get("module", "").strip()
        if open_key and module:
            try:
                open_key = int(open_key)
                module = int(module)
            except ValueError:
                return render_template("encRSA.html", data=data)

            text_bytes = text.encode("utf-8")
            m = int.from_bytes(text_bytes, "big")
            if m >= module:
                data["enc_text"] = "Ошибка: текст слишком длинный для этого модуля!"
                return render_template(
                    "encRSA.html",
                    data=data,
                )
            data["enc_text"] = pow(m, open_key, module)
            data["open_key"] = open_key
            data["module"] = module
            return render_template("encRSA.html", data=data)
        else:
            data["enc_text"], data["open_key"], data["module"], data["secret_key"] = (
                RSAEncrypt(text)
            )
    return render_template("encRSA.html", data=data)


@app.route("/decRSA", methods=["GET", "POST"])
def decRSA():
    if request.method == "POST":
        data["enc_text_user"] = request.form.get("enc_text_user", "")
        data["secret_key_user"] = request.form.get("secret_key_user", "")
        data["module_user"] = request.form.get("module_user", "")
        data["dec_text"] = RSADecrypt(
            data["enc_text_user"], data["secret_key_user"], data["module_user"]
        )
    return render_template("decRSA.html", data=data)


@app.route("/encLSB", methods=["GET", "POST"])
def encLSB():
    if request.method == "POST":
        text = request.form.get("lsb_text", "")
        img = request.files.get("image", "")
        if not img or img.filename == "":
            return "Вы не выбрали картинку!"
        image, file_name = LSB_algoritm(img, text)
        if isinstance(image, str):
            return image
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return send_file(
            buf, mimetype="image/png", as_attachment=True, download_name=file_name
        )
    return render_template("encLSB.html")


@app.route("/decLSB", methods=["GET", "POST"])
def decLSB():
    decoded_text = ""
    if request.method == "POST":
        img = request.files.get("image", "")
        if not img or img.filename == "":
            return render_template("decLSB.html", decoded_text="")
        decoded_text = LSB_decrypt(img)
    return render_template("decLSB.html", decoded_text=decoded_text)


def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    webview.create_window(
        "RSA & LSB Шифратор",
        "http://127.0.0.1:5000",
        width=1100,
        height=750,
        text_select=True,
        
    )
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.start(icon=icon_path)