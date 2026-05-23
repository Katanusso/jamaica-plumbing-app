import os
import csv
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename

from app import db
from app.models import User, Plumber, Service, Booking, Review
from app.forms import (
    RegistrationForm,
    LoginForm,
    ServiceForm,
    EditServiceForm,
    BookingForm,
    ReviewForm,
    SearchForm,
    UpdatePlumberStatusForm,
    ManageServiceRequestForm,
    UpdateStatusForm,
    CSVUploadForm,
)

bp = Blueprint("main", __name__)


def allowed_file(filename):
    allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", {"csv"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_search_form():
    return SearchForm()


def get_current_plumber():
    if not current_user.is_authenticated:
        return None
    return Plumber.query.filter_by(user_id=current_user.id).first()


def get_first_service_id():
    service = Service.query.first()
    return service.id if service else None


@bp.route("/")
@bp.route("/index")
def index():
    form = get_search_form()
    service_id = None

    if current_user.is_authenticated:
        plumber = get_current_plumber()
        if plumber:
            service = Service.query.filter_by(plumber_id=plumber.id).first()
            service_id = service.id if service else get_first_service_id()
        else:
            service_id = get_first_service_id()
    else:
        service_id = get_first_service_id()

    return render_template("index.html", title="Home", form=form, service_id=service_id)


