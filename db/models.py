from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from db.base import Base

class Review(Base):
    __tablename__ = 'reviews'
    task_id = Column(String, primary_key=True)
    status = Column(String)
    summary = Column(JSON)

class FileIssue(Base):
    __tablename__ = 'file_issues'
    id = Column(Integer, primary_key=True)
    review_id = Column(String, ForeignKey('reviews.task_id'))
    file_name = Column(String)
    issues = Column(JSON)