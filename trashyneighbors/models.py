import enum
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import BigInteger, Enum, Index, UniqueConstraint

from .extensions import db


class UserRole(str, enum.Enum):
    GUEST = "GUEST"
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    MODERATOR = "MODERATOR"
    ADMINISTRATOR = "ADMINISTRATOR"
    SUPER_ADMINISTRATOR = "SUPER_ADMINISTRATOR"


class User(db.Model, UserMixin):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    screen_name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)

    role = db.Column(Enum(UserRole), nullable=False, default=UserRole.UNVERIFIED)

    email_verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    camera_url = db.Column(db.String(2048), nullable=True)

    def get_id(self):
        return str(self.user_id)


class Post(db.Model):
    __tablename__ = "post"

    post_id = db.Column(db.BigInteger, primary_key=True)
    author_user_id = db.Column(
        db.Integer, db.ForeignKey("user.user_id"), nullable=False, index=True
    )

    title = db.Column(db.String(255), nullable=False)
    story_text = db.Column(db.Text, nullable=False)

    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(128), nullable=False, index=True)
    state = db.Column(db.String(2), nullable=False, index=True)
    zip_code = db.Column(db.String(5), nullable=False, index=True)

    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class PostImage(db.Model):
    __tablename__ = "post_image"

    image_id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(
        db.BigInteger, db.ForeignKey("post.post_id"), nullable=False, index=True
    )

    content_type = db.Column(db.String(64), nullable=False)
    image_bytes = db.Column(db.LargeBinary(length=(16 * 1024 * 1024)), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class PostName(db.Model):
    __tablename__ = "post_name"

    post_name_id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(
        db.BigInteger, db.ForeignKey("post.post_id"), nullable=False, index=True
    )
    name_text = db.Column(db.String(255), nullable=False)


class VoteValue(int, enum.Enum):
    LIKE = 1
    DISLIKE = -1


class PostVote(db.Model):
    __tablename__ = "post_vote"

    post_vote_id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(
        db.BigInteger, db.ForeignKey("post.post_id"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    vote_value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_post_vote_post_user"),
    )


class Comment(db.Model):
    __tablename__ = "comment"

    comment_id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(
        db.BigInteger, db.ForeignKey("post.post_id"), nullable=False, index=True
    )
    author_user_id = db.Column(
        db.Integer, db.ForeignKey("user.user_id"), nullable=False, index=True
    )
    body_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AuditEventType(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER = "REGISTER"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    CREATE_POST = "CREATE_POST"
    CREATE_COMMENT = "CREATE_COMMENT"
    VOTE = "VOTE"


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    audit_log_id = db.Column(db.BigInteger, primary_key=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)

    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)

    entity_type = db.Column(db.String(64), nullable=True)
    entity_id = db.Column(db.String(64), nullable=True)

    event_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ZipCodeLocation(db.Model):
    __tablename__ = "zip_code_location"

    zip_code = db.Column(db.String(5), primary_key=True)
    city = db.Column(db.String(128), primary_key=True)
    state = db.Column(db.String(2), primary_key=True)
    county = db.Column(db.String(128), primary_key=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)


Index("idx_post_score", Post.created_at)
Index("idx_audit_created", AuditLog.created_at)