@bp.route("/about")
def about():
    form = get_search_form()
    return render_template("about.html", title="About Us", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash("That username or email is already registered.", "error")
            return redirect(url_for("main.register"))

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        plumber = Plumber(name=form.username.data, user_id=user.id, status="available")
        db.session.add(plumber)
        db.session.commit()

        flash("Registration successful. You can now sign in.")
        return redirect(url_for("main.login"))

    return render_template("register.html", title="Register", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", "error")
            return redirect(url_for("main.login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        return redirect(next_page) if next_page else redirect(url_for("main.index"))

    return render_template("login.html", title="Sign In", login_form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@bp.route("/profile")
@login_required
def profile():
    form = get_search_form()
    plumber = get_current_plumber()

    if plumber is None:
        flash("Plumber profile not found. Please contact support.", "error")
        return render_template("profile.html", title="Profile", form=form)

    return render_template("profile.html", title="Profile", form=form, plumber=plumber)


@bp.route("/add_service", methods=["GET", "POST"])
@login_required
def add_service():
    form = get_search_form()
    service_form = ServiceForm()
    csv_form = CSVUploadForm()
    plumber = get_current_plumber()

    if plumber is None:
        flash("Plumber profile not found. Please contact support.", "error")
        return redirect(url_for("main.profile"))

    if service_form.validate_on_submit():
        service = Service(
            name=service_form.name.data.strip(),
            min_price=service_form.min_price.data,
            max_price=service_form.max_price.data,
            plumber_id=plumber.id,
        )
        db.session.add(service)

        try:
            db.session.commit()
            flash("Service has been added.")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding service: {e}", "error")

        return redirect(url_for("main.view_services"))

    if csv_form.validate_on_submit():
        return process_csv_upload(csv_form, plumber, redirect_endpoint="main.add_service")

    return render_template(
        "add_service.html",
        title="Add Service",
        form=form,
        service_form=service_form,
        csv_form=csv_form,
    )


@bp.route("/upload_csv", methods=["GET", "POST"])
@login_required
def upload_csv():
    form = CSVUploadForm()
    plumber = get_current_plumber()

    if plumber is None:
        flash("Plumber profile not found. Please contact support.", "error")
        return redirect(url_for("main.profile"))

    if form.validate_on_submit():
        return process_csv_upload(form, plumber, redirect_endpoint="main.upload_csv")

    return render_template("upload_csv.html", title="Upload CSV", form=form)


def process_csv_upload(form, plumber, redirect_endpoint):
    file = form.file.data

    if not file or not allowed_file(file.filename):
        flash("Please upload a valid CSV file.", "error")
        return redirect(url_for(redirect_endpoint))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    required_columns = {"Description", "Minimum Price", "Maximum Price"}
    services_processed = 0
    services_created = 0
    services_updated = 0

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)

            if reader.fieldnames is None:
                flash("The CSV file appears to be empty.", "error")
                return redirect(url_for(redirect_endpoint))

            reader.fieldnames = [field.strip() for field in reader.fieldnames]
            missing_columns = required_columns - set(reader.fieldnames)

            if missing_columns:
                flash(f'Missing required columns in CSV: {", ".join(missing_columns)}', "error")
                return redirect(url_for(redirect_endpoint))

            for row in reader:
                description = row.get("Description", "").strip()

                if not description:
                    continue

                try:
                    min_price = float(row["Minimum Price"])
                    max_price = float(row["Maximum Price"])
                except ValueError:
                    flash(f"Invalid price format for service: {description}", "error")
                    return redirect(url_for(redirect_endpoint))

                service = Service.query.filter_by(
                    name=description,
                    plumber_id=plumber.id,
                ).first()

                if service:
                    service.min_price = min_price
                    service.max_price = max_price
                    services_updated += 1
                else:
                    service = Service(
                        name=description,
                        min_price=min_price,
                        max_price=max_price,
                        plumber_id=plumber.id,
                    )
                    db.session.add(service)
                    services_created += 1

                services_processed += 1

        db.session.commit()
        flash(
            f"CSV upload complete. {services_processed} services processed, "
            f"{services_created} created, {services_updated} updated."
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error processing CSV file: {e}", "error")
        return redirect(url_for(redirect_endpoint))

    return redirect(url_for("main.view_services"))


@bp.route("/view_services")
@login_required
def view_services():
    form = get_search_form()
    plumber = get_current_plumber()

    if plumber is None:
        flash("Plumber profile not found. Please contact support.", "error")
        return redirect(url_for("main.profile"))

    services = Service.query.filter_by(plumber_id=plumber.id).order_by(Service.name.asc()).all()

    return render_template(
        "view_services.html",
        title="View Services",
        form=form,
        services=services,
    )


@bp.route("/all_services")
def all_services():
    services = Service.query.order_by(Service.name.asc()).all()
    return render_template("all_services.html", title="All Services", services=services)


@bp.route("/edit_service/<int:service_id>", methods=["GET", "POST"])
@login_required
def edit_service(service_id):
    plumber = get_current_plumber()
    service = Service.query.get_or_404(service_id)

    if plumber is None or service.plumber_id != plumber.id:
        flash("You are not authorized to edit this service.", "error")
        return redirect(url_for("main.view_services"))

    form = EditServiceForm(obj=service)

    if form.validate_on_submit():
        service.name = form.name.data.strip()
        service.min_price = form.min_price.data
        service.max_price = form.max_price.data
        db.session.commit()
        flash("Service has been updated.")
        return redirect(url_for("main.view_services"))

    return render_template("edit_service.html", title="Edit Service", form=form, service=service)


@bp.route("/delete_service/<int:service_id>", methods=["POST"])
@login_required
def delete_service(service_id):
    plumber = get_current_plumber()
    service = Service.query.get_or_404(service_id)

    if plumber is None or service.plumber_id != plumber.id:
        flash("You are not authorized to delete this service.", "error")
        return redirect(url_for("main.view_services"))

    db.session.delete(service)
    db.session.commit()
    flash("Service has been deleted.")

    return redirect(url_for("main.view_services"))


@bp.route("/book_service/<int:service_id>", methods=["GET", "POST"])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    form = BookingForm()
    form.service.choices = [(service.id, service.name)]
    form.service.data = service.id

    if form.validate_on_submit():
        booking = Booking(
            service_id=service.id,
            plumber_id=service.plumber_id,
            user_id=current_user.id,
            date=form.date.data,
            status="pending",
        )
        db.session.add(booking)

        try:
            db.session.commit()
            flash("Service has been booked.")
            return redirect(url_for("main.view_bookings"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error booking service: {e}", "error")

    return render_template(
        "book_service.html",
        title="Book Service",
        form=form,
        service=service,
        service_id=service.id,
    )


@bp.route("/view_bookings")
@login_required
def view_bookings():
    form = get_search_form()
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date.desc()).all()

    return render_template(
        "view_bookings.html",
        title="View Bookings",
        form=form,
        bookings=bookings,
    )


@bp.route("/leave_review/<int:service_id>", methods=["GET", "POST"])
@login_required
def leave_review(service_id):
    service = Service.query.get_or_404(service_id)
    form = ReviewForm()

    if form.validate_on_submit():
        review = Review(
            plumber_id=service.plumber_id,
            user_id=current_user.id,
            rating=form.rating.data,
            body=form.body.data,
        )
        db.session.add(review)

        try:
            db.session.commit()
            flash("Review has been submitted.")
            return redirect(url_for("main.view_services"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting review: {e}", "error")

    return render_template("leave_review.html", title="Leave Review", form=form, service=service)


@bp.route("/update_plumber_status", methods=["GET", "POST"])
@login_required
def update_plumber_status():
    form = UpdatePlumberStatusForm()
    plumber = get_current_plumber()

    if plumber is None:
        flash("Plumber profile not found. Please contact support.", "error")
        return redirect(url_for("main.profile"))

    if form.validate_on_submit():
        plumber.status = form.status.data
        db.session.commit()
        flash("Plumber status has been updated.")
        return redirect(url_for("main.profile"))

    return render_template("update_plumber_status.html", title="Update Plumber Status", form=form)


@bp.route("/manage_service_requests", methods=["GET", "POST"])
@login_required
def manage_service_requests():
    form = ManageServiceRequestForm()
    if form.validate_on_submit():
        flash("Service requests have been managed.")
    return render_template("manage_service_requests.html", title="Manage Service Requests", form=form)


@bp.route("/update_status/<int:service_id>", methods=["POST"])
@login_required
def update_status(service_id):
    flash("Service-level status updates are not part of the demo flow yet.")
    return redirect(url_for("main.view_services"))


@bp.route("/api/plumbers")
def api_plumbers():
    plumbers = Plumber.query.filter(
        Plumber.latitude.isnot(None),
        Plumber.longitude.isnot(None),
    ).all()

    return jsonify([
        {
            "id": plumber.id,
            "name": plumber.name,
            "status": plumber.status,
            "latitude": plumber.latitude,
            "longitude": plumber.longitude,
        }
        for plumber in plumbers
    ])


@bp.route("/map")
@login_required
def map_view():
    form = get_search_form()
    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY")
    return render_template(
        "map.html",
        title="Map",
        form=form,
        google_maps_api_key=google_maps_api_key,
    )
