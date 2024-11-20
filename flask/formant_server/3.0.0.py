import os
from flask import Flask, send_file, jsonify, request  # request 추가

app = Flask(__name__)
image_path = "C:/servertest/blended_img.png"
last_modified = None  # 마지막 수정 시간 저장

@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Graph with Buttons</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center; /* 콘텐츠 가운데 정렬 */
            margin: 0;
            padding: 0;
        }

        #graph-container {
            margin-bottom: 20px; /* 그래프와 버튼 간격 */
        }

        .button-container {
            display: flex;
            justify-content: center; /* 버튼 가로로 가운데 정렬 */
            gap: 10px; /* 버튼 간 간격 */
        }

        button {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }

        #dynamic-image {
            width: 700px; /* 그래프 크기 조정 */
            height: auto; /* 비율 유지 */
            }
    </style>
        <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0;
            padding: 0;
        }

        .button-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }

        button {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border: 2px solid #007BFF;
            border-radius: 5px;
            background-color: #007BFF;
            color: white;
            transition: transform 0.1s ease, background-color 0.1s ease;
        }

        button:active {
            transform: scale(0.95);
            background-color: #0056b3;
        }

        button:hover {
            background-color: #0056b3;
        }
    </style>
   <script>
        let intervalId = null;
        let currentType = 'default';

        function refreshImage(type) {
            const img = document.getElementById('dynamic-image');
            const timestamp = new Date().getTime();
            currentType = type;
            img.src = `/get_image?type=${type}&timestamp=${timestamp}`;
        }

        function showPitch() {
            if (intervalId) {
                clearInterval(intervalId);
            }
            currentType = 'default';
            intervalId = setInterval(() => refreshImage('default'), 1000);
        }

        function showFormant() {
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
            refreshImage('formant');
        }

        function refreshFormantOnce() {
            if (currentType === 'formant') {
                refreshImage('formant');
            }
        }
    </script>
</head>
<body>
    <div id="graph-container">
        <!-- 그래프 영역 -->
    <img id="dynamic-image" src="/get_image" alt="Graph"> <!-- Flask 라우트로 이미지 요청 -->
    </div>

    <div class="button-container">
        <!-- 버튼 영역 -->
        <button onclick="showPitch()">Pitch, Intensity</button>
        <button onclick="showFormant()">Formant</button>
        <button onclick="refreshFormantOnce()">Refresh</button>


    </div>

 </body>
</html>
    '''

@app.route("/get_image")
def get_image():
    global last_modified
    image_type = request.args.get('type', 'default')  # type 파라미터로 이미지 구분
    if image_type == 'formant':
        image_path = "C:/servertest/formant_blended.png"  # Formant 이미지 경로
    else:
        image_path = "C:/servertest/blended_img.png"  # 기본 이미지 경로

    if os.path.exists(image_path):
        # 파일 수정 시간을 확인
        modified_time = os.path.getmtime(image_path)
        if last_modified is None or modified_time > last_modified:
            last_modified = modified_time  # 마지막 수정 시간 업데이트

        # Flask Response로 캐시 방지 헤더 추가
        response = send_file(image_path, mimetype="image/png")
        response.headers['Cache-Control'] = 'no-store'  # 캐시 방지
        return response
    else:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
