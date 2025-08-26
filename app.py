from flask import Flask, render_template,request,session,redirect,flash
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
if __name__=='__main__':
    app.run(debug=True)
