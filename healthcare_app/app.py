from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import random
import json
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'
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
    adminID = db.Column(db.Integer)



class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', backref='feedbacks')


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
    final_price=db.Column(db.Float)
    final_vendor=db.Column(db.String(50))
    patient = db.relationship('User', backref='orders')
    prescription = db.relationship('Prescription', backref='orders')





# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- HELPER FUNCTIONS ---
import random

def get_price_comparison(medicine_name):
    # Simulates real-time fetching and adds slight variation
    base_price = round(random.uniform(100, 400), 2)
    
    vendors = {
        "Apollo Pharmacy": {
            "price": base_price,
            "link": f"https://www.apollopharmacy.in/search/{medicine_name}",
        },
        "MedPlus Mart": {
            "price": round(base_price * 0.93, 2), # 7% cheaper
            "link": f"https://www.medplusmart.com/search/{medicine_name}",
        },
        "NetMeds": {
            "price": round(base_price * 1.05, 2), # 5% pricier
            "link": f"https://www.netmeds.com/catalogsearch/result?q={medicine_name}",
        }
    }
    
    # Sort to easily find the cheapest vendor
    cheapest = min(vendors.items(), key=lambda item: item[1]['price'])
    
    return vendors, cheapest
# --------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        address = request.form['address']
        contact = request.form['contact']
        password = generate_password_hash(request.form['password'])

        # ✅ Patient registration
        if role == 'patient':
            dob = request.form['dob']
            height = float(request.form['height'])
            weight = float(request.form['weight'])
            bmi = round(weight / ((height / 100) ** 2), 2)

            new_user = User(
                role=role,
                name=name,
                dob=dob,
                height=height,
                weight=weight,
                bmi=bmi,
                address=address,
                contact=contact,
                password=password
            )

        # ✅ Doctor registration
        elif role == 'doctor':
            specialization = request.form['specialization']
            hospital = request.form['hospital']
            experience = int(request.form['experience'])
            location = request.form['location']

            new_user = User(
                role=role,
                name=name,
                specialization=specialization,
                hospital=hospital,
                experience=experience,
                location=location,
                address=address,
                contact=contact,
                password=password
            )

        # ✅ Admin registration
        elif role == 'admin':
            new_user = User(
                role=role,
                name=name,
                address=address,
                contact=contact,
                password=password
            )

        # ❌ If role is invalid
        else:
            flash("Invalid role selected. Please try again.")
            return redirect(url_for('register'))

        # ✅ Save to database
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ... (Login logic remains the same) ...
        identifier = request.form['identifier']
        password = request.form['password']

        user = User.query.filter(
            (User.contact == identifier) | (User.name == identifier)
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['role'] = user.role
            return redirect('/patient_dashboard' if user.role == 'patient' else '/admin_dashboard' if user.role == 'admin' else '/doctor_dashboard')
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

@app.route('/patient/profile')
@login_required
def patient_profile():
    return render_template('patient_profile.html')

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime




# -----------------------------
# Routes
# -----------------------------
@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    message = request.form['message']
    feedback = Feedback(patient_id=current_user.id, message=message)
    db.session.add(feedback)
    db.session.commit()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for('patient_dashboard'))





@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin_dashboard.html', feedbacks=feedbacks)



# In app.py - Patient Orders
@app.route('/patient/my_orders')
@login_required
def my_orders():
    if current_user.role != 'patient':
        return redirect(url_for('patient_dashboard'))
    
    orders = Order.query.filter_by(patient_id=current_user.id).all()
    
    return render_template('my_orders.html', orders=orders)


# In app.py - E-Pharmacy 
@app.route('/epharmacy', methods=['GET', 'POST'])
@login_required
def epharmacy():
    if current_user.role != 'patient':
        return redirect(url_for('patient_dashboard'))

    # Get available prescriptions (not yet ordered)
    available_prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id,
        status='Available'
    ).all()
    
    # Handle order submission
    if request.method == 'POST':
        pres_id = request.form.get('prescription_id')
        vendor_name = request.form.get('vendor')
        final_price = request.form.get('final_price')
        
        if not pres_id or not vendor_name or not final_price:
            flash("Missing order details.", "danger")
            return redirect(url_for('epharmacy'))

        prescription = Prescription.query.get(pres_id)
        
        # 1. Create the Order
        new_order = Order(
            patient_id=current_user.id,
            prescription_id=pres_id,
            status='Ordered', 
            final_price=float(final_price),
            final_vendor=vendor_name
        )
        
        # 2. Update Prescription Status
        prescription.status = 'Ordered'
        
        db.session.add(new_order)
        db.session.commit()
        
        flash(f"🎉 Order Confirmed with {vendor_name} for ₹{final_price}! Click the link to complete purchase.", "success")
        return redirect(url_for('epharmacy'))

    # Handle display logic (GET)
    return render_template('epharmacy.html', prescriptions=available_prescriptions)

