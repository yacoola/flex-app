import os
import random
from flask import Flask, request, Response, send_from_directory, render_template
from multiprocessing import Process
import subprocess

from bookingfuncs import notify_close_cars

# For local testing Only:
from dotenv import load_dotenv
load_dotenv()

subprocess.run(["playwright", "install", "chromium"])

# Check keys when program start
KEYS = os.getenv('KEYS')
if not KEYS:
    print('Missing KEYS environment variable.')
    os._exit(1)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main_function():
    # import keys from environment variables
    keys = dict(item.split(':') for item in KEYS.split(','))

    if request.method == 'GET':
        if request.args.get('key') not in keys.values():
            return 'API key is needed'

        return render_template('index.html') 

    if request.method == 'POST':
        if request.args.get('key') not in keys.values():
            return 'API key is needed'

        loc = [float(request.form.get('latitude')), float(request.form.get('longitude'))]
        max_dis = float(request.form.get('radius'))
        api_key = request.form.get('key')
        login_cred = request.form.get('login_cred')
        autobook = request.form.get('autobook')
        ethical = request.form.get('ethical')

        p = Process(target=notify_close_cars, args=(loc, max_dis, api_key,autobook,login_cred, ethical,), name=f'{api_key}{random.randint(10000, 99999)}')
        p.start()

        if login_cred=='' and autobook is not None:
            return render_template('requested.html', warn=True) 
        else:
            return render_template('requested.html', warn=False) 

@app.route('/docs')
def docs():
    return render_template('docs.html') 

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/images/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/mylocation.png')
def mylocation():
    return send_from_directory(app.root_path, 'static/images/mylocation.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=False)
