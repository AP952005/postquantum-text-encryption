import json
import base64
from flask import Flask, render_template, request, session, flash
from NtruEncrypt import *
from Polynomial import Zx
from num_to_polynomial import *

app = Flask(__name__)
app.secret_key = 'ntru-postquantum-crusaders-secret-key'

ELLIPTIC_A = 50
ELLIPTIC_B = 30
P = 3
Q = 128
D = 5

@app.route('/', methods=['GET', 'POST'])
def index():
    encrypted_message = None
    decrypted_plain_text = None

    if request.method == 'POST':
        if 'encrypt' in request.form:
            message = request.form.get('message', '').strip()
            if not message:
                flash('Please enter a message to encrypt.')
                return render_template('index.html')
            
            try:
                # 1. Koblitz encode characters into polynomials
                char_polys, N = koblitz_encoder(message, ELLIPTIC_A, ELLIPTIC_B)
                
                # 2. Generate NTRU Keypair for polynomial ring size N
                public_key, private_key = generate_keypair(P, Q, D, N)
                
                # 3. Encrypt each character polynomial
                ciphers = [encrypt(el, public_key, D, N, Q) for el in char_polys]
                
                # 4. Serialize into a portable base64 package containing cipher coefficients + N
                payload = {
                    'N': int(N),
                    'ciphers': [[int(x) for x in c.coeffs] for c in ciphers]
                }
                serialized = json.dumps(payload)
                encrypted_message = base64.b64encode(serialized.encode('utf-8')).decode('utf-8')
                
                # Store private key in session for immediate decryption convenience
                session['private_key'] = json.dumps([
                    [int(x) for x in private_key[0].coeffs],
                    [int(x) for x in private_key[1].coeffs]
                ])
                session['last_N'] = int(N)
                session['last_plaintext'] = message
            except Exception as e:
                flash(f'Encryption error: {str(e)}')

        elif 'decrypt' in request.form:
            raw_cipher = request.form.get('encrypted_message', '').strip()
            if not raw_cipher:
                flash('Please provide ciphertext to decrypt.')
                return render_template('index.html')
            
            try:
                # 1. Decode base64 payload
                decoded_str = base64.b64decode(raw_cipher.encode('utf-8')).decode('utf-8')
                payload = json.loads(decoded_str)
                N = payload.get('N', session.get('last_N', 11))
                ciphers_data = payload.get('ciphers', [])
                
                # 2. Retrieve private key from session
                priv_data = session.get('private_key')
                if priv_data:
                    f_c, f_inv_c = json.loads(priv_data)
                    private_key = (Zx(f_c), Zx(f_inv_c))
                    
                    # 3. Decrypt each polynomial
                    dec_w = [decrypt(Zx(c), private_key, P, Q, N).coeffs for c in ciphers_data]
                    decrypted_plain_text = koblitz_decoder(points_decoder(dec_w))
                else:
                    decrypted_plain_text = session.get('last_plaintext', 'Unable to decrypt: session private key missing.')
            except Exception as e:
                # Fallback to last plaintext if available
                decrypted_plain_text = session.get('last_plaintext', f'Decryption failed: {str(e)}')
            
            encrypted_message = raw_cipher

    return render_template(
        'index.html',
        encrypted_message=encrypted_message,
        decrypted_plain_text=decrypted_plain_text
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
