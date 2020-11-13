# app.py - a minimal flask api using flask_restful
from flask import Flask, jsonify, request

# local import
from stockprices import StockPrices
from curl import cURL
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["ENV"] = "development"


@app.route("/")
def index():
    processor = StockPrices(app).get()
    return jsonify()


@app.route("/curl", methods=["GET"])
def curl():
    processor = cURL(request, app.logger)
    return jsonify(processor.get())


if __name__ == "__main__":
    handler = RotatingFileHandler("flask.log", maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    # app.logger.addHandler(handler)
    app.run(debug=True, host="0.0.0.0")
