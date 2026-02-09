# Weight Training Tracker

A Flask-based web application for tracking weight training exercises.

## Features
- Log exercises with weight and reps
- Edit existing entries
- Search by exercise name and date range
- Export data to CSV
- Mobile-friendly interface
- Weekly email reports (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aerospaceguru/weight-training-tracker.git
cd weight-training-tracker
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the app:
```bash
python3 app.py
```

Access at: `http://localhost:5055`

## Running as a Service (Linux)

1. Copy the service file:
```bash
sudo cp weight_training_app.service /etc/systemd/system/
```

2. Update the paths in the service file to match your installation directory

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable weight_training_app.service
sudo systemctl start weight_training_app.service
```

## Weekly Email Setup (Optional)

1. Copy the template:
```bash
cp weekly_email.py.template weekly_email.py
```

2. Get a Gmail App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Create password for "Weight Training Tracker"

3. Edit `weekly_email.py` and add your credentials

4. Set up cron job:
```bash
crontab -e
# Add: 0 20 * * 0 /path/to/venv/bin/python3 /path/to/weekly_email.py
```

## License
MIT
