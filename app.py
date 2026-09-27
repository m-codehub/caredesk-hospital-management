import hmac
import os
import secrets
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import DEFAULT_DB_PATH, connect, initialize_database


MODULES = {
    "patients": {
        "title": "Patients", "table": "patients", "roles": {"admin", "doctor", "receptionist"},
        "columns": {"name": "Patient", "age": "Age", "gender": "Gender", "phone": "Phone", "department_id": "Department"},
        "fields": [
            ("name", "Patient name", "text"), ("age", "Age", "number"),
            ("gender", "Gender", "select:Female,Male,Other"), ("phone", "Phone", "tel"),
            ("department_id", "Department", "ref:departments"),
        ],
    },
    "doctors": {
        "title": "Doctors", "table": "doctors", "roles": {"admin", "receptionist"},
        "columns": {"name": "Doctor", "specialty": "Specialty", "phone": "Phone", "department_id": "Department"},
        "fields": [("name", "Doctor name", "text"), ("specialty", "Specialty", "text"), ("phone", "Phone", "tel"), ("department_id", "Department", "ref:departments")],
    },
    "departments": {
        "title": "Departments", "table": "departments", "roles": {"admin", "receptionist"},
        "columns": {"name": "Department", "location": "Location"},
        "fields": [("name", "Department name", "text"), ("location", "Location", "text")],
    },
    "staff": {
        "title": "Staff", "table": "staff", "roles": {"admin"},
        "columns": {"name": "Name", "role": "Role", "phone": "Phone"},
        "fields": [("name", "Staff name", "text"), ("role", "Role", "select:Receptionist,Nurse,Technician,Administrator"), ("phone", "Phone", "tel")],
    },
    "appointments": {
        "title": "Appointments", "table": "appointments", "roles": {"admin", "doctor", "receptionist", "patient"},
        "columns": {"patient_id": "Patient", "doctor_id": "Doctor", "visit_date": "Date", "visit_time": "Time", "reason": "Reason", "status": "Status"},
        "fields": [("patient_id", "Patient", "ref:patients"), ("doctor_id", "Doctor", "ref:doctors"), ("visit_date", "Date", "date"), ("visit_time", "Time", "time"), ("reason", "Reason", "text"), ("status", "Status", "select:Scheduled,Checked in,Completed,Cancelled")],
    },
    "medical_records": {
        "title": "Medical records", "table": "medical_records", "roles": {"admin", "doctor", "patient"},
        "columns": {"patient_id": "Patient", "doctor_id": "Doctor", "record_date": "Date", "diagnosis": "Diagnosis", "notes": "Notes"},
        "fields": [("patient_id", "Patient", "ref:patients"), ("doctor_id", "Doctor", "ref:doctors"), ("record_date", "Date", "date"), ("diagnosis", "Diagnosis", "text"), ("notes", "Notes", "text")],
    },
    "prescriptions": {
        "title": "Prescriptions", "table": "prescriptions", "roles": {"admin", "doctor", "patient"},
        "columns": {"patient_id": "Patient", "doctor_id": "Doctor", "medication": "Medication", "dosage": "Dosage", "instructions": "Instructions", "prescribed_date": "Date"},
        "fields": [("patient_id", "Patient", "ref:patients"), ("doctor_id", "Doctor", "ref:doctors"), ("medication", "Medication", "text"), ("dosage", "Dosage", "text"), ("instructions", "Instructions", "text"), ("prescribed_date", "Date", "date")],
    },
    "billing": {
        "title": "Billing", "table": "bills", "roles": {"admin", "receptionist", "patient"},
        "columns": {"patient_id": "Patient", "amount": "Amount", "due_date": "Due date", "status": "Status"},
        "fields": [("patient_id", "Patient", "ref:patients"), ("amount", "Amount", "number"), ("due_date", "Due date", "date"), ("status", "Status", "select:Pending,Paid,Overdue")],
    },
    "beds": {
        "title": "Beds", "table": "beds", "roles": {"admin", "receptionist"},
        "columns": {"bed_number": "Bed", "ward": "Ward", "status": "Status", "patient_id": "Patient"},
        "fields": [("bed_number", "Bed number", "text"), ("ward", "Ward", "text"), ("status", "Status", "select:Available,Occupied,Maintenance"), ("patient_id", "Patient", "ref:patients")],
    },
}

NAVIGATION = {
    "admin": ["patients", "doctors", "staff", "departments", "appointments", "medical_records", "prescriptions", "billing", "beds"],
    "doctor": ["appointments", "patients", "medical_records", "prescriptions"],
    "receptionist": ["patients", "doctors", "departments", "appointments", "billing", "beds"],
    "patient": ["appointments", "medical_records", "prescriptions", "billing"],
}

