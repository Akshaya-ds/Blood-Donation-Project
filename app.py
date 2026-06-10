from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import get_connection, create_tables
from datetime import datetime
from math import radians, cos, sin, sqrt, atan2
from urllib.parse import quote

app = Flask(__name__)

# ==========================
# SESSION SUPPORT
# ==========================
app.secret_key = "blood_app_secret_key"

create_tables()

# ==========================
# DISTANCE CALCULATOR
# ==========================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return round(distance, 1)

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
# DONOR LOGIN
# ==========================

@app.route('/donor_login')
def donor_login():
    return render_template("donor_login.html")

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
        INSERT INTO users
        (name, age, blood, email, password)

        VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            age,
            blood,
            email,
            password
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    except:

        conn.close()

        return render_template(
            "entry.html",
            error="Email already registered!"
        )

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
    SELECT * FROM users
    WHERE email=? AND password=?
    """, (
        email,
        password
    ))

    user = cursor.fetchone()

    conn.close()

    if user:

        session["user_id"] = user[0]
        session["email"] = email

        return redirect(url_for("dashboard"))

    else:

        return render_template(
            "entry.html",
            error="Invalid email or password!"
        )

# ==========================
# DONOR PAGE
# ==========================

@app.route('/donor')
def donor():
    return render_template("donor_dashboard.html")

# ==========================
# REGISTER DONOR
# ==========================

@app.route('/register_donor', methods=["POST"])
def register_donor():

    name = request.form.get("name")
    age = request.form.get("age")
    blood = request.form.get("blood")
    phone = request.form.get("phone")
    location = request.form.get("location")

    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    last_date = request.form.get("last_date")

    last_donation_date = datetime.strptime(
        last_date,
        "%Y-%m-%d"
    )

    today = datetime.today()

    difference = (
        today - last_donation_date
    ).days

    if difference >= 90:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO donors
        (
            name,
            age,
            blood,
            phone,
            location,
            latitude,
            longitude,
            last_date,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            age,
            blood,
            phone,
            location,
            latitude,
            longitude,
            last_date,
            "approved"
        ))

        conn.commit()
        conn.close()

        return render_template(
            "donor_result.html",
            success=True,
            name=name
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

        cursor.execute("""
        SELECT * FROM donors
        WHERE blood=?
        ORDER BY id DESC
        """, (blood,))

    else:

        cursor.execute("""
        SELECT * FROM donors
        ORDER BY id DESC
        """)

    donors = cursor.fetchall()

    conn.close()

    return render_template(
        "donors_list.html",
        donors=donors
    )

# ==========================
# PATIENT PAGE
# ==========================

@app.route('/patient')
def patient():
    return render_template("patient_dashboard.html")

# ==========================
# BLOOD COMPATIBILITY
# ==========================

def get_compatible_donors(patient_blood):

    compatibility = {

        "A+": ["A+", "A-", "O+", "O-"],
        "A-": ["A-", "O-"],

        "B+": ["B+", "B-", "O+", "O-"],
        "B-": ["B-", "O-"],

        "AB+": [
            "A+", "A-",
            "B+", "B-",
            "AB+", "AB-",
            "O+", "O-"
        ],

        "AB-": [
            "A-", "B-",
            "AB-", "O-"
        ],

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

    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    units = request.form["units"]
    urgency = request.form["urgency"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO patients
    (
        name,
        age,
        blood,
        phone,
        location,
        latitude,
        longitude,
        units_required,
        urgency
    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        age,
        blood,
        phone,
        location,
        latitude,
        longitude,
        units,
        urgency
    ))

    conn.commit()

    compatible_groups = get_compatible_donors(blood)

    placeholders = ",".join(
        ["?"] * len(compatible_groups)
    )

    query = f"""
    SELECT
        name,
        blood,
        phone,
        location,
        latitude,
        longitude

    FROM donors

    WHERE blood IN ({placeholders})
    AND status='approved'
    """

    cursor.execute(query, compatible_groups)

    donors = cursor.fetchall()

    conn.close()

    ranked_donors = []

    for donor in donors:

        donor_name = donor[0]
        donor_blood = donor[1]
        donor_phone = donor[2]
        donor_location = donor[3]

        donor_latitude = donor[4]
        donor_longitude = donor[5]

        score = 0
        badge = ""

        distance = calculate_distance(
            latitude,
            longitude,
            donor_latitude,
            donor_longitude
        )

        if donor_blood == blood:
            score += 50

        if distance <= 5:
            score += 40

        elif distance <= 15:
            score += 25

        elif distance <= 30:
            score += 10

        if donor_blood == "O-":
            badge = "Universal Donor"
            score += 20

        if urgency == "Critical":
            score += 20

        ranked_donors.append({

            "name": donor_name,
            "blood": donor_blood,
            "phone": donor_phone,
            "location": donor_location,

            "distance": distance,

            "score": score,
            "badge": badge,

            "patient_name": name,
            "patient_phone": phone
        })

    ranked_donors = sorted(
        ranked_donors,
        key=lambda x: (
            x["distance"],
            -x["score"]
        )
    )

    return render_template(
        "patient_result.html",
        pname=name,
        blood=blood,
        urgency=urgency,
        donors=ranked_donors
    )

# ==========================
# VIEW PATIENTS
# ==========================

@app.route('/patients_list')
def patients_list():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM patients
    ORDER BY id DESC
    """)

    patients = cursor.fetchall()

    conn.close()

    return render_template(
        "patients_list.html",
        patients=patients
    )

