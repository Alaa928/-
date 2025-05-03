from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash # For admin auth (simple example)
import os
import boto3 # Import boto3
from botocore.exceptions import NoCredentialsError, ClientError # Import exceptions

from src.models import db
from src.models.research_item import ResearchItem

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# --- Configuration (Replace with more secure method later) ---
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
# IMPORTANT: Generate a strong hash for production! This is just an example.
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASS_HASH", generate_password_hash("password"))
ALLOWED_EXTENSIONS = {"pdf"}

# --- Helper Functions ---
def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin_logged_in():
    return session.get("admin_logged_in")

def get_s3_client():
    """Initializes and returns an S3 client."""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=current_app.config.get("S3_ENDPOINT_URL"),
            aws_access_key_id=current_app.config.get("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=current_app.config.get("S3_SECRET_ACCESS_KEY")
        )
        return s3_client
    except Exception as e:
        current_app.logger.error(f"Failed to create S3 client: {e}")
        return None

# --- Routes ---
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة", "error")
    return render_template("admin_login.html")

@admin_bp.route("/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for("admin.admin_login"))

@admin_bp.route("/dashboard")
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for("admin.admin_login"))
    
    items = ResearchItem.query.order_by(ResearchItem.upload_date.desc()).all()
    return render_template("admin_dashboard.html", items=items)

@admin_bp.route("/upload", methods=["POST"])
def admin_upload():
    if not is_admin_logged_in():
        flash("يرجى تسجيل الدخول أولاً", "error")
        return redirect(url_for("admin.admin_login"))

    if "file" not in request.files:
        flash("لم يتم العثور على جزء الملف", "error")
        return redirect(url_for("admin.admin_dashboard"))
    
    file = request.files["file"]
    if file.filename == "":
        flash("لم يتم تحديد أي ملف", "error")
        return redirect(url_for("admin.admin_dashboard"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Consider adding a unique prefix/timestamp to filename to avoid collisions
        s3_client = get_s3_client()
        s3_bucket = current_app.config.get("S3_BUCKET_NAME")
        s3_endpoint_url = current_app.config.get("S3_ENDPOINT_URL")

        if not s3_client or not s3_bucket or not s3_endpoint_url:
            flash("خطأ في إعدادات التخزين السحابي. يرجى مراجعة الإعدادات.", "error")
            current_app.logger.error("S3 client, bucket, or endpoint URL not configured.")
            return redirect(url_for("admin.admin_dashboard"))

        try:
            # Upload file to S3/R2
            s3_client.upload_fileobj(
                file, 
                s3_bucket, 
                filename,
                ExtraArgs={
                    'ACL': 'public-read', # Make file publicly readable
                    'ContentType': file.content_type
                }
            )
            
            # Construct the public URL (adjust based on your S3/R2 provider)
            # Example for Cloudflare R2 public bucket URL:
            # Assuming R2 public URL is like https://<ACCOUNT_ID>.r2.cloudflarestorage.com/<BUCKET_NAME>/<FILENAME>
            # Or if using a custom domain: https://<CUSTOM_DOMAIN>/<FILENAME>
            # For simplicity, using a common pattern. VERIFY THIS for your specific provider.
            file_url = f"{s3_endpoint_url}/{s3_bucket}/{filename}" 
            # A more robust way for R2 might involve constructing from account ID if no custom domain
            # file_url = f"https://{os.environ.get('CLOUDFLARE_ACCOUNT_ID')}.r2.cloudflarestorage.com/{s3_bucket}/{filename}"

            # Save metadata to database
            new_item = ResearchItem(
                title=request.form.get("title"),
                author=request.form.get("author"),
                item_type=request.form.get("type"),
                subject=request.form.get("subject"),
                abstract=request.form.get("abstract"),
                keywords=request.form.get("keywords"),
                file_path=file_url # Store the public URL
            )
            db.session.add(new_item)
            db.session.commit()
            flash(f"تم رفع الملف {filename} بنجاح وحفظ البيانات", "success")

        except NoCredentialsError:
            flash("خطأ في بيانات اعتماد التخزين السحابي.", "error")
            current_app.logger.error("S3 credentials not found.")
        except ClientError as e:
            flash(f"خطأ في التخزين السحابي: {e.response['Error']['Message']}", "error")
            current_app.logger.error(f"S3 ClientError: {e}")
        except Exception as e:
            db.session.rollback() # Rollback DB changes if S3 upload or commit fails
            flash(f"حدث خطأ غير متوقع: {e}", "error")
            current_app.logger.error(f"Error during upload process: {e}")
            # Note: We don't need to remove a local file anymore

    else:
        flash("نوع الملف غير مسموح به (فقط PDF مسموح)", "error")

    return redirect(url_for("admin.admin_dashboard"))

# Add routes for editing and deleting items later