# In app.py - Compare Prices
@app.route('/compare/<medicine_name>/<int:pres_id>')
@login_required
def compare_prices(medicine_name, pres_id):
    vendors, cheapest = get_price_comparison(medicine_name)
    prescription = Prescription.query.get_or_404(pres_id)

    return render_template('compare_prices.html', 
                           vendors=vendors, 
                           cheapest=cheapest,
                           medicine_name=medicine_name,
                           pres_id=pres_id,
                           prescription=prescription)


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
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'POST':
        order_id = request.form['order_id']
        new_status = request.form['status']
        
        order = Order.query.get(order_id)
        
        if order:
            order.status = new_status
            db.session.commit()
            flash(f"Order #{order_id} status updated to {new_status}!", 'success')
        return redirect(url_for('manage_orders'))

    # Fetch all orders to display
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


@app.route('/chatbot_api', methods=['POST'])
@login_required
def chatbot_api():
    # --- Integration of Language Logic into Chatbot ---
    user_lang_code = session.get('language', 'en')
    lang_name = {"en": "English", "ta": "Tamil", "hi": "Hindi"}.get(user_lang_code, "English")
    # --- End Language Logic ---

    user_input = request.form['user_input']
    api_key = "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"  # Replace with your actual key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            # Instruct the AI to reply in the user's selected language
            "content": f"You are a healthcare assistant. Provide first aid advice and recommend a specialist. Reply fully in {lang_name}."
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
             # Fallback to local logic if API fails
            return chatbot_local_fallback(user_input, user_lang_code)

        content = result['choices'][0]['message']['content']
        # The AI is instructed to reply in a chosen language, no need for JSON parsing here.

        # --- Local Specialist Match (Case-Insensitive) ---
        # Look for keywords to match a local specialist, even if AI is active
        specialist = match_specialist(user_input)

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
        
        reply = content + doctor_info # Append local doctor info to AI response

    except Exception as e:
        # Use local fallback on any API error
        return chatbot_local_fallback(user_input, user_lang_code, error=str(e))

    return jsonify({'reply': reply})


# --- NEW LOCAL FALLBACK FUNCTION (Translates based on lang_code) ---
def chatbot_local_fallback(user_input, lang_code, error=None):
    """Provides simple, reliable, local responses when API fails."""
    
    specialist = match_specialist(user_input)
    
    # Simple, pre-translated replies (Need to expand this for full multilingual support)
    FALLBACK_REPLIES = {
        "en": "Please rest and consult a doctor if symptoms persist.",
        "ta": "தயவுசெய்து ஓய்வெடுக்கவும், அறிகுறிகள் தொடர்ந்தால் மருத்துவரை அணுகவும்.",
        "hi": "कृपया आराम करें और यदि लक्षण बने रहें तो डॉक्टर से सलाह लें।",
    }
    
    error_msg = f"API Error: {error}. " if error else ""
    first_aid_msg = FALLBACK_REPLIES.get(lang_code, FALLBACK_REPLIES['en'])

    # Look for a matching doctor (case-insensitive)
    doctor = User.query.filter_by(role='doctor').filter(
        func.lower(User.specialization) == specialist.lower()
    ).first()

    if doctor:
        doctor_info = (
            f"\n\n🩺 **Recommended Specialist**:\n"
            f"Dr. {doctor.name}\n"
            f"{doctor.specialization}, {doctor.hospital}\n"
            f"Location: {doctor.location}"
        )
    else:
        doctor_info = f"\n\n⚠️ No {specialist} available currently in the system."
        
    reply = f"🆘 {error_msg}{first_aid_msg}" + doctor_info
    return jsonify({'reply': reply})

# --- NEW LOCAL SPECIALIST MATCHER FUNCTION ---
def match_specialist(user_input):
    """Simple keyword matching to find specialist type."""
    user_input = user_input.lower()
    symptoms_map = {
        "heart": "Cardiologist",
        "chest": "Cardiologist",
        "throat": "ENT",
        "fever": "General Physician",
        "skin": "Dermatologist",
        "eye": "Ophthalmologist",
        "ear": "ENT",
        "headache": "Neurologist",
    }
    for keyword, specialist in symptoms_map.items():
        if keyword in user_input:
            return specialist
    return "General Physician"
# --------------------------------------------------------


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