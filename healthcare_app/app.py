from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask import request, jsonify
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# PostgreSQL configuration (edit password/db name as per your setup)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/healthcaredb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10))  # patient or doctor
    name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi = db.Column(db.Float)
    address = db.Column(db.String(200))
    contact = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(200))
    specialization = db.Column(db.String(100))
    hospital = db.Column(db.String(200))
    experience = db.Column(db.Integer)
    location = db.Column(db.String(100))
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    reason = db.Column(db.String(200))

    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_appointments')
class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(20))
    medicine = db.Column(db.String(200))
    dosage = db.Column(db.String(200))
    instructions = db.Column(db.String(500))
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='Available')
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'))
    status = db.Column(db.String(50), default="Pending")

    patient = db.relationship('User', backref='orders')
    prescription = db.relationship('Prescription', backref='orders')


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Form submitted!")
        print(request.form)
        #print("🔥 Register form submitted")  # Debug log
        role = request.form['role']
        name = request.form['name']
        address = request.form['address']
        contact = request.form['contact']
        password = generate_password_hash(request.form['password'])

        if role == 'patient':
            dob = request.form['dob']
            height = float(request.form['height'])
            weight = float(request.form['weight'])
            bmi = round(weight / ((height / 100) ** 2), 2)
            new_user = User(role=role, name=name, dob=dob, height=height, weight=weight,
                            bmi=bmi, address=address, contact=contact, password=password)
        else:
            specialization = request.form['specialization']
            hospital = request.form['hospital']
            experience = int(request.form['experience'])
            location = request.form['location']
            new_user = User(role=role, name=name, specialization=specialization,
                            hospital=hospital, experience=experience, location=location,
                            address=address, contact=contact, password=password)

        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']  # could be contact or username
        password = request.form['password']

        # Try fetching user by contact OR name
        user = User.query.filter(
            (User.contact == identifier) | (User.name == identifier)
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['role'] = user.role
            return redirect('/patient_dashboard' if user.role == 'patient' else '/doctor_dashboard')
        else:
            return render_template('login.html', error="Invalid username/contact or password")
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect('/login')

@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    if session.get('role') == 'patient':
        return render_template('patient_dashboard.html')
    return redirect('/login')

# In app.py - Replace your existing epharmacy route
from flask import flash # Ensure this is imported at the top

@app.route('/epharmacy', methods=['GET', 'POST'])
@login_required
def epharmacy():
    if current_user.role != 'patient':
        return redirect(url_for('patient_dashboard'))

    if request.method == 'POST':
        # --- POST: Place the Order ---
        try:
            prescription_id = int(request.form['prescription_id'])
        except KeyError:
            # Should not happen with the correct HTML, but handles missing form data
            flash("Error: Please select a valid prescription.", "danger")
            return redirect(url_for('epharmacy'))

        # 1. Fetch the prescription
        prescription = Prescription.query.get(prescription_id)

        if not prescription or prescription.status != 'Available':
            flash("Error: This prescription is unavailable or already ordered.", "danger")
            return redirect(url_for('epharmacy'))

        # 2. Update status and save the actual order
        prescription.status = 'Ordered'
        
        new_order = Order(
            patient_id=current_user.id,
            prescription_id=prescription.id,
            status='Pending'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        flash(f"✅ Order placed successfully for {prescription.medicine}! Total amount: ₹{prescription.price:.2f}", "success")
        return redirect(url_for('epharmacy'))

    # --- GET: Display Available Prescriptions ---
    available_prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id,
        status='Available'
    ).all()

    return render_template('epharmacy.html', prescriptions=available_prescriptions)

# In app.py - Add this new route


@app.route('/doctor/appointments')
@login_required
def doctor_appointments():
    if current_user.role != 'doctor':
        return redirect('/login')
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
    return render_template('doctor_appointments.html', appointments=appointments)

@app.route('/doctor/manage_orders', methods=['GET', 'POST'])
@login_required
def manage_orders():
    if current_user.role != 'doctor':
        # You might want a different user role for management in a real app,
        # but for now, we'll assign it to the doctor role.
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'POST':
        # --- POST: Update Order Status ---
        order_id = request.form['order_id']
        new_status = request.form['status']
        
        order = Order.query.get(order_id)
        
        # Security: Only allow doctors to manage orders for their prescribed medicines
        # (Optional but recommended, let's skip for simplicity now and show all)
        
        if order:
            order.status = new_status
            db.session.commit()
            flash(f"Order #{order_id} status updated to {new_status}!", 'success')
        return redirect(url_for('manage_orders'))

    # --- GET: Display all orders ---
    # Fetch all orders to display in the management dashboard
    orders = Order.query.all()
    
    return render_template('manage_orders.html', orders=orders)
@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if session.get('role') == 'doctor':
        return render_template('doctor_dashboard.html')
    return redirect('/login')
@app.route('/doctor/patient_history')
@login_required
def patient_history():
    if current_user.role != 'doctor':
        return redirect('/login')

    patients = User.query.filter_by(role='patient').all()
    return render_template('patient_history.html', patients=patients)
@app.route('/doctor/patient_history/<int:patient_id>')
@login_required
def view_patient_history(patient_id):
    if current_user.role != 'doctor':
        return redirect('/login')

    patient = User.query.get_or_404(patient_id)
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()

    return render_template('view_patient_history.html', patient=patient, prescriptions=prescriptions)



@app.route('/doctor/prescribe', methods=['GET', 'POST'])
@login_required
def prescribe_medicine():
    if current_user.role != 'doctor':
        return redirect('/login')

    patients = User.query.filter_by(role='patient').all()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        date = request.form['date']
        medicine = request.form['medicine']
        dosage = request.form['dosage']
        instructions = request.form['instructions']
        price = float(request.form['price'])
        prescription = Prescription (
            doctor_id=current_user.id,
            patient_id=patient_id,
            date=date,
            medicine=medicine,
            dosage=dosage,
            instructions=instructions,
            price=price
        )
        db.session.add(prescription)
        db.session.commit()
        return redirect('/doctor_dashboard')

    return render_template('prescribe_medicine.html', patients=patients)



@app.route('/doctor/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.hospital = request.form['hospital']
        current_user.experience = int(request.form['experience'])
        current_user.location = request.form['location']
        db.session.commit()
        return redirect('/doctor_dashboard')
    return render_template('edit_profile.html')


@app.route('/chatbot')
@login_required
def chatbot_page():
    return render_template('chatbot.html')



import json
import requests
from sqlalchemy import func

@app.route('/chatbot_api', methods=['POST'])
@login_required
def chatbot_api():
    user_input = request.form['user_input']
    api_key = "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"  # Replace with your real key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are a healthcare assistant. Based on symptoms, first give first aid advice "
                "and clearly mention what type of specialist (e.g., Cardiologist, Neurologist, etc.) is needed. "
                "Reply ONLY in JSON format like this:\n"
                "{\"first_aid\": \"...\", \"specialist\": \"Cardiologist\"}"
            )
        },
        {"role": "user", "content": user_input}
    ]

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": messages
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()

        if 'choices' not in result:
            return jsonify({'reply': f"⚠️ Error: {result.get('error', 'No response received')}"})

        content = result['choices'][0]['message']['content']

        # Convert the model's string output to a dictionary safely
        content_dict = json.loads(content)

        specialist = content_dict.get("specialist", "").strip()
        first_aid = content_dict.get("first_aid", "No first aid info provided.")

        # Look for a matching doctor (case-insensitive)
        doctor = User.query.filter_by(role='doctor').filter(
            func.lower(User.specialization) == specialist.lower()
        ).first()

        if doctor:
            doctor_info = (
                f"\n\n🩺 **Recommended Specialist**:\n"
                f"Dr. {doctor.name}\n"
                f"{doctor.specialization}, {doctor.hospital}\n"
                f"Location: {doctor.location} | Experience: {doctor.experience} years"
            )
        else:
            doctor_info = f"\n\n⚠️ No {specialist} available currently in the system."

        reply = f"🆘 **First Aid**:\n{first_aid}{doctor_info}"

    except Exception as e:
        reply = f"⚠️ Error occurred: {str(e)}"

    return jsonify({'reply': reply})

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if current_user.role != 'patient':
        return redirect('/login')

    doctors = User.query.filter_by(role='doctor').all()

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']

        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            date=date,
            time=time,
            reason=reason
        )
        db.session.add(appointment)
        db.session.commit()
        return redirect('/patient_dashboard')

    return render_template('book_appointment.html', doctors=doctors)


# Create DB tables once
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)