from flask import Flask, render_template, jsonify, request
import threading
import time
import random
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# File path for medication database
MEDICATION_DB_FILE = 'medications.json'

def load_medications():
    if os.path.exists(MEDICATION_DB_FILE):
        with open(MEDICATION_DB_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default medications
        return {
            "Levothyroxine": {
                "shape": "oval",
                "color": "white",
                "imprint": "L50",
                "schedule": ["06:30"],
                "critical": True,
                "dose": "50 mcg",
                "icon": "💊"
            },
            "Aspirin": {
                "shape": "round",
                "color": "white",
                "imprint": "ASP81",
                "schedule": ["08:00"],
                "critical": False,
                "dose": "75 mg",
                "icon": "💊"
            },
            "Metformin": {
                "shape": "oval",
                "color": "blue",
                "imprint": "M500",
                "schedule": ["13:00"],
                "critical": True,
                "dose": "500 mg",
                "icon": "💊"
            },
            "Donepezil": {
                "shape": "round",
                "color": "yellow",
                "imprint": "D5",
                "schedule": ["20:00"],
                "critical": True,
                "dose": "5 mg",
                "icon": "💊"
            },
            "Atorvastatin": {
                "shape": "oval",
                "color": "pink",
                "imprint": "A10",
                "schedule": ["21:00"],
                "critical": False,
                "dose": "10 mg",
                "icon": "💊"
            }
        }

def save_medications(meds):
    with open(MEDICATION_DB_FILE, 'w') as f:
        json.dump(meds, f, indent=4)

# Load medications from file
MEDICATION_DB = load_medications()

# System state with historical data
system_state = {
    "current_med": None,
    "missed_count": 2,
    "compliance_history": [],
    "alerts": [
        {
            "level": "family",
            "message": "Missed dose of Aspirin",
            "medication": "Aspirin",
            "time": "08:05:00",
            "read": False
        }
    ],
    "next_dose_time": datetime.now().replace(hour=13, minute=0, second=0),
    "last_check": datetime.now().replace(hour=8, minute=14, second=0),
    "compliance_rate": 87,
    "status": "alert"
}

def calculate_compliance():
    total = len(system_state["compliance_history"])
    if total == 0:
        return 100
    taken = sum(1 for e in system_state["compliance_history"] if e["status"] == "Taken")
    return round((taken / total) * 100)

def get_current_medication():
    now = datetime.now().strftime("%H:%M")
    for med, details in MEDICATION_DB.items():
        if now in details["schedule"]:
            return med
    return None

def verify_pill(camera_input, expected_med):
    expected = MEDICATION_DB[expected_med]
    if random.random() > 0.15:
        return camera_input == expected
    return False

def send_alert(level, medication, emergency=False):
    if emergency:
        message = "EMERGENCY: Help button pressed! Medical assistance requested!"
    else:
        alert_types = {
            "family": f"Missed dose of {medication}",
            "caregiver": f"URGENT: 3 consecutive misses of {medication}",
            "emergency": f"EMERGENCY: Critical medication {medication} missed!"
        }
        message = alert_types[level]
    
    alert = {
        "level": level,
        "message": message,
        "medication": medication if not emergency else "Emergency",
        "time": datetime.now().strftime("%H:%M:%S"),
        "read": False
    }
    
    system_state["alerts"].insert(0, alert)
    system_state["status"] = "alert" if level != "emergency" else "emergency"

def medication_check():
    current_med = get_current_medication()
    if not current_med:
        return
        
    med_details = MEDICATION_DB[current_med]
    system_state["current_med"] = current_med
    
    if random.random() < 0.7:
        user_pill = med_details
    else:
        other_med = random.choice([m for m in MEDICATION_DB.keys() if m != current_med])
        user_pill = MEDICATION_DB[other_med]
    
    if verify_pill(user_pill, current_med):
        result = "Taken"
        system_state["missed_count"] = 0
    else:
        result = "Missed"
        system_state["missed_count"] += 1
        
        if med_details["critical"]:
            send_alert("emergency", current_med)
        elif system_state["missed_count"] >= 3:
            send_alert("caregiver", current_med)
        else:
            send_alert("family", current_med)
    
    event = {
        "medication": current_med,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": result,
        "details": f"Expected: {med_details['shape']} {med_details['color']}, Scanned: {user_pill['shape']} {user_pill['color']}"
    }
    
    system_state["compliance_history"].insert(0, event)
    system_state["last_check"] = datetime.now()
    system_state["compliance_rate"] = calculate_compliance()
    schedule_next_dose()

def schedule_next_dose():
    now = datetime.now()
    next_time = None
    
    for med, details in MEDICATION_DB.items():
        for time_str in details["schedule"]:
            med_time = datetime.strptime(time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day)
            if med_time > now and (next_time is None or med_time < next_time):
                next_time = med_time
    
    if next_time:
        system_state["next_dose_time"] = next_time

def background_scheduler():
    while True:
        now = datetime.now()
        if now >= system_state["next_dose_time"]:
            medication_check()
            time.sleep(10)
        time.sleep(5)

# Start background thread
scheduler_thread = threading.Thread(target=background_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

@app.route('/')
def dashboard():
    return render_template('dashboard.html', 
                           state=system_state, 
                           meds=MEDICATION_DB,
                           now=datetime.now())

@app.route('/history')
def history():
    return render_template('history.html', 
                           history=system_state["compliance_history"],
                           state=system_state)

@app.route('/add_medication', methods=['POST'])
def add_medication():
    # Get form data
    data = request.get_json()
    name = data.get('name')
    dose = data.get('dose')
    schedule = [t.strip() for t in data.get('schedule').split(',')]
    critical = data.get('critical', False)
    icon = data.get('icon', '💊')
    
    # Add to database
    MEDICATION_DB[name] = {
        "dose": dose,
        "schedule": schedule,
        "critical": critical,
        "icon": icon,
        "shape": data.get('shape', 'round'),
        "color": data.get('color', 'white'),
        "imprint": data.get('imprint', '')
    }
    
    # Save to file
    save_medications(MEDICATION_DB)
    
    # Recalculate next dose
    schedule_next_dose()
    
    return jsonify(success=True)

@app.route('/delete_medication', methods=['POST'])
def delete_medication():
    data = request.get_json()
    name = data.get('name')
    if name in MEDICATION_DB:
        del MEDICATION_DB[name]
        save_medications(MEDICATION_DB)
        schedule_next_dose()
    return jsonify(success=True)

@app.route('/data')
def data():
    return jsonify({
        "state": system_state,
        "meds": MEDICATION_DB
    })

@app.route('/mark_alert_read/<int:index>')
def mark_alert_read(index):
    if index < len(system_state["alerts"]):
        system_state["alerts"][index]["read"] = True
        if all(alert["read"] for alert in system_state["alerts"]):
            system_state["status"] = "normal"
    return jsonify(success=True)

@app.route('/trigger_emergency', methods=['POST'])
def trigger_emergency():
    send_alert("emergency", "", emergency=True)
    return jsonify(success=True)

# Dashboard Template
dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>MediGuardian Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --teal: #20B2AA;
            --orange: #FFA500;
            --alert: #FF6B6B;
            --emergency: #FF0000;
        }
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
        }
        .card {
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: none;
        }
        .status-normal { border-left: 5px solid var(--teal); }
        .status-alert { border-left: 5px solid var(--orange); }
        .status-emergency { border-left: 5px solid var(--emergency); }
        .med-card { background-color: #e6f7ff; }
        .alert-card { background-color: #fff3cd; }
        .compliance-card { background-color: #e6ffe6; }
        .history-card { background-color: #f8f9fa; }
        .critical { color: var(--emergency); font-weight: bold; }
        .next-dose {
            background: linear-gradient(135deg, var(--teal), var(--orange));
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .compliance-ring {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: conic-gradient(var(--teal) 0% {{ state.compliance_rate * 3.6 }}deg, #eee 0);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }
        .alert-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: var(--emergency);
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        .alert-item {
            border-left: 3px solid;
            margin-bottom: 8px;
            padding-left: 10px;
        }
        .alert-family { border-color: var(--orange); }
        .alert-caregiver { border-color: #FF8C00; }
        .alert-emergency { border-color: var(--emergency); }
        .med-icon { font-size: 2rem; }
        .alert-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #FF0000, #FF6B6B);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            box-shadow: 0 4px 12px rgba(255, 0, 0, 0.4);
            z-index: 1000;
            cursor: pointer;
            animation: pulse 2s infinite;
            border: 2px solid white;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(255, 0, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
        }
        .alert-button:hover {
            transform: scale(1.05);
            background: linear-gradient(135deg, #FF0000, #FF4D4D);
        }
        .schedule-table th {
            background-color: var(--teal);
            color: white;
        }
        .badge-taken { background-color: #28a745; }
        .badge-missed { background-color: #dc3545; }
        .badge-pending { background-color: #6c757d; }
        .modal-content {
            border-radius: 15px;
        }
        .manage-btn {
            position: fixed;
            bottom: 100px;
            right: 20px;
            z-index: 1000;
        }
        .icon-option {
            font-size: 2rem;
            cursor: pointer;
            padding: 10px;
            border-radius: 50%;
            border: 2px solid transparent;
            transition: all 0.3s;
        }
        .icon-option.selected {
            border-color: var(--teal);
            background-color: rgba(32, 178, 170, 0.1);
            transform: scale(1.1);
        }
        .icon-option:hover {
            background-color: rgba(32, 178, 170, 0.1);
        }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="display-4"><i class="fas fa-heartbeat"></i> MediGuardian</h1>
            <div class="status-indicator">
                <span class="badge bg-{% if state.status == 'normal' %}teal{% elif state.status == 'alert' %}warning{% else %}danger{% endif %} p-2">
                    Status: <span class="text-uppercase">{{ state.status }}</span>
                </span>
            </div>
        </div>
        
        <div class="row">
            <!-- Left Column -->
            <div class="col-md-4">
                <!-- Next Medication Card -->
                <div class="card status-{{ state.status }}">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-clock"></i> Next Medication</h5>
                        {% if state.next_dose_time %}
                            <div class="next-dose mt-3 mb-3">
                                {% if state.current_med %}
                                    <h3 class="mt-2">{{ meds[state.current_med]['icon'] }} {{ state.current_med }}</h3>
                                    <p>{{ meds[state.current_med]['dose'] }}</p>
                                {% endif %}
                                <h2>{{ state.next_dose_time.strftime('%H:%M') }}</h2>
                                <div class="text-center mt-2">
                                    <p class="mb-1">Time remaining: 
                                        <span id="countdown">4h 46m</span>
                                    </p>
                                </div>
                            </div>
                        {% else %}
                            <p class="text-muted">No medications scheduled</p>
                        {% endif %}
                    </div>
                </div>
                
                <!-- Compliance Card -->
                <div class="card compliance-card">
                    <div class="card-body text-center">
                        <h5 class="card-title"><i class="fas fa-chart-line"></i> Compliance Rate</h5>
                        <div class="compliance-ring my-3">
                            <div class="inner-circle bg-white rounded-circle d-flex align-items-center justify-content-center" 
                                style="width: 90px; height: 90px;">
                                <h2 class="mb-0">{{ state.compliance_rate }}%</h2>
                            </div>
                        </div>
                        <p class="mb-0">{{ state.compliance_history|length }} tracked doses</p>
                    </div>
                </div>
                
                <!-- Medication Schedule Card -->
                <div class="card med-card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-calendar-alt"></i> Today's Schedule</h5>
                        <div class="table-responsive">
                            <table class="table schedule-table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Medicine</th>
                                        <th>Dose</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for med_name, details in meds.items() %}
                                        {% for time in details.schedule %}
                                            <tr>
                                                <td>{{ time }}</td>
                                                <td>{{ med_name }}</td>
                                                <td>{{ details.dose }}</td>
                                                <td>
                                                    {% if time == "06:30" %}
                                                        <span class="badge badge-taken">Taken</span>
                                                    {% elif time == "08:00" %}
                                                        <span class="badge badge-missed">Missed</span>
                                                    {% else %}
                                                        <span class="badge badge-pending">Pending</span>
                                                    {% endif %}
                                                </td>
                                            </tr>
                                        {% endfor %}
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Column -->
            <div class="col-md-8">
                <!-- Alerts Card -->
                <div class="card alert-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title"><i class="fas fa-bell"></i> Alerts</h5>
                            <span class="position-relative">
                                <i class="fas fa-bell fs-4"></i>
                                {% set unread = state.alerts|selectattr('read', 'false')|list|length %}
                                {% if unread > 0 %}
                                    <span class="alert-badge">{{ unread }}</span>
                                {% endif %}
                            </span>
                        </div>
                        <div class="mt-3">
                            {% if state.alerts %}
                                {% for alert in state.alerts %}
                                <div class="alert-item alert-{{ alert.level }} {% if alert.read %}text-muted{% endif %}">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <strong>{{ alert.message }}</strong>
                                            <div class="text-muted small">{{ alert.time }}</div>
                                        </div>
                                        {% if not alert.read %}
                                        <button class="btn btn-sm btn-outline-secondary mark-read" 
                                                data-index="{{ loop.index0 }}">
                                            Mark Read
                                        </button>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <p class="text-muted">No alerts</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- History Card -->
                <div class="card history-card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-history"></i> Recent History</h5>
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Medication</th>
                                        <th>Status</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for event in state.compliance_history[:5] %}
                                    <tr>
                                        <td>{{ event.time }}</td>
                                        <td>{{ event.medication }}</td>
                                        <td>
                                            {% if event.status == "Taken" %}
                                                <span class="badge badge-taken">Taken</span>
                                            {% else %}
                                                <span class="badge badge-missed">Missed</span>
                                            {% endif %}
                                        </td>
                                        <td><small>{{ event.details }}</small></td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="4" class="text-center text-muted">No history yet</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        <div class="text-end">
                            <small><a href="/history">View full history ({{ state.compliance_history|length }} events)</a></small>
                        </div>
                    </div>
                </div>
                
                <!-- System Status Card -->
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-info-circle"></i> System Status</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <ul class="list-group">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Last Check:</span>
                                        <span>{{ state.last_check.strftime('%Y-%m-%d %H:%M:%S') }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Missed Doses:</span>
                                        <span>{{ state.missed_count }} (last 7 days)</span>
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <ul class="list-group">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Current Medication:</span>
                                        <span>
                                            {% if state.current_med %}
                                                {{ state.current_med }}
                                            {% else %}
                                                None
                                            {% endif %}
                                        </span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>System Mode:</span>
                                        <span class="text-uppercase">{{ state.status }}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Medication Management Button -->
    <button class="btn btn-primary manage-btn" data-bs-toggle="modal" data-bs-target="#manageMedsModal">
        <i class="fas fa-pills"></i> Manage Medications
    </button>
    
    <!-- EMERGENCY ALERT Button -->
    <div class="alert-button" data-bs-toggle="modal" data-bs-target="#emergencyModal">
        <i class="fas fa-exclamation-triangle"></i>
    </div>
    
    <!-- Medication Management Modal -->
    <div class="modal fade" id="manageMedsModal" tabindex="-1" aria-labelledby="manageMedsModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title" id="manageMedsModalLabel">
                        <i class="fas fa-pills"></i> Manage Medications
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-4">
                        <h5>Current Medications</h5>
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Medication</th>
                                        <th>Dose</th>
                                        <th>Schedule</th>
                                        <th>Critical</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="medicationsList">
                                    {% for med, details in meds.items() %}
                                    <tr id="med-{{ med }}">
                                        <td>{{ details.icon }} {{ med }}</td>
                                        <td>{{ details.dose }}</td>
                                        <td>
                                            {% for time in details.schedule %}
                                                <span class="badge bg-teal me-1">{{ time }}</span>
                                            {% endfor %}
                                        </td>
                                        <td>
                                            {% if details.critical %}
                                                <span class="badge bg-danger">Critical</span>
                                            {% else %}
                                                <span class="badge bg-secondary">Normal</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            <button class="btn btn-sm btn-danger delete-med" data-med="{{ med }}">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <hr>
                    
                    <h5 class="mb-3">Add New Medication</h5>
                    <form id="addMedicationForm">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Medication Name</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Dose</label>
                                <input type="text" class="form-control" name="dose" required 
                                       placeholder="e.g., 50 mg, 10 units">
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Schedule Times</label>
                            <input type="text" class="form-control" name="schedule" required
                                   placeholder="Enter times separated by commas (e.g., 08:00, 13:00, 20:00)">
                            <div class="form-text">Use 24-hour format (HH:MM)</div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Icon</label>
                                <select class="form-select" name="icon">
                                    <option value="💊">💊 Pill</option>
                                    <option value="💉">💉 Injection</option>
                                    <option value="🧪">🧪 Liquid</option>
                                    <option value="🧴">🧴 Cream</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Critical Medication</label>
                                <div class="form-check form-switch mt-2">
                                    <input class="form-check-input" type="checkbox" name="critical" id="criticalSwitch">
                                    <label class="form-check-label" for="criticalSwitch">Mark as critical</label>
                                </div>
                            </div>
                        </div>
                        
                        <div class="text-center">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-plus"></i> Add Medication
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Emergency Modal -->
    <div class="modal fade" id="emergencyModal" tabindex="-1" aria-labelledby="emergencyModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title" id="emergencyModalLabel">
                        <i class="fas fa-exclamation-triangle"></i> Emergency Assistance
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center mb-4">
                        <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
                        <h3 class="text-danger">Emergency Assistance Request</h3>
                    </div>
                    
                    <div class="alert alert-danger">
                        <p class="mb-1"><strong>Pressing the emergency button will:</strong></p>
                        <ul class="mb-0">
                            <li>Notify all emergency contacts immediately</li>
                            <li>Alert local emergency services (108)</li>
                            <li>Share your current location with responders</li>
                            <li>Activate voice assistance for hands-free help</li>
                            <li>Unlock doors for emergency access</li>
                        </ul>
                    </div>
                    
                    <div class="mt-4">
                        <p class="mb-1"><strong>Emergency contacts:</strong></p>
                        <ul>
                            <li>Sarah Johnson (Daughter) - +91 8590586955</li>
                            <li>John Smith (Caregiver) - +91 7036985373</li>
                            <li>Local EMS - +91 9054242294</li>
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger btn-lg" id="confirmEmergency">
                        <i class="fas fa-bell"></i> REQUEST EMERGENCY HELP
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Update countdown timer
        function updateCountdown() {
            const nextDoseTime = new Date("{{ state.next_dose_time.strftime('%Y-%m-%dT%H:%M:%S') }}");
            const now = new Date();
            
            if (nextDoseTime > now) {
                const diff = Math.floor((nextDoseTime - now) / 1000);
                const hours = Math.floor(diff / 3600);
                const minutes = Math.floor((diff % 3600) / 60);
                const seconds = diff % 60;
                
                document.getElementById('countdown').innerText = 
                    `${hours}h ${minutes}m ${seconds}s`;
            } else {
                document.getElementById('countdown').innerText = "Due now";
            }
        }
        
        // Update data periodically
        function updateData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    // Update the medications list
                    const medsList = document.getElementById('medicationsList');
                    medsList.innerHTML = '';
                    
                    for (const [med, details] of Object.entries(data.meds)) {
                        const criticalBadge = details.critical ? 
                            '<span class="badge bg-danger">Critical</span>' : 
                            '<span class="badge bg-secondary">Normal</span>';
                        
                        let scheduleBadges = '';
                        for (const time of details.schedule) {
                            scheduleBadges += `<span class="badge bg-teal me-1">${time}</span>`;
                        }
                        
                        medsList.innerHTML += `
                            <tr id="med-${med}">
                                <td>${details.icon} ${med}</td>
                                <td>${details.dose}</td>
                                <td>${scheduleBadges}</td>
                                <td>${criticalBadge}</td>
                                <td>
                                    <button class="btn btn-sm btn-danger delete-med" data-med="${med}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `;
                    }
                    
                    // Reattach delete event listeners
                    document.querySelectorAll('.delete-med').forEach(button => {
                        button.addEventListener('click', function() {
                            const medName = this.getAttribute('data-med');
                            if (confirm(`Are you sure you want to delete ${medName}?`)) {
                                fetch('/delete_medication', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({ name: medName })
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        document.getElementById(`med-${medName}`).remove();
                                        // Refresh the page to update the schedule
                                        setTimeout(() => location.reload(), 500);
                                    }
                                });
                            }
                        });
                    });
                });
                
            setTimeout(updateData, 5000); // Update every 5 seconds
        }
        
        // Add medication form
        document.getElementById('addMedicationForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                name: formData.get('name'),
                dose: formData.get('dose'),
                schedule: formData.get('schedule'),
                critical: document.getElementById('criticalSwitch').checked,
                icon: formData.get('icon'),
                shape: 'round',
                color: 'white',
                imprint: ''
            };
            
            fetch('/add_medication', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Medication added successfully!');
                    document.getElementById('addMedicationForm').reset();
                    // Close modal and refresh
                    const modal = bootstrap.Modal.getInstance(document.getElementById('manageMedsModal'));
                    modal.hide();
                    setTimeout(() => location.reload(), 500);
                } else {
                    alert('Failed to add medication. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });
        
        // Delete medication
        document.querySelectorAll('.delete-med').forEach(button => {
            button.addEventListener('click', function() {
                const medName = this.getAttribute('data-med');
                if (confirm(`Are you sure you want to delete ${medName}?`)) {
                    fetch('/delete_medication', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ name: medName })
                    })
                    .then(response => response.json())
                    .then data => {
                        if (data.success) {
                            document.getElementById(`med-${medName}`).remove();
                            // Refresh the page to update the schedule
                            setTimeout(() => location.reload(), 500);
                        }
                    });
                }
            });
        });
        
        // Mark alert as read
        document.querySelectorAll('.mark-read').forEach(button => {
            button.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                fetch(`/mark_alert_read/${index}`)
                    .then(() => window.location.reload());
            });
        });
        
        // Confirm emergency
        document.getElementById('confirmEmergency').addEventListener('click', function() {
            fetch('/trigger_emergency', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert('Emergency assistance requested! Help is on the way.');
                    window.location.reload();
                });
        });

        // Add pulsing animation to emergency button
        const alertButton = document.querySelector('.alert-button');
        setInterval(() => {
            alertButton.style.animation = 'none';
            setTimeout(() => {
                alertButton.style.animation = 'pulse 2s infinite';
            }, 10);
        }, 10000);

        // Initialize
        updateCountdown();
        setInterval(updateCountdown, 1000);
        updateData();
    </script>
</body>
</html>
'''

# History Template
history_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>MediGuardian - Full History</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --teal: #20B2AA;
        }
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
        }
        .history-table th {
            background-color: var(--teal);
            color: white;
        }
        .badge-taken { background-color: #28a745; }
        .badge-missed { background-color: #dc3545; }
        .back-button {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container py-4">
        <a href="/" class="btn btn-primary back-button">
            <i class="fas fa-arrow-left"></i> Back to Dashboard
        </a>
        
        <div class="card">
            <div class="card-header bg-teal text-white">
                <h2><i class="fas fa-history"></i> Medication History</h2>
                <p class="mb-0">Compliance Rate: {{ state.compliance_rate }}% ({{ history|length }} events)</p>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover history-table">
                        <thead>
                            <tr>
                                <th>Date & Time</th>
                                <th>Medication</th>
                                <th>Status</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for event in history %}
                            <tr>
                                <td>{{ event.time }}</td>
                                <td>{{ event.medication }}</td>
                                <td>
                                    {% if event.status == "Taken" %}
                                        <span class="badge badge-taken">Taken</span>
                                    {% else %}
                                        <span class="badge badge-missed">Missed</span>
                                    {% endif %}
                                </td>
                                <td>{{ event.details }}</td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="4" class="text-center text-muted">No history available</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# Create template files
os.makedirs('templates', exist_ok=True)
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)
    
with open('templates/history.html', 'w', encoding='utf-8') as f:
    f.write(history_html)

def generate_dummy_history():
    """Generate dummy history for past two days and today's passed medications"""
    history = []
    now = datetime.now()
    # Create dates for past two days and today
    dates = [
        now - timedelta(days=2),
        now - timedelta(days=1),
        now.date()
    ]
    # Status probabilities (80% taken, 20% missed)
    status_probs = ["Taken"] * 8 + ["Missed"] * 2
    for date in dates:
        for med_name, details in MEDICATION_DB.items():
            for time_str in details["schedule"]:
                # Skip future times for today
                if date == now.date():
                    med_time = datetime.strptime(time_str, "%H:%M").time()
                    if (datetime.combine(now.date(), med_time) > now):
                        continue
                # Create datetime for event
                event_time = datetime.combine(date, datetime.strptime(time_str, "%H:%M").time())
                # Special handling for today's Aspirin at 8am
                if (date == now.date() and med_name == "Aspirin" and time_str == "08:00"):
                    status = "Missed"
                    details_str = "Expected: round white, Scanned: None"
                else:
                    # Random status based on probabilities
                    status = random.choice(status_probs)
                    # Create plausible details
                    if status == "Taken":
                        details_str = f"Expected: {details['shape']} {details['color']}, Scanned: {details['shape']} {details['color']}"
                    else:
                        if random.random() > 0.5:
                            details_str = f"Expected: {details['shape']} {details['color']}, Scanned: None"
                        else:
                            other_med = random.choice([m for m in MEDICATION_DB if m != med_name])
                            other_details = MEDICATION_DB[other_med]
                            details_str = f"Expected: {details['shape']} {details['color']}, Scanned: {other_details['shape']} {other_details['color']}"
                history.append({
                    "medication": med_name,
                    "time": event_time.strftime("%Y-%m-%d %H:%M"),
                    "status": status,
                    "details": details_str
                })
    # Sort history by time (newest first)
    history.sort(key=lambda x: datetime.strptime(x["time"], "%Y-%m-%d %H:%M"), reverse=True)
    return history

# Generate and add dummy history
system_state["compliance_history"] = generate_dummy_history()
system_state["compliance_rate"] = calculate_compliance()

if __name__ == '__main__':
    system_state["next_dose_time"] = datetime.now().replace(hour=13, minute=0, second=0)
    app.run(debug=True)