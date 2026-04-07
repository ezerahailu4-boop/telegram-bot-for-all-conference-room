from flask import Flask, render_template, request, jsonify, send_from_directory
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIST = os.path.join(BASE_DIR, 'webapp', 'dist')

app = Flask(
    __name__,
    static_folder=WEBAPP_DIST,
    template_folder=WEBAPP_DIST,
    static_url_path=''
)

@app.route('/')
def index():
    return send_from_directory(WEBAPP_DIST, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(WEBAPP_DIST, path)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"Received from web app: {data}")
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)