EDIT_ROLES = {
    "patients": {"admin", "receptionist"},
    "doctors": {"admin"},
    "staff": {"admin"},
    "departments": {"admin"},
    "appointments": {"admin", "doctor", "receptionist"},
    "medical_records": {"admin", "doctor"},
    "prescriptions": {"doctor"},
    "billing": {"admin", "receptionist"},
    "beds": {"admin", "receptionist"},
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-student-demo-change-before-deploy"),
        DATABASE=str(DEFAULT_DB_PATH),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    initialize_database(app.config["DATABASE"])

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id:
            with connect(app.config["DATABASE"]) as connection:
                g.user = connection.execute(
                    "SELECT id, username, role, patient_id, doctor_id FROM users WHERE id = ?", (user_id,)
                ).fetchone()
            if g.user is None:
                session.clear()

    @app.context_processor
    def inject_template_data():
        return {
            "navigation": NAVIGATION,
            "module_titles": {key: config["title"] for key, config in MODULES.items()},
            "csrf_token": csrf_token,
        }

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    def valid_csrf():
        submitted = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        return bool(submitted and expected and hmac.compare_digest(submitted, expected))

    def role_scope(module_key):
        if g.user["role"] == "patient":
            if module_key == "patients":
                return " WHERE id = ?", (g.user["patient_id"],)
            if "patient_id" in MODULES[module_key]["columns"]:
                return " WHERE patient_id = ?", (g.user["patient_id"],)
            return " WHERE 1 = 0", ()
        if g.user["role"] == "doctor":
            if module_key == "patients":
                return " WHERE id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?)", (g.user["doctor_id"],)
            if "doctor_id" in MODULES[module_key]["columns"]:
                return " WHERE doctor_id = ?", (g.user["doctor_id"],)
            return " WHERE 1 = 0", ()
        return "", ()

    def can_edit_module(module_key):
        return g.user["role"] in EDIT_ROLES.get(module_key, set())

    def validated_fields(module_key, payload, patient_booking=False):
        config = MODULES[module_key]
        names = []
        values = []
        for field, _label, kind in config["fields"]:
            if patient_booking and field in {"patient_id", "status"}:
                continue
            if g.user["role"] == "doctor" and field == "doctor_id":
                continue
            value = payload.get(field, "").strip()
            if not value:
                if module_key == "beds" and field == "patient_id":
                    names.append(field)
                    values.append(None)
                    continue
                raise ValueError("Complete every field before saving.")
            if kind == "number":
                value = float(value) if module_key == "billing" else int(value)
            if kind.startswith("select:") and value not in kind.split(":", 1)[1].split(","):
                raise ValueError("Choose a valid option.")
            if kind.startswith("ref:"):
                reference = kind.split(":", 1)[1]
                reference_sql = f"SELECT id FROM {reference} WHERE id = ?"
                reference_params = [value]
                if g.user["role"] == "doctor" and reference == "patients":
                    reference_sql += " AND id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?)"
                    reference_params.append(g.user["doctor_id"])
                with connect(app.config["DATABASE"]) as connection:
                    row = connection.execute(reference_sql, reference_params).fetchone()
                if not row:
                    raise ValueError("Choose a valid linked record.")
                value = int(value)
            names.append(field)
            values.append(value)
        if patient_booking:
            names.extend(["patient_id", "status"])
            values.extend([g.user["patient_id"], "Scheduled"])
        if g.user["role"] == "doctor" and "doctor_id" in config["columns"]:
            names.append("doctor_id")
            values.append(g.user["doctor_id"])
        return names, values

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            if not valid_csrf():
                abort(400, "The form expired. Refresh and try again.")
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            with connect(app.config["DATABASE"]) as connection:
                user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("dashboard"))
            flash("Username or password is incorrect.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        if not valid_csrf():
            abort(400, "The form expired. Refresh and try again.")
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        with connect(app.config["DATABASE"]) as connection:
            counts = {
                "patients": connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
                "doctors": connection.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
                "appointments": connection.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
                "departments": connection.execute("SELECT COUNT(*) FROM departments").fetchone()[0],
                "beds_available": connection.execute("SELECT COUNT(*) FROM beds WHERE status = 'Available'").fetchone()[0],
            }
            if g.user["role"] == "patient":
                counts["patients"] = 1
                counts["appointments"] = connection.execute(
                    "SELECT COUNT(*) FROM appointments WHERE patient_id = ?", (g.user["patient_id"],)
                ).fetchone()[0]
            elif g.user["role"] == "doctor":
                counts["patients"] = connection.execute(
                    "SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id = ?",
                    (g.user["doctor_id"],),
                ).fetchone()[0]
                counts["appointments"] = connection.execute(
                    "SELECT COUNT(*) FROM appointments WHERE doctor_id = ?", (g.user["doctor_id"],)
                ).fetchone()[0]
            sql = "SELECT a.visit_date, a.visit_time, a.reason, a.status, p.name AS patient, d.name AS doctor " \
                  "FROM appointments a JOIN patients p ON p.id = a.patient_id " \
                  "JOIN doctors d ON d.id = a.doctor_id WHERE a.visit_date >= date('now') " \
                  "ORDER BY a.visit_date, a.visit_time LIMIT 8"
            params = ()
            if g.user["role"] == "patient":
                sql = sql.replace("WHERE a.visit_date", "WHERE a.patient_id = ? AND a.visit_date")
                params = (g.user["patient_id"],)
            elif g.user["role"] == "doctor":
                sql = sql.replace("WHERE a.visit_date", "WHERE a.doctor_id = ? AND a.visit_date")
                params = (g.user["doctor_id"],)
            appointments = connection.execute(sql, params).fetchall()
        return render_template(f"{g.user['role']}/dashboard.html", counts=counts, appointments=appointments)

    @app.route("/module/<module_key>", methods=["GET", "POST"])
    @login_required
    def module(module_key):
        config = MODULES.get(module_key)
        if config is None:
            abort(404)
        if g.user["role"] not in config["roles"]:
            abort(403)

        if request.method == "POST":
            patient_booking = g.user["role"] == "patient" and module_key == "appointments"
            if not can_edit_module(module_key) and not patient_booking:
                abort(403)
            if not valid_csrf():
                abort(400, "The form expired. Refresh and try again.")
            try:
                names, values = validated_fields(module_key, request.form, patient_booking)
                placeholders = ", ".join("?" for _ in names)
                columns = ", ".join(names)
                with connect(app.config["DATABASE"]) as connection:
                    connection.execute(
                        f"INSERT INTO {config['table']} ({columns}) VALUES ({placeholders})", values
                    )
                flash(f"{config['title']} record added.", "success")
                return redirect(url_for("module", module_key=module_key))
            except (ValueError, sqlite3.IntegrityError) as error:
                flash(str(error) or "That record could not be saved.", "error")

        where, params = role_scope(module_key)
        select = ", ".join(config["columns"])
        with connect(app.config["DATABASE"]) as connection:
            rows = connection.execute(
                f"SELECT id, {select} FROM {config['table']}{where} ORDER BY id DESC LIMIT 200", params
            ).fetchall()
            rows = [dict(row) for row in rows]
            reference_options = {}
            for field, _label, kind in config["fields"]:
                if kind.startswith("ref:"):
                    reference = kind.split(":", 1)[1]
                    option_where = ""
                    option_params = ()
                    if g.user["role"] == "doctor" and reference == "patients":
                        option_where = " WHERE id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?)"
                        option_params = (g.user["doctor_id"],)
                    reference_options[field] = connection.execute(
                        f"SELECT id, name FROM {reference}{option_where} ORDER BY name", option_params
                    ).fetchall()
            for field in config["columns"]:
                if field.endswith("_id"):
                    reference = field[:-3]
                    options = reference_options.get(field, [])
                    if reference == "department" and not options:
                        options = connection.execute("SELECT id, name FROM departments").fetchall()
                    name_by_id = {str(option["id"]): option["name"] for option in options}
                    if not name_by_id and reference in ("patients", "doctors"):
                        name_by_id = {
                            str(option["id"]): option["name"]
                            for option in connection.execute(f"SELECT id, name FROM {reference}")
                        }
                    for row in rows:
                        if field in row.keys():
                            row[field] = name_by_id.get(str(row[field]), "")

        can_edit = can_edit_module(module_key)
        can_book = g.user["role"] == "patient" and module_key == "appointments"
        can_pay = g.user["role"] == "patient" and module_key == "billing"
        return render_template("module.html", config=config, module_key=module_key,
                               rows=rows, reference_options=reference_options, can_edit=can_edit,
                               can_book=can_book, can_pay=can_pay)

    @app.route("/module/<module_key>/<int:record_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_record(module_key, record_id):
        config = MODULES.get(module_key)
        if config is None:
            abort(404)
        if not can_edit_module(module_key):
            abort(403)
        scope, scope_params = role_scope(module_key)
        where = "id = ?"
        params = [record_id]
        if scope:
            where += " AND " + scope.removeprefix(" WHERE ")
            params.extend(scope_params)
        with connect(app.config["DATABASE"]) as connection:
            record = connection.execute(
                f"SELECT * FROM {config['table']} WHERE {where}", params
            ).fetchone()
        if record is None:
            abort(404)

        if request.method == "POST":
            if not valid_csrf():
                abort(400, "The form expired. Refresh and try again.")
            try:
                names, values = validated_fields(module_key, request.form)
                assignments = ", ".join(f"{name} = ?" for name in names)
                values.append(record_id)
                with connect(app.config["DATABASE"]) as connection:
                    connection.execute(
                        f"UPDATE {config['table']} SET {assignments} WHERE id = ?", values
                    )
                flash(f"{config['title']} record updated.", "success")
                return redirect(url_for("module", module_key=module_key))
            except (ValueError, sqlite3.IntegrityError) as error:
                flash(str(error) or "That record could not be updated.", "error")

        reference_options = {}
        with connect(app.config["DATABASE"]) as connection:
            for field, _label, kind in config["fields"]:
                if kind.startswith("ref:"):
                    reference = kind.split(":", 1)[1]
                    option_where = ""
                    option_params = ()
                    if g.user["role"] == "doctor" and reference == "patients":
                        option_where = " WHERE id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?)"
                        option_params = (g.user["doctor_id"],)
                    reference_options[field] = connection.execute(
                        f"SELECT id, name FROM {reference}{option_where} ORDER BY name", option_params
                    ).fetchall()
        return render_template("edit_record.html", config=config, module_key=module_key,
                               record=record, reference_options=reference_options)

    @app.post("/module/<module_key>/<int:record_id>/delete")
    @login_required
    def delete_record(module_key, record_id):
        config = MODULES.get(module_key)
        if config is None:
            abort(404)
        if not can_edit_module(module_key):
            abort(403)
        if not valid_csrf():
            abort(400, "The form expired. Refresh and try again.")
        where = "id = ?"
        params = [record_id]
        if g.user["role"] == "doctor" and "doctor_id" in config["columns"]:
            where += " AND doctor_id = ?"
            params.append(g.user["doctor_id"])
        if g.user["role"] == "doctor" and module_key == "patients":
            abort(403)
        try:
            with connect(app.config["DATABASE"]) as connection:
                cursor = connection.execute(f"DELETE FROM {config['table']} WHERE {where}", params)
                if not cursor.rowcount:
                    abort(404)
        except sqlite3.IntegrityError:
            flash("This record is linked to other records and cannot be removed.", "error")
            return redirect(url_for("module", module_key=module_key))
        flash("Record removed.", "success")
        return redirect(url_for("module", module_key=module_key))

    @app.post("/module/billing/<int:record_id>/pay")
    @login_required
    def pay_bill(record_id):
        if g.user["role"] != "patient":
            abort(403)
        if not valid_csrf():
            abort(400, "The form expired. Refresh and try again.")
        with connect(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                "UPDATE bills SET status = 'Paid' WHERE id = ? AND patient_id = ? AND status != 'Paid'",
                (record_id, g.user["patient_id"]),
            )
            if not cursor.rowcount:
                abort(404)
        flash("Demo payment recorded. No real payment was processed.", "success")
        return redirect(url_for("module", module_key="billing"))

    @app.get("/reports")
    @login_required
    def reports():
        if g.user["role"] not in {"admin", "doctor"}:
            abort(403)
        with connect(app.config["DATABASE"]) as connection:
            if g.user["role"] == "doctor":
                rows = connection.execute(
                    "SELECT d.name AS department, COUNT(DISTINCT p.id) AS patients "
                    "FROM departments d LEFT JOIN patients p ON p.department_id = d.id "
                    "AND p.id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?) "
                    "GROUP BY d.id ORDER BY d.name", (g.user["doctor_id"],)
                ).fetchall()
                bill_total = None
            else:
                rows = connection.execute(
                    "SELECT d.name AS department, COUNT(p.id) AS patients "
                    "FROM departments d LEFT JOIN patients p ON p.department_id = d.id "
                    "GROUP BY d.id ORDER BY d.name"
                ).fetchall()
                bill_total = connection.execute("SELECT COALESCE(SUM(amount), 0) FROM bills").fetchone()[0]
        return render_template("reports.html", department_rows=rows, bill_total=bill_total)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)