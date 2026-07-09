from sqlalchemy import DateTime, ForeignKey, Column, Table, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from enum import Enum
from typing import Optional
from decimal import Decimal


class UserRole(str, Enum):
    USER = 'user'
    ADMIN = 'admin'

class Status(str, Enum):
    OFFLINE = 'offline'
    LIVE = 'live'
    ENDED = 'ended'


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.UTC), 
        index=True
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC)
    )


class User(Base):
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(nullable=False)

    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    avatar_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    streams: Mapped[list["Stream"]] = relationship(
        back_populates='streamer'
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates='sender'
    )

    clips: Mapped[list["Clip"]] = relationship(
        back_populates='creator'
    )

    followers: Mapped[list["User"]] = relationship(
        "User",
        secondary="followers",
        primaryjoin="User.id == Follower.streamer_id",
        secondaryjoin="User.id == Follower.follower_id",
        back_populates="following"
    )

    following: Mapped[list["User"]] = relationship(
        "User",
        secondary="followers",
        primaryjoin="User.id == Follower.follower_id",
        secondaryjoin="User.id == Follower.streamer_id",
        back_populates="followers"
    )

    messages: Mapped[list["StreamMessage"]] = relationship(
        back_populates="sender"
    )


stream_categories = Table(
    "stream_categories",
    Base.metadata,
    Column("stream_id", UUID(as_uuid=True), ForeignKey("streams.id")),
    Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id"))
)


class Category(Base):
    __tablename__ = "categories"

    title: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)

    streams: Mapped[list["Stream"]] = relationship(
        secondary=stream_categories,
        back_populates="categories"
    )


class Stream(Base):
    __tablename__ = "streams"

    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]]
    thumbnail_url: Mapped[Optional[str]]
    stream_key: Mapped[str] = mapped_column(unique=True, nullable=False)

    status: Mapped[Status] = mapped_column(default=Status.OFFLINE)

    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    categories: Mapped[list["Category"]] = relationship(
        secondary=stream_categories,
        back_populates="streams"
    )


    streamer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    streamer: Mapped["User"] = relationship(
        back_populates="streams"
    )

    clips: Mapped[list["Clip"]] = relationship(
        back_populates="stream"
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates="stream"
    )

    metrics: Mapped[Optional["StreamMetric"]] = relationship(
        back_populates="stream",
        uselist=False
    )

    messages: Mapped[list["StreamMessage"]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan"
    )


class Clip(Base):
    __tablename__ = 'clips'

    stream_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('streams.id'), index=True)
    video_url: Mapped[str] = mapped_column(nullable=False) 
    start_sec: Mapped[float] = mapped_column(nullable=False) 
    end_sec: Mapped[float] = mapped_column(nullable=False)

    stream: Mapped["Stream"] = relationship(back_populates="clips")

    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True)

    creator: Mapped["User"] = relationship(
        back_populates='clips'
    )


class Donation(Base):
    __tablename__ = 'donations'

    stream_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('streams.id'), index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True)

    stream: Mapped["Stream"] = relationship(
        back_populates="donations"
    )

    sender: Mapped["User"] = relationship(
        back_populates="donations"
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    message: Mapped[Optional[str]]


class StreamMetric(Base):
    __tablename__ = 'stream_metrics'

    stream_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('streams.id'), index=True, unique=True)

    stream: Mapped["Stream"] = relationship(
        back_populates="metrics"
    )
    
    total_views: Mapped[int] = mapped_column(default=0)
    total_messages: Mapped[int] = mapped_column(default=0)
    total_donations: Mapped[int] = mapped_column(default=0)
    donation_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    peak_viewers: Mapped[int] = mapped_column(default=0)
    avg_watch_time: Mapped[int] = mapped_column(default=0)


class Follower(Base):
    __tablename__ = 'followers'

    __table_args__ = (
        UniqueConstraint("streamer_id", "follower_id"),
    )

    streamer_id: Mapped[uuid.UUID]  = mapped_column(ForeignKey('users.id'), index=True)
    follower_id: Mapped[uuid.UUID]  = mapped_column(ForeignKey('users.id'), index=True)

    streamer: Mapped["User"] = relationship(
        foreign_keys=[streamer_id]
    )

    follower: Mapped["User"] = relationship(
        foreign_keys=[follower_id]                  
    )

    followed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC)
    )


class StreamMessage(Base):
    __tablename__ = 'stream_messages'

    stream_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('streams.id'), index=True)

    stream: Mapped["Stream"] = relationship(
        back_populates="messages"
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True)

    sender: Mapped["User"] = relationship(
        back_populates="messages"
    )

    content: Mapped[str] = mapped_column(nullable=False)