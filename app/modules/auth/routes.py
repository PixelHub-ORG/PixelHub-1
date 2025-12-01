from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app import oauth
from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
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

        # Log user
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
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
