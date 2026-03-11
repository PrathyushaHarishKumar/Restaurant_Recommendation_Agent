"""
Flask API Server for Restaurant Agent
SENG 691 HW3 – Web Interface Backend
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from restaurant_agent import RestaurantAgent

app = Flask(__name__, static_folder='../static')
CORS(app)

# Load agent once at startup
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurants.csv')
agent = RestaurantAgent(CSV_PATH)

@app.route('/')
def index():
    return send_from_directory('../static', 'index.html')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' field"}), 400
    
    user_query = data['query'].strip()
    top_n = int(data.get('top_n', 5))
    
    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400
    
    result = agent.run(user_query, top_n=top_n)
    return jsonify(result)

@app.route('/api/restaurants', methods=['GET'])
def all_restaurants():
    """Return all restaurants for browsing"""
    all_r = agent.db.all()
    # Clean for JSON
    clean = []
    for r in all_r:
        clean.append({k: v for k, v in r.items()})
    return jsonify({"restaurants": clean, "count": len(clean)})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "restaurants_loaded": len(agent.db.all())})

if __name__ == '__main__':
    print("\n🚀 Restaurant Agent Web Server starting...")
    print("   Open: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
