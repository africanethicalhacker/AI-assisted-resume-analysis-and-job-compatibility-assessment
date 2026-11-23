from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import FloatField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import AnyOf, DataRequired, Email, EqualTo, Length, NumberRange


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password (12+ characters)", validators=[DataRequired(), Length(min=12, max=128)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Log in")


class ResetRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=254)])
    submit = SubmitField("Send reset link")


class ResetForm(FlaskForm):
    password = PasswordField("New password (12+ characters)", validators=[DataRequired(), Length(min=12, max=128)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])
    submit = SubmitField("Set new password")


class UploadForm(FlaskForm):
    file = FileField("Resume (PDF or DOCX)", validators=[FileRequired(), FileAllowed(["pdf", "docx"], "PDF or DOCX only.")])
    submit = SubmitField("Upload securely")


class JobForm(FlaskForm):
    title = StringField("Job title (optional, detected if blank)", validators=[Length(max=200)])
    organization = StringField("Organisation (optional)", validators=[Length(max=200)])
    text = TextAreaField("Paste the job description", validators=[Length(max=20000)])
    file = FileField("...or upload PDF/DOCX", validators=[FileAllowed(["pdf", "docx"], "PDF or DOCX only.")])
    submit = SubmitField("Analyse job description")


class SkillForm(FlaskForm):
    name = StringField("Skill name", validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField("Category", choices=[("cybersecurity", "Cyber security"), ("programming", "Programming"),
                                                ("tools", "Tools and technologies"), ("soft", "Non-technical")])
    aliases = StringField("Aliases (separate with |)", validators=[Length(max=500)])
    submit = SubmitField("Add skill")


class AssessmentForm(FlaskForm):
    resume_id = SelectField("Resume", coerce=int, validators=[DataRequired()])
    job_id = SelectField("Job description", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Run assessment")


class ScoringForm(FlaskForm):
    skills = IntegerField("Technical skills (%)", validators=[NumberRange(0, 100)])
    semantic = IntegerField("Semantic similarity (%)", validators=[NumberRange(0, 100)])
    education = IntegerField("Education (%)", validators=[NumberRange(0, 100)])
    experience = IntegerField("Experience (%)", validators=[NumberRange(0, 100)])
    projects_certs = IntegerField("Projects and certifications (%)", validators=[NumberRange(0, 100)])
    semantic_mode = SelectField("Semantic method", choices=[("sbert", "Sentence-BERT"), ("tfidf", "TF-IDF only"), ("blend", "Blend of both")])
    blend_alpha = FloatField("Blend factor (SBERT share, 0-1)", validators=[NumberRange(0, 1)])
    submit = SubmitField("Save configuration")


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Current password", validators=[DataRequired(), Length(max=128)])
    confirm = StringField("Type DELETE to confirm", validators=[DataRequired(), AnyOf(["DELETE"], "Type DELETE exactly.")])
    submit = SubmitField("Permanently delete my account and data")


class JobPostForm(FlaskForm):
    title = StringField("Job title", validators=[DataRequired(), Length(max=200)])
    organization = StringField("Organisation", validators=[Length(max=200)])
    threshold = IntegerField("Match needed to be eligible (%)", default=60, validators=[NumberRange(0, 100)])
    text = TextAreaField("Job description (paste)", validators=[Length(max=20000)])
    file = FileField("...or upload PDF/DOCX", validators=[FileAllowed(["pdf", "docx"], "PDF or DOCX only.")])
    submit = SubmitField("Post job")


class EligibilityCheckForm(FlaskForm):
    resume_id = SelectField("Use a CV you already uploaded", coerce=int)
    file = FileField("...or upload your CV now (PDF or DOCX)", validators=[FileAllowed(["pdf", "docx"], "PDF or DOCX only.")])
    submit = SubmitField("Check my eligibility")