# ==========================
# SEND REQUEST
# ==========================

@app.route('/send_request', methods=['POST'])
def send_request():

    patient_name = request.form['patient_name']
    patient_contact = request.form['patient_contact']

    donor_name = request.form['donor_name']
    donor_contact = request.form['donor_contact']

    blood_group = request.form['blood_group']

    request_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO blood_requests
    (
        patient_name,
        patient_contact,
        donor_name,
        donor_contact,
        blood_group,
        status,
        request_date
    )

    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        patient_name,
        patient_contact,

        donor_name,
        donor_contact,

        blood_group,
        "Pending",
        request_date
    ))

    conn.commit()
    conn.close()

    return render_template(
        "request_success.html",
        patient_name=patient_name,
        donor_name=donor_name,
        blood_group=blood_group
    )

# ==========================
# VERIFY DONOR
# ==========================

@app.route('/verify_donor', methods=['POST'])
def verify_donor():

    donor_name = request.form['name']
    donor_phone = request.form['phone']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM donors
    WHERE name=?
    AND phone=?
    """, (
        donor_name,
        donor_phone
    ))

    donor = cursor.fetchone()

    if not donor:

        conn.close()

        return """
        <h2 style='color:red;text-align:center;margin-top:100px;'>
        Invalid Donor Details
        </h2>
        """

    cursor.execute("""
    SELECT * FROM blood_requests
    WHERE donor_name=?
    AND donor_contact=?
    AND status='Pending'
    ORDER BY id DESC
    """, (
        donor_name,
        donor_phone
    ))

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "donor_requests.html",
        requests=requests,
        donor_name=donor_name,
        donor_phone=donor_phone
    )

# ==========================
# ACCEPT REQUEST
# ==========================

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):

    donor_name = request.form['donor_name']
    donor_phone = request.form['donor_phone']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE blood_requests
    SET status='Accepted'
    WHERE id=?
    """, (request_id,))

    conn.commit()

    cursor.execute("""
    SELECT * FROM blood_requests
    WHERE id=?
    """, (request_id,))

    accepted_request = cursor.fetchone()

    patient_name = accepted_request[1]
    patient_contact = accepted_request[2]
    blood_group = accepted_request[5]

    clean_number = (
        patient_contact
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
    )

    whatsapp_number = clean_number

    if not whatsapp_number.startswith("91"):
        whatsapp_number = "91" + whatsapp_number

    whatsapp_message = f"""
Hello {patient_name},

I am ready to donate blood.

Blood Group: {blood_group}

Please share your hospital location and required details.

- {donor_name}
"""

    encoded_message = quote(whatsapp_message)

    whatsapp_link = (
        f"https://wa.me/{whatsapp_number}"
        f"?text={encoded_message}"
    )

    sms_message = (
        f"Hello {patient_name}, "
        f"I am ready to donate {blood_group} blood. "
        f"Please share hospital details. "
        f"- {donor_name}"
    )

    encoded_sms = quote(sms_message)

    sms_link = (
        f"sms:{clean_number}"
        f"?body={encoded_sms}"
    )

    cursor.execute("""
    SELECT * FROM blood_requests
    WHERE donor_name=?
    AND donor_contact=?
    AND status='Pending'
    ORDER BY id DESC
    """, (
        donor_name,
        donor_phone
    ))

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "donor_requests.html",

        requests=requests,

        donor_name=donor_name,
        donor_phone=donor_phone,

        accepted_request=accepted_request,

        whatsapp_link=whatsapp_link,
        sms_link=sms_link
    )

