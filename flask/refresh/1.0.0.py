import os
import time
from flask import Flask, send_file, jsonify

app = Flask(__name__)
image_path = "C:/servertest/blended_img.png"
last_modified = None  # 마지막 수정 시간 저장

@app.route("/")
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>Dynamic Image</title>
    <style>
        #dynamic-image {
            width: 700px; /* 너비를 설정 */ 
            height: auto; /* 비율 유지 */
        }
        button {
            margin-top: 20px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }
    </style>
    <script>
        function refreshImage() {
            const img = document.getElementById('dynamic-image');
            const timestamp = new Date().getTime();
            img.src = '/get_image?timestamp=' + timestamp; // 새로고침 시 타임스탬프 추가
        }
    </script>
    </head>
    <body>
        <img id="dynamic-image" src="/get_image?timestamp=0" alt="Dynamic Image">
        <br>
        <button onclick="refreshImage()">새로고침</button> <!-- 새로고침 버튼 -->
    </body>
    </html>
    '''

@app.route("/get_image")
def get_image():
    global last_modified
    if os.path.exists(image_path):
        # 파일 수정 시간을 확인
        modified_time = os.path.getmtime(image_path)
        if last_modified is None or modified_time > last_modified:
            last_modified = modified_time  # 마지막 수정 시간 업데이트
        return send_file(image_path, mimetype="image/png")  # 항상 이미지 반환
    else:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
