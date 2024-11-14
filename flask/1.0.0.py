# flask_server.py

from flask import Flask, jsonify, send_file
import threading

app = Flask(__name__)

# transcribed_text = "Default text"
graph_path1 = "C:/servertest/blended_plot1.png"
graph_path2 = "C:/servertest/blended_plot2.png"



@app.route('/get_graph1', methods=['GET'])
def get_graph1():
    return send_file(graph_path1, mimetype='image/png')

@app.route('/get_graph2', methods=['GET'])
def get_graph2():
    return send_file(graph_path2, mimetype='image/png')

# @app.route('/status', methods=['GET'])
# def check_status():
#     # 서버가 연결되었음을 확인하는 간단한 메시지 전송s
#     return jsonify({"message": "Connected"})

# 여기에서 host와 port를 설정하여 외부 접속을 허용합니다.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
