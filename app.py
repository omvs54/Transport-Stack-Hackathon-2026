#!/usr/bin/env python3
"""Demo server.  python app.py [--routes ...] [--crowd ...] [--port 5000]"""
import argparse
import os
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from planner import Planner

BASE_DIR = Path(__file__).resolve().parent

delhi_routes = BASE_DIR / "data" / "routes_stops_delhi.csv"
synth_routes = BASE_DIR / "data" / "routes_stops_SYNTHETIC.csv"
default_routes = str(delhi_routes if delhi_routes.exists() else synth_routes)
default_crowd = str(BASE_DIR / "out" / "crowding_by_stretch.csv")

ap = argparse.ArgumentParser()
ap.add_argument("--routes", default=default_routes)
ap.add_argument("--crowd", default=default_crowd)
ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
args, _ = ap.parse_known_args()

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
P = Planner(args.routes, args.crowd)


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/stops")
def stops():
    return jsonify(P.stops())


@app.get("/api/options")
def options():
    q = request.args
    return jsonify(P.options(q.get("from", ""), q.get("to", ""), q.get("depart", "18:00"),
                             q.get("day", "weekday")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=args.port)
