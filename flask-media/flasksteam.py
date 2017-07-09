import os, glob
from flask import Flask, request, render_template, Response
from flask_socketio

#video_dir = '/home/pi/.virtualenvs/blog/src/flask/flaskmedia/static/video'
image_dir = '/home/pi/.virtualenvs/blog/src/flask-media/static/image'

app = Flask(__name__)

@app.route('/jpg_feed')
def jpg_feed():
    def generate():
        # 21-motion 의 최신파일을 가져옵니다
        #recent_jpg = max(glob.iglob('/home/pi/media/3001/21-motion2/2*jpg'), key = os.path.getctime)
        recent_jpg = 'static/image/current.jpg'
        print(recent_jpg)
        with open(recent_jpg, "rb") as im:
            data = im.read(1024)
            while data:
                yield data
                data = im.read(1024)
    return Response(generate(), mimetype="image/jpg")

'''
@app.route('/')
@app.route('/home')
def index():
    video_files = [f for f in os.listdir(video_dir) if f.endswith('mp4')] 
    video_files_num = len(video_files)
    return render_template("index.html", \
                        title = 'Home', \
                        video_files_num = video_files_num, \
                        video_files = video_files)

@app.route('/<filename>')
def song(filename):
    return render_template('play.html', \
                            title = filename, \
                            video_file = filename)
'''

'''
@app.route('/mp4_feed')
def mp4_feed():
    def generate():
        with open("static/video/out2.mp4", "rb") as vd:
            data = vd.read(10240)
            while data:
                yield data
                data = vd.read(10240)
    return Response(generate(), mimetype="video/mp4")
    '''



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug = True)
