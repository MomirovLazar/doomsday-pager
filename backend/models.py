from datetime import datetime, timezone
from sqlalchemy import (
    DateTime, 
    ForeignKey, 
    String, 
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="role"
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False
    )

    role: Mapped["Role"] = relationship(
        back_populates="users"
    )

    created_incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="creator",
        foreign_keys="Incident.created_by_id"
    )

    owned_incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="owner",
        foreign_keys="Incident.owner_id"
    )

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="NEW",
        nullable=False
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False  
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_incidents",
        foreign_keys=[created_by_id]
    )

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_incidents",
        foreign_keys=[owner_id]
    )

    responders: Mapped[list["IncidentResponder"]] = relationship(
        back_populates="incident"
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="incident"
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="incident"
    )

class IncidentResponder(Base):
    __tablename__ = "incident_responders"
    __table_args__ = (
        UniqueConstraint(
            "incident_id", 
            "user_id",
            name="uq_incident_responder"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False  
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="responders"
    )

    user: Mapped["User"] = relationship()

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False  
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="comments"
    )

    author: Mapped["User"] = relationship()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False  
    )

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    details: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="audit_logs"
    )

    actor: Mapped["User | None"] = relationship()

class IncidentAcknowledgement(Base):
    __tablename__ = "incident_acknowledgements"

    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "user_id",
            name="uq_incident_acknowledgement"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    incident: Mapped["Incident"] = relationship()
    user: Mapped["User"] = relationship()