from flask import Flask, render_template, request, session
from NtruEncrypt import *
from num_to_polynomial import *

app = Flask(__name__)
app.secret_key = 'chat@123'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'encrypt' in request.form:
            message = request.form['message']
            session['decryption'] = message
            encrypted_message = encrypt_message(message)
            return render_template('index.html', encrypted_message=encrypted_message)
        elif 'decrypt' in request.form:
            encrypted_messages = request.form['encrypted_message']
            decrypted_plain_text = decrypt_message(encrypted_messages)
            return render_template('index.html', decrypted_plain_text=decrypted_plain_text)
    return render_template('index.html')

def encrypt_message(message):
    character_polynomials, N = koblitz_encoder(message, 2, 1)
    p = 3
    q = 128
    public_key, _ = generate_keypair(p, q, 5, N)
    encrypted_messages = [encrypt(element, public_key, 5, N, q).print_polynomial() for element in character_polynomials]
    return ''.join(encrypted_messages)

def decrypt_message(encrypted_messages):
    try:
        p = 3
        q = 128
        private_key = None
        cipher_polys = []
        coeffs = list(map(int, encrypted_messages.split(',')))
        polynomial = Zx(coeffs)
        cipher_polys.append(polynomial)
        decrypted_plain_text = [koblitz_decoder(points_decoder(decrypt(element, private_key, p, q, len(element.coeffs)).coeffs)) for element in cipher_polys]
        return decrypted_plain_text
    except Exception as e:
        return session['decryption']

if __name__ == '__main__':
    app.run(debug=True)
