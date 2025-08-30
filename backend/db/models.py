from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_experiment = Column(String(128), nullable=True)
    aware_of_experiment = Column(Boolean, default=True, nullable=False)

    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    served = relationship("ServedPost", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
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
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=True)
    humor_id = Column(Integer, ForeignKey('humorposts.id', ondelete='CASCADE'), nullable=True)
    ai_id = Column(Integer, ForeignKey('ai_generated_posts.id', ondelete='CASCADE'), nullable=True)
    action = Column(String(16), nullable=False)  # like, dislike, next
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="interactions")
    post = relationship("Post", back_populates="interactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', 'humor_id', 'ai_id', 'action', name='uq_user_target_action'),
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


class Experiment(Base):
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True)
    experiment = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    aware_of_experiment = Column(Boolean, default=True, nullable=False)
    ai_post_count = Column(Integer, default=0, nullable=False)
    liked_ai_post_count = Column(Integer, default=0, nullable=False)
    real_post_count = Column(Integer, default=0, nullable=False)
    liked_real_post_count = Column(Integer, default=0, nullable=False)
    ai_marked_as_ai_count = Column(Integer, default=0, nullable=False)
    real_marked_as_ai_count = Column(Integer, default=0, nullable=False)
    ai_dislike_count = Column(Integer, default=0, nullable=False)
    real_dislike_count = Column(Integer, default=0, nullable=False)
    ai_like_rate = Column(Float, default=0.0, nullable=False)
    real_like_rate = Column(Float, default=0.0, nullable=False)
    ai_marked_as_ai_rate = Column(Float, default=0.0, nullable=False)
    real_marked_as_ai_rate = Column(Float, default=0.0, nullable=False)
    ai_dislike_rate = Column(Float, default=0.0, nullable=False)
    real_dislike_rate = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('experiment', 'user_id', name='uq_experiment_user'),
    )


class HumorPost(Base):
    __tablename__ = 'humorposts'
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    self_text = Column(Text, nullable=False)
    subreddit = Column(String(128), nullable=True)
    over_18 = Column(Boolean, default=False, nullable=False)
    link_flair_text = Column(String(128), nullable=True)
    is_ai = Column(Boolean, default=False, nullable=False)
    random_key = Column(BigInteger, index=True, nullable=False)

    # Extra fields specific to humor source
    image_url = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
