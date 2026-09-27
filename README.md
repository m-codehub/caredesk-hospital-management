# CareDesk Hospital Management

A student project built with Flask, SQLite, HTML, and CSS. It demonstrates role-based sign-in and records for patients, doctors, staff, departments, appointments, medical records, prescriptions, billing, beds, and reports.

This is a classroom demo, not a clinical system. Do not enter real patient information or use it for medical decisions.

## Run in VS Code

1. Open this folder in VS Code.
2. Install the dependency once in the selected Python environment: `python -m pip install -r requirements.txt`.
3. Select **Terminal > Run Build Task... > Run Hospital Management**. The app runs at `http://127.0.0.1:5000`.
4. Sign in with one of the demo accounts. Press `Ctrl+C` in the task terminal to stop the server.

You can also start it from the project folder with `python app.py`.

## Demo accounts

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin123` |
| Doctor | `doctor` | `doctor123` |
| Receptionist | `reception` | `reception123` |
| Patient | `patient` | `patient123` |
| Doctor | `doctor2` | `doctor2123` |
| Doctor | `doctor3` | `doctor3123` |
| Patient | `patient2` | `patient2123` |
| Patient | `patient3` | `patient3123` |
| Patient | `patient4` | `patient4123` |

The SQLite database is created at `database/hospital.db` the first time the app starts. A set of fictional sample records is added once to each module, including when upgrading an existing student database. Restarting the app will not duplicate the sample rows. This app is for local learning only; change the secret key and complete a security and privacy review before any real deployment.

## Role permissions

- Admins can add, edit, and remove patients, doctors, staff, departments, beds, and billing records. Prescription records are view-only for admins.
- Receptionists can view doctors and departments but cannot change them.
- Patients can request appointments for themselves and mark their own bills paid in the demo. The payment action does not process money.
- Doctors and patients only see records associated with their account.

Use **Terminal > Run Test Task... > Run Hospital Management Tests** to run the access-control tests.