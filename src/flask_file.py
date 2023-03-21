from flask import Flask


def run_flask():

    app = Flask(__name__)

    @app.route('/')
    def hello_sasha():
        return 'Hello, Sasha! This is our diploma. CRY!'

    app.run(host='82.148.28.79', port=5001)
