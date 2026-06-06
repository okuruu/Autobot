from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class JobListing:
    title: str
    company: str
    url: str
    site: str

@dataclass
class JobDetail:
    listing: JobListing
    description: str

@dataclass
class ApplicationStatus:
    url: str
    status: str

class BaseSite(ABC):
    @abstractmethod
    def login(self) -> None: ...

    @abstractmethod
    def search_jobs(self, keywords: list[str], location: str) -> list[JobListing]: ...

    @abstractmethod
    def get_job_detail(self, listing: JobListing) -> JobDetail: ...

    @abstractmethod
    def apply(self, job: JobDetail, cv_path: str, cover_letter: str) -> bool: ...

    @abstractmethod
    def get_application_statuses(self) -> list[ApplicationStatus]: ...
