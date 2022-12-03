import os
from flask import Flask, request, Response
from multiprocessing import Process

from funcs import notify_close_cars

# For local testing Only:
# from dotenv import load_dotenv
# load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main_function():

    # import keys from environment variables
    keys = os.getenv('KEYS')
    keys = dict(item.split(':') for item in keys.split(','))

    if request.method == 'GET':
        if request.args.get('key') not in keys.values():
            return 'API key is needed'
            
        return Response(open('index.html').read())

    if request.method == 'POST':
        if request.args.get('key') not in keys.values():
            return 'API key is needed'
        
        loc = [float(request.form.get('latitude')), float(request.form.get('longitude'))]
        max_dis = float(request.form.get('radius'))
        api_key = request.form.get('key')        

        p = Process(target=notify_close_cars, args=(loc, max_dis, api_key,))
        p.start() 
            
        return Response(open('requested.html').read())


if __name__ == '__main__':
    app.run(debug=True)
