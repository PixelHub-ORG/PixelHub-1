from flask import redirect, render_template, request, url_for, session
from flask_login import current_user, login_user, logout_user

from app import oauth
from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()

@auth_bp.route("/signup/", methods=["GET", "POST"], endpoint="show_signup_form")
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        session['setup_2fa_user_id'] = user.id

        return redirect(url_for("auth.enable_2fa"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if current_user.is_authenticated:
        if not current_user.is_two_factor_enabled:
            return redirect(url_for("auth.enable_2fa"))
        return redirect(url_for("public.index"))

    form = LoginForm()
    error = None

    if form.validate_on_submit():
        user = authentication_service.repository.get_by_email(form.email.data)

        if not user or not user.check_password(form.password.data):
            error = "Invalid credentials"
            return render_template("auth/login_form.html", form=form, error=error)

        login_user(user, remember=form.remember_me.data)

        if user.is_two_factor_enabled:
            session['two_factor_user_id'] = user.id
            return redirect(url_for("auth.verify_2fa"))
        else:
            session['setup_2fa_user_id'] = user.id
            return redirect(url_for("auth.enable_2fa"))

    return render_template("auth/login_form.html", form=form, error=error)

@auth_bp.route("/logout", endpoint="logout")
def logout():
    logout_user() 
    session.pop('setup_2fa_user_id', None)
    session.pop('two_factor_user_id', None)
    return redirect(url_for("public.index"))


@auth_bp.route("/2fa/enable", methods=["GET", "POST"], endpoint="enable_2fa")
def enable_2fa():
    user = None
    if current_user.is_authenticated:
        user = current_user
        if user.is_two_factor_enabled:
            return render_template("auth/enabled_2fa.html")
    else:
        user_id = session.get('setup_2fa_user_id')
        if user_id:
            user = authentication_service.repository.get(user_id)
        else:
            return redirect(url_for("auth.login"))

    if not user.two_factor_secret:
        secret = authentication_service.generate_two_factor_secret(user)
        user.two_factor_secret = secret
        authentication_service.repository.session.commit()
    else:
        secret = user.two_factor_secret

    qr_code = authentication_service.generate_qr_code_for_two_factor(user)

    error = None 

    if request.method == "POST":
        code = request.form.get("code")
        if code and authentication_service.verify_two_factor_code(user, code):
            authentication_service.enable_two_factor(user)
            login_user(user) 
            session.pop('setup_2fa_user_id', None)
            return redirect(url_for("public.index"))
        else:
            error = "Invalid code, please try again."

    return render_template("auth/enable_2fa.html", qr_code=qr_code, secret=secret, error=error)

@auth_bp.route("/2fa/verify", methods=["GET", "POST"], endpoint="verify_2fa")
def verify_2fa():
    user_id = session.get('two_factor_user_id')
    if not user_id:
        return redirect(url_for("auth.login"))

    user = authentication_service.repository.get(user_id)
    error = None

    if request.method == "POST":
        code = request.form.get("code")
        if not code:
            error = "Please enter the 2FA code."
        elif authentication_service.verify_two_factor_code(user, code):
            login_user(user) 
            session.pop('two_factor_user_id', None) 
            return redirect(url_for("public.index"))
        else:
            error = "Invalid 2FA code, please try again."

    return render_template("auth/verify_2fa.html", error=error)

@auth_bp.route("/2fa/disable", methods=["POST"], endpoint="disable_2fa")
def disable_2fa():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    authentication_service.disable_two_factor(current_user)
    return redirect(url_for("public.index"))


@auth_bp.route("/orcid/login")
def orcid_login():
    """
    Route to trigger the ORCID login.
    This will redirect the user to the ORCID authorization page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    # Define the callback URL for Authlib
    redirect_uri = url_for("auth.orcid_callback", _external=True)

    # Use the oauth object to authorize the redirect
    return oauth.orcid.authorize_redirect(redirect_uri)


@auth_bp.route("/orcid/callback")
def orcid_callback():
    """
    Callback route that ORCID redirects to after authorization.
    """
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    try:
        # Exchange the authorization code for an access token
        token = oauth.orcid.authorize_access_token()
    except Exception as e:
        # Handle error (e.g., user denied access)
        return render_template("auth/login_form.html", error=f"ORCID login failed: {e}")

    # The token response from ORCID (with /authenticate scope) includes 'orcid' and 'name'
    orcid_id = token.get("orcid")
    full_name = token.get("name")

    if not orcid_id:
        return render_template("auth/login_form.html", error="Could not retrieve ORCID iD.")

    # Find or create a local user account
    try:
        user = authentication_service.find_or_create_by_orcid(orcid_id=orcid_id, full_name=full_name)
    except Exception as e:
        # Handle error during user creation
        return render_template("auth/login_form.html", error=f"Error creating user profile: {e}")

    # Log the user in
    login_user(user, remember=True)

    # Redirect to the main page
    return redirect(url_for("public.index"))
