from flask import Flask, render_template, request, redirect, url_for
from database import get_connection, create_tables
from datetime import datetime

app = Flask(__name__)

create_tables()

# ==========================
# HOME
# ==========================
@app.route('/')
def home():
    return render_template("entry.html")


# ==========================
# DASHBOARD
# ==========================
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


# ==========================
# SIGNUP
# ==========================
@app.route('/signup', methods=["POST"])
def signup():

    name = request.form["name"]
    age = request.form["age"]
    blood = request.form["blood"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO users (name, age, blood, email, password)
        VALUES (?, ?, ?, ?, ?)
        """, (name, age, blood, email, password))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    except:
        conn.close()
        return render_template("entry.html", error="Email already registered!")


# ==========================
# LOGIN
# ==========================
@app.route('/login', methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users WHERE email=? AND password=?
    """, (email, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        return redirect(url_for("dashboard"))
    else:
        return render_template("entry.html", error="Invalid email or password!")


# ==========================
# DONOR PAGE
# ==========================
@app.route('/donor')
def donor():
    return render_template("donor_dashboard.html")


# ==========================
# REGISTER DONOR (90 DAYS RULE)
# ==========================
@app.route('/register_donor', methods=["POST"])
def register_donor():

    name = request.form.get("name")
    age = request.form.get("age")
    blood = request.form.get("blood")
    phone = request.form.get("phone")
    location = request.form.get("location")
    last_date = request.form.get("last_date")

    last_donation_date = datetime.strptime(last_date, "%Y-%m-%d")
    today = datetime.today()

    difference = (today - last_donation_date).days

    if difference >= 90:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO donors (name, age, blood, phone, location, last_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, blood, phone, location, last_date, "approved"))

        conn.commit()
        conn.close()

        return render_template(
            "donor_result.html",
            success=True,
            name=name,
            blood=blood
        )

    else:
        wait_days = 90 - difference

        return render_template(
            "donor_result.html",
            success=False,
            wait_days=wait_days
        )


# ==========================
# VIEW DONORS
# ==========================
@app.route('/donors_list')
def donors_list():

    blood = request.args.get('blood')

    conn = get_connection()
    cursor = conn.cursor()

    if blood:
        cursor.execute("SELECT * FROM donors WHERE blood=? ORDER BY id DESC", (blood,))
    else:
        cursor.execute("SELECT * FROM donors ORDER BY id DESC")

    donors = cursor.fetchall()
    conn.close()

    return render_template("donors_list.html", donors=donors)


# ==========================
# PATIENT PAGE
# ==========================
@app.route('/patient')
def patient():
    return render_template("patient_dashboard.html")


# ==========================
# BLOOD COMPATIBILITY FUNCTION
# ==========================
def get_compatible_donors(patient_blood):

    compatibility = {
        "A+": ["A+", "A-", "O+", "O-"],
        "A-": ["A-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
        "AB-": ["A-", "B-", "AB-", "O-"],
        "O+": ["O+", "O-"],
        "O-": ["O-"]
    }

    return compatibility.get(patient_blood, [])


# ==========================
# REGISTER PATIENT
# ==========================
@app.route('/register_patient', methods=["POST"])
def register_patient():

    name = request.form["name"]
    age = request.form["age"]
    blood = request.form["blood"]
    phone = request.form["phone"]
    location = request.form["location"]
    units = request.form["units"]
    urgency = request.form["urgency"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO patients (name, age, blood, phone, location, units_required, urgency)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, age, blood, phone, location, units, urgency))

    compatible_groups = get_compatible_donors(blood)

    placeholders = ",".join(["?"] * len(compatible_groups))

    query = f"""
    SELECT name, blood, phone, location
    FROM donors
    WHERE blood IN ({placeholders}) AND status='approved'
    """

    cursor.execute(query, compatible_groups)
    donors = cursor.fetchall()

    conn.commit()
    conn.close()

    ranked_donors = []

    for donor in donors:
        donor_name, donor_blood, donor_phone, donor_location = donor

        score = 0
        badge = ""

        if donor_blood == blood:
            score += 50

        if donor_location.lower() == location.lower():
            score += 30

        if donor_blood == "O-":
            badge = "Universal Donor"
            score += 20

        ranked_donors.append({
            "name": donor_name,
            "blood": donor_blood,
            "phone": donor_phone,
            "location": donor_location,
            "score": score,
            "badge": badge
        })

    ranked_donors = sorted(ranked_donors, key=lambda x: x["score"], reverse=True)

    return render_template(
        "patient_result.html",
        pname=name,
        blood=blood,
        donors=ranked_donors
    )
# ==========================
# VIEW REGISTERED PATIENTS
# ==========================
@app.route('/patients_list')
def patients_list():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients ORDER BY id DESC")
    patients = cursor.fetchall()

    conn.close()

    return render_template("patients_list.html", patients=patients)

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)