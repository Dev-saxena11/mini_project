from flask import Flask, render_template,request,session,redirect,flash, jsonify
import os
import json
from datetime import datetime, timedelta
import requests
app = Flask(__name__)
app.secret_key = "my_secret_123"
# 🗂 Fake database (dictionary)
users_db = {}

@app.route('/')
@app.route('/home')
def home():
    username = session.get("username")
    return render_template('home.html',username=username)
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/groups')
def groups():
    return render_template('groups.html')
@app.route('/travel')
def travel():
    return render_template('travel.html')
@app.route('/user')
def user():
    return render_template('user.html')
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        if action == "register":
            if username in users_db:
                flash("⚠️ Username already exists! Please login.")
                return redirect('/auth')

            # Save new user
            users_db[username] = {"password": password, "email": email}
            session["username"] = username
            flash("✅ Registration successful! Welcome.")
            return redirect('/home')

        elif action == "login":
            if username not in users_db:
                flash("⚠️ User not found. Please register first.")
                return redirect('/auth')

            if users_db[username]["password"] != password:
                flash("❌ Incorrect password. Try again.")
                return redirect('/auth')

            session["username"] = username
            flash("✅ Login successful!")
            return redirect('/home')

    return render_template("auth.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("👋 You have been logged out.")
    return redirect('/home')
@app.route('/api/itinerary', methods=['POST'])
def api_itinerary():
    try:
        data = request.get_json(force=True)
        source_city = (data.get('from') or '').strip()
        destination_city = (data.get('to') or '').strip()
        start_date_str = (data.get('startDate') or '').strip()
        end_date_str = (data.get('endDate') or '').strip()
        interests = data.get('interests') or []
        limit = int(data.get('limit') or 40)

        if not destination_city or not start_date_str or not end_date_str:
            return jsonify({"error": "to, startDate, endDate are required"}), 400

        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({"error": "Dates must be ISO format YYYY-MM-DD"}), 400

        if end_date < start_date:
            return jsonify({"error": "endDate must be after startDate"}), 400

        # Load local POIs dataset
        data_path = os.path.join(app.root_path, 'static', 'data', 'pois.json')
        pois = []
        if os.path.exists(data_path):
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    all_pois = json.load(f)
                    for poi in all_pois:
                        if poi.get('city', '').lower() == destination_city.lower():
                            pois.append(poi)
            except Exception:
                pois = []

        # Free sources: OpenStreetMap Overpass API + Nominatim (no key)
        if destination_city:
            # Free fallback: OpenStreetMap Overpass API + Nominatim (no key)
            try:
                # Geocode city via Nominatim
                g = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": destination_city, "format": "json", "limit": 1},
                    headers={"User-Agent": "TravelTogether/1.0"}, timeout=10
                )
                if g.ok and isinstance(g.json(), list) and g.json():
                    gj = g.json()[0]
                    lat = float(gj.get('lat'))
                    lon = float(gj.get('lon'))
                    # Overpass query for attractions within ~10km
                    overpass_query = f"""
                    [out:json][timeout:25];
                    (
                      node["tourism"="attraction"](around:10000,{lat},{lon});
                      node["historic"](around:10000,{lat},{lon});
                      node["amenity"="place_of_worship"](around:10000,{lat},{lon});
                      node["leisure"="park"](around:10000,{lat},{lon});
                      node["tourism"="museum"](around:10000,{lat},{lon});
                      way["tourism"="attraction"](around:10000,{lat},{lon});
                      way["historic"](around:10000,{lat},{lon});
                    );
                    out center {limit};
                    """
                    ov = requests.post(
                        "https://overpass-api.de/api/interpreter",
                        data={"data": overpass_query},
                        headers={"User-Agent": "TravelTogether/1.0"}, timeout=30
                    )
                    if ov.ok:
                        data_ov = ov.json()
                        elements = data_ov.get('elements', [])
                        overpass_pois = []
                        for el in elements:
                            tags = el.get('tags', {})
                            name = tags.get('name')
                            if not name:
                                continue
                            center = el.get('center') or {}
                            lat_p = center.get('lat') or el.get('lat')
                            lon_p = center.get('lon') or el.get('lon')
                            if lat_p is None or lon_p is None:
                                continue
                            cat = tags.get('tourism') or tags.get('historic') or tags.get('amenity') or tags.get('leisure')
                            overpass_pois.append({
                                "id": f"ov-{el.get('id')}",
                                "name": name,
                                "city": destination_city,
                                "description": cat or "",
                                "image": "/static/images/temple.jpg",
                                "suggestedDurationMin": 60,
                                "tags": ["overpass"],
                                "lat": lat_p,
                                "lon": lon_p
                            })
                        # Merge unique
                        existing_ids = {p.get('id') for p in pois}
                        for p in overpass_pois:
                            if p['id'] not in existing_ids:
                                pois.append(p)
            except Exception:
                pass

        # Basic fallback if no POIs found
        if not pois:
            pois = [{
                "id": "generic-1",
                "name": f"Explore {destination_city}",
                "city": destination_city,
                "description": f"Discover landmarks, markets, and cuisine around {destination_city}.",
                "image": "/static/images/india-gate.jpg",
                "suggestedDurationMin": 120
            }]

        # Optional: filter by interests if tags present
        if interests and isinstance(interests, list):
            filtered = [p for p in pois if not p.get('tags') or any(t in p.get('tags', []) for t in interests)]
            if filtered:
                pois = filtered

        # Build day-wise itinerary
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            total_days = 1

        # Sort POIs by a simple priority (has image, has duration)
        pois.sort(key=lambda p: (
            0 if p.get('image') else 1,
            0 if p.get('suggestedDurationMin') else 1,
            p.get('name', '')
        ))

        # Distribute POIs across days (3-5 per day)
        daily_plan = []
        poi_index = 0
        per_day = 4 if len(pois) >= total_days * 4 else max(3, len(pois) // max(1, total_days) or 3)
        for d in range(total_days):
            day_date = (start_date + timedelta(days=d)).date().isoformat()
            day_items = []
            for _ in range(per_day):
                if poi_index < len(pois):
                    day_items.append(pois[poi_index])
                    poi_index += 1
            if not day_items and pois:
                # still ensure at least 1 per day
                day_items.append(pois[min(d, len(pois)-1)])
            daily_plan.append({
                "date": day_date,
                "items": day_items
            })

        response = {
            "from": source_city,
            "to": destination_city,
            "startDate": start_date.date().isoformat(),
            "endDate": end_date.date().isoformat(),
            "days": daily_plan
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__=='__main__':
    app.run(debug=True)
#Hello Aryan Here
