import os
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

        // 이미지 새로고침 함수
        function refreshImage() {
            const img = document.getElementById('dynamic-image');
            const timestamp = new Date().getTime();
            img.src = '/get_image?timestamp=' + timestamp; // 새로고침 시 타임스탬프 추가
        }

        // 자동 새로고침 시작
        function showPitch() {
            if (!intervalId) { // 이미 실행 중이 아닐 때만 실행
                intervalId = setInterval(refreshImage, 1000); // 1초마다 새로고침
                console.log('자동 새로고침 시작');
            }
        }

        // 자동 새로고침 중단
        function showFormant() {
            if (intervalId) { // 실행 중인 경우에만 중단
                clearInterval(intervalId);
                intervalId = null;
                console.log('자동 새로고침 중단');
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
        <button onclick="refreshImage()">Refresh</button>
    </div>

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
