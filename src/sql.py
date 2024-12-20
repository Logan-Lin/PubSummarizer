from datetime import datetime
from typing import List, Any, Dict

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'Paper'

    id = Column(String, primary_key=True)
    platform = Column(String)
    collection = Column(String)
    title = Column(String)

    pdf_url = Column(String)
    pdf_path = Column(String)
    content = Column(String)
    summary = Column(String)

    def __repr__(self):
        return f"<Paper(id={self.id}, title='{self.title}', platform='{self.platform}')>"


class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_entry(self, paper: Paper) -> None:
        session = self.Session()
        session.add(paper)
        session.commit()
        session.close()

    def get_papers(self, filters: Dict[str, Any] = None) -> List[Paper]:
        session = self.Session()
        query = session.query(Paper)
        if filters:
            query = query.filter_by(**filters)
        papers = query.all()
        session.close()
        return papers

    def update_paper(self, paper_id: str, updates: Dict[str, Any]) -> None:
        session = self.Session()
        paper = session.query(Paper).filter_by(id=paper_id).first()
        if paper:
            for key, value in updates.items():
                setattr(paper, key, value)
            session.commit()
        session.close()

    def delete_paper(self, paper_id: str) -> None:
        session = self.Session()
        paper = session.query(Paper).filter_by(id=paper_id).first()
        if paper:
            session.delete(paper)
            session.commit()
        session.close()
