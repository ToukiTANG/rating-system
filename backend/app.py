from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 允许前端跨域访问
CORS(app)


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({
        "code": 200,
        "message": "Flask 后端运行成功",
        "data": "Hello Vue"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )