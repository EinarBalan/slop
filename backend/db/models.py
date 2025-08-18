from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    served = relationship("ServedPost", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    post_id = Column(String(64), unique=True, nullable=True)
    title = Column(Text, nullable=False)
    self_text = Column(Text, nullable=False)
    subreddit = Column(String(128), nullable=True)
    over_18 = Column(Boolean, default=False, nullable=False)
    link_flair_text = Column(String(128), nullable=True)
    is_ai = Column(Boolean, default=False, nullable=False)
    random_key = Column(BigInteger, index=True, nullable=False)

    interactions = relationship("Interaction", back_populates="post", cascade="all, delete-orphan")
    served = relationship("ServedPost", back_populates="post", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    action = Column(String(16), nullable=False)  # like, dislike, next
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="interactions")
    post = relationship("Post", back_populates="interactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', 'action', name='uq_user_post_action'),
    )


class ServedPost(Base):
    __tablename__ = 'served_posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    served_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="served")
    post = relationship("Post", back_populates="served")

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_user_post_served'),
    )


class AiGeneratedPost(Base):
    __tablename__ = 'ai_generated_posts'
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    self_text = Column(Text, nullable=False)
    subreddit = Column(String(128), nullable=True)
    model_name = Column(String(128), nullable=True)
    prompt = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


