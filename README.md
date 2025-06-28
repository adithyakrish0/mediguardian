MediGuardian - Smart Medication Management System
![MediGuardian Dashboard](https://github.com/user-attachments/assets/a7db0758-13f6-40bd-a4f1-3e5c7b0a4bab)
# MediGuardian - Smart Medication Management System

![MediGuardian Dashboard](https://github.com/adithyakrish0/mediguardian/blob/main/screenshots/dashboard.png?raw=true)

MediGuardian is an intelligent medication management system designed to help patients adhere to their medication schedules while providing caregivers with real-time monitoring and emergency alerts. This Flask-based application simulates pill recognition, tracks compliance, and sends alerts for missed doses or emergencies.

## Key Features

- **Smart Pill Verification**: Simulated camera-based pill identification
- **Automated Scheduling**: Medication reminders based on custom schedules
- **Multi-level Alert System**: 
  - 🔔 Family notifications for missed doses
  - ⚠️ Caregiver alerts for critical misses
  - 🚨 Emergency assistance with location sharing
- **Compliance Tracking**: Visual compliance rate and historical data
- **Emergency Button**: One-touch emergency assistance request
- **Medication Management**: Add, edit, or remove medications
- **Responsive Dashboard**: Mobile-friendly interface

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Database**: JSON file storage
- **Simulation**: Random pill verification algorithm
- **Background Processing**: Python threading

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adithyakrish0/mediguardian.git
   cd mediguardian
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate    # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the dashboard at:
   ```
   http://localhost:5000
   ```

## Usage

### Dashboard
- View upcoming medications
- Monitor compliance rate
- Check system status
- See recent alerts

### Medication Management
1. Click "Manage Medications" button
2. Add new medications with:
   - Name and dosage
   - Schedule times (comma-separated)
   - Critical status
   - Custom icon
3. Delete medications as needed

### Emergency Assistance
- Click the red emergency button
- Confirm emergency request
- System will notify all emergency contacts

### History
- View full medication history
- Filter by date and medication
- Analyze compliance patterns


## System Architecture

```
mediguardian/
├── app.py                 # Main application
├── medications.json       # Medication database
├── requirements.txt       # Dependencies
├── templates/
│   ├── dashboard.html     # Main dashboard template
│   └── history.html       # Medication history template
├── screenshots/           # Application screenshots
└── README.md              # Documentation
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## Future Enhancements

- Integrate with actual pill recognition APIs
- Add user authentication system
- Implement SMS/email notifications
- Create mobile app version
- Add voice assistance
- Integrate with smart dispensers

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**MediGuardian** - Never miss a dose again. Your health, our priority.
