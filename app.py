from flask import Flask, request, Response
import json
import time
from multiprocessing import Process

from funcs import notify_close_cars

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main_function():
    keys = {'Connor': 'o.t7o0OzqvPvGBSh958BZuLtB1Zg6BVcim'}

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
