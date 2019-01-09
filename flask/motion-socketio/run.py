from flask import Flask, render_template, Response, redirect, url_for, request
from flask_socketio import SocketIO, emit
from collections import deque
import glob, os.path, re, time
import mimetypes


app = Flask(__name__)   
socketio = SocketIO(app)
filenames = deque(maxlen = 4)
#img_root = r'/home/pi/media/3001/21-motion2/'
img_root = r'/home/pi/media/4001/21-motion2/'

def init():
    print('initing')
    global filenames, img_root
    l = sorted(glob.iglob(img_root +'2*jpg'), key=os.path.getctime)
    # samba 서버가 오토마운트 되지 않은 상태에서 자꾸 접속하려 하니 time_wait가 발생하는 것 같습니다
    # 오류 발생시키기 위해 assert 를 적당한 조건으로 넣어줬습니다만 
    # 생각해보니 이것은 원래 exception이 나지 않았을까 싶고 supervisor에서의 무한 자동 재시작이 문제인 것 같기도 합니다
    assert len(l) > 3
    for i in l[-4:]:
        filenames.append(i[-18:]) 

@app.route('/message/<filename>')
def message(filename):
    global filenames, img_root
    print('came into /message')
    recent = max(glob.iglob(img_root +'2*jpg'), key=os.path.getctime)
    filenames.append(recent[-18:])
    print('emiting 1')
    socketio.emit('update', {'data': 0}, namespace='/motion')
    return filename 

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/video/<filename>')
def video(filename):
    print('came into video')
    return render_template('video.html', filename=filename)

@app.route('/play/<filename>')
def play(filename):
    print('came into play')
    range_header = request.headers.get('Range', None)
    print(" ## Range header : {}".format(range_header))

    BUF = 4096
    f = img_root + filename[:-4] + ".avi.mp4"
    #print('video : {}'.format(f))

    size = os.path.getsize(f)
    byte1, byte2 = 0, None
    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1
        #length = byte2 - byte1

    #
    def vid_generate():
        remain = length
        with open(f, "rb") as v:
            v.seek(byte1)
            data = v.read(BUF)
            yield data
            remain = remain - len(data)
            print("remained : {}".format(remain))
            while ((remain > 0) and data): 
                if(remain < BUF):
                    r = remain
                else:
                    r = BUF
                data = v.read(r)
                yield data
                remain = remain - len(data)
                print('len(data) : {}, remain : {}'.format(len(data), remain))

    # buffer 크기 (4096)을 초과할 경우, 제너레이터 yield를 통해 응답하여 스트리밍 합니다
    if (length > BUF):
        print("length > {} : generate() started".format(BUF))
        rv = Response(vid_generate(), 206, mimetype=mimetypes.guess_type(f)[0], direct_passthrough=True)
    # buffer 크기 이내의 응답을 할 경우, (보통 safari의 첫 두 바이트 요청 등), 한방에 응답합니다
    else :
        print("length < {} : data responsing".format(BUF))
        with open(f, "rb") as v:
            v.seek(byte1)
            data = v.read(length)
        rv = Response(data, 206, mimetype=mimetypes.guess_type(f)[0], direct_passthrough=True)

    print('Content-Range bytes {}-{}/{}'.format(byte1, byte1 + length - 1, size))
    rv.headers.add('Content-Range', 'bytes {}-{}/{}'.format(byte1, byte1 + length - 1, size))

    return rv

@app.route('/image1/<int:n>')
def image1(n):
    global filenames, img_root
    if(n==99):
        print('99 !!!!')
        f = img_root + filenames[3][:-4] + ".avi.mp4"
        print(f)
        return redirect(url_for('video', filename = filenames[3]))

    def generate():
        f = img_root + filenames[3]
        with open(f, "rb") as im:
            data = im.read(1024)
            while data:
                yield data
                data = im.read(1024)
    return Response(generate(), mimetype="image/jpeg")


@app.route('/image2/<int:n>')
def image2(n):
    print('came into image2')
    if(n==99):
        return redirect(url_for('video', filename = filenames[2]))
    def generate():
        global filenames
        f = img_root + filenames[2]
        print(f)
        with open(f, "rb") as im:
            data = im.read(1024)
            while data:
                yield data
                data = im.read(1024)
    return Response(generate(), mimetype="image/jpeg")

@app.route('/image3/<int:n>')
def image3(n):
    global filenames
    if(n==99):
        return redirect(url_for('video', filename = filenames[1]))
    def generate():
        f = img_root + filenames[1]
        print(f)
        with open(f, "rb") as im:
            data = im.read(1024)
            while data:
                yield data
                data = im.read(1024)
    return Response(generate(), mimetype="image/jpeg")

@app.route('/image4/<int:n>')
def image4(n):
    global filenames
    if(n==99):
        return redirect(url_for('video', filename = filenames[0]))
    def generate():
        f = img_root + filenames[0]
        print(f)
        with open(f, "rb") as im:
            data = im.read(1024)
            while data:
                yield data
                data = im.read(1024)
    return Response(generate(), mimetype="image/jpeg")

@socketio.on('connect', namespace='/motion')
def connect():
    emit('update', {'data': 'Connected'})
    print('client connected')

@socketio.on('disconnect', namespace='/motion')
def disconnect():
    print('client disconnected')


if __name__ == "__main__":
    init()
    #socketio.run(app, host='0.0.0.0', port='5000')
    socketio.run(app, host='0.0.0.0', port='5001')

