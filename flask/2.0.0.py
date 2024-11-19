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
        <script>
            // 이미지 새로고침 함수
            function refreshImage() {
                const img = document.getElementById("dynamic-image");
                img.src = "/get_image?timestamp=" + new Date().getTime();  // 타임스탬프 추가로 캐시 방지
            }
            setInterval(refreshImage, 1000);  // 1초마다 업데이트
        </script>
    </head>
    <body>
        <h1>Check out this image:</h1>
        <img id="dynamic-image" src="/get_image?timestamp=0" alt="Dynamic Image">
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