# ==========================
# REJECT REQUEST
# ==========================

@app.route('/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):

    donor_name = request.form['donor_name']
    donor_phone = request.form['donor_phone']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE blood_requests
    SET status='Rejected'
    WHERE id=?
    """, (request_id,))

    conn.commit()

    cursor.execute("""
    SELECT * FROM blood_requests
    WHERE donor_name=?
    AND donor_contact=?
    AND status='Pending'
    ORDER BY id DESC
    """, (
        donor_name,
        donor_phone
    ))

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "donor_requests.html",
        requests=requests,
        donor_name=donor_name,
        donor_phone=donor_phone
    )

# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route('/admin')
def admin_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM donors
    """)
    total_donors = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM patients
    """)
    total_patients = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM blood_requests
    WHERE status='Pending'
    """)
    pending_requests = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM blood_requests
    WHERE status='Accepted'
    """)
    accepted_requests = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM blood_requests
    WHERE status='Rejected'
    """)
    rejected_requests = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",

        total_donors=total_donors,
        total_patients=total_patients,

        pending_requests=pending_requests,
        accepted_requests=accepted_requests,
        rejected_requests=rejected_requests
    )

# ==========================
# AI CHATBOT
# ==========================

@app.route('/chatbot', methods=['POST'])
def chatbot():

    data = request.get_json()

    user_message = data['message'].lower()

    if any(word in user_message for word in
    ["hello", "hi", "hey", "hii"]):

        reply = """
        Hello 👋<br><br>

        Welcome to BloodBridge AI Assistant ❤️<br><br>

        Ask me about:<br>

        🩸 Blood donation<br>
        📍 GPS donor matching<br>
        🚨 Emergency requests<br>
        🧬 Blood compatibility<br>
        🤖 AI features
        """

    elif any(word in user_message for word in
    ["blood", "group", "types"]):

        reply = """
        🩸 Blood Groups Available:<br><br>

        ✔ A+<br>
        ✔ A-<br>
        ✔ B+<br>
        ✔ B-<br>
        ✔ O+<br>
        ✔ O-<br>
        ✔ AB+<br>
        ✔ AB-
        """

    elif any(word in user_message for word in
    ["compatible", "compatibility", "match"]):

        reply = """
        🧬 Blood Compatibility:<br><br>

        🩸 O- → Universal Donor<br>
        🩸 AB+ → Universal Receiver
        """

    elif any(word in user_message for word in
    ["donate", "donation", "eligible"]):

        reply = """
        ❤️ Donation Rules:<br><br>

        ✔ Age above 18<br>
        ✔ Healthy condition<br>
        ✔ 90 days gap required
        """

    elif any(word in user_message for word in
    ["gps", "distance", "nearby"]):

        reply = """
        📍 GPS Matching:<br><br>

        AI automatically finds nearest donors using live GPS.
        """

    elif any(word in user_message for word in
    ["emergency", "critical", "urgent"]):

        reply = """
        🚨 Emergency Support:<br><br>

        Critical requests get higher AI priority.
        """

    elif any(word in user_message for word in
    ["ai", "smart", "ranking"]):

        reply = """
        🤖 AI Features:<br><br>

        ✔ Smart donor ranking<br>
        ✔ Distance-based priority<br>
        ✔ Emergency optimization
        """

    elif any(word in user_message for word in
    ["thanks", "thank you"]):

        reply = """
        ❤️ You're Welcome.<br><br>

        Thank you for supporting blood donation.
        """

    else:

        reply = f"""
        😅 Sorry, I couldn't understand:<br><br>

        <b>{user_message}</b><br><br>

        Ask about:<br>

        🩸 Blood groups<br>
        📍 GPS<br>
        🤖 AI<br>
        🚨 Emergency
        """

    return jsonify({
        "reply": reply
    })

# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
