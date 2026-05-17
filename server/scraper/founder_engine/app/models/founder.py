from pydantic import BaseModel
from typing import Optional


class CompanyData(BaseModel):
    name: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    employees_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    followers_count: Optional[int] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    tagline: Optional[str] = None
    specialities: list[str] = []


class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    contract_type: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_data: Optional[CompanyData] = None


class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    years: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None
    school_url: Optional[str] = None


class CertificationEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issued: Optional[str] = None


class RecommendationEntry(BaseModel):
    recommender_name: Optional[str] = None
    recommender_title: Optional[str] = None
    text: Optional[str] = None


class LinkedInProfile(BaseModel):
    url: str
    member_id: Optional[str] = None
    public_id: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    country_code: Optional[str] = None
    about: Optional[str] = None
    profile_image_url: Optional[str] = None
    background_image_url: Optional[str] = None
    followers_count: Optional[int] = None
    connections_count: Optional[int] = None
    is_open_to_work: Optional[bool] = None
    has_premium: Optional[bool] = None
    has_verification_badge: Optional[bool] = None
    creation_date: Optional[str] = None
    pronoun: Optional[str] = None
    spoken_languages: list[str] = []
    experience: list[ExperienceEntry] = []
    education: list[EducationEntry] = []
    skills: list[str] = []
    certifications: list[CertificationEntry] = []
    recommendations: list[RecommendationEntry] = []
    test_scores: list[dict] = []


class GitHubRepo(BaseModel):
    name: str
    description: Optional[str] = None
    readme: Optional[str] = None
    language: Optional[str] = None
    language_bytes: dict[str, int] = {}
    stars: int = 0
    forks: int = 0
    topics: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: str


class GitHubActivity(BaseModel):
    type: str
    repo_name: str
    created_at: str


class GitHubProfile(BaseModel):
    username: str
    bio: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    location: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    avatar_url: Optional[str] = None


class GitHubData(BaseModel):
    username: Optional[str] = None
    profile: Optional[GitHubProfile] = None
    repositories: list[GitHubRepo] = []
    organizations: list[str] = []
    languages: list[str] = []
    language_bytes_total: dict[str, int] = {}
    recent_activity: list[GitHubActivity] = []


class WebPresence(BaseModel):
    personal_website: Optional[str] = None
    startup_website: Optional[str] = None
    twitter_handle: Optional[str] = None
    technologies: list[str] = []
    social_links: list[str] = []
    page_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductHuntProduct(BaseModel):
    name: str
    tagline: Optional[str] = None
    url: Optional[str] = None
    votes: Optional[int] = None


class ProductHuntData(BaseModel):
    profile_url: Optional[str] = None
    products: list[ProductHuntProduct] = []
    followers: Optional[int] = None


class DevToArticle(BaseModel):
    title: str
    url: str
    tags: list[str] = []
    reactions: int = 0
    comments: int = 0
    published_at: Optional[str] = None


class DevToData(BaseModel):
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    twitter_username: Optional[str] = None
    github_username: Optional[str] = None
    website_url: Optional[str] = None
    joined_at: Optional[str] = None
    profile_url: str
    articles: list[DevToArticle] = []


class Metadata(BaseModel):
    collected_at: str
    sources: list[str] = []
    missing_fields: list[str] = []


class FounderProfile(BaseModel):
    name: str
    linkedin: Optional[LinkedInProfile] = None
    github: GitHubData = GitHubData()
    web_presence: WebPresence = WebPresence()
    product_hunt: Optional[ProductHuntData] = None
    devto: Optional[DevToData] = None
    metadata: Metadata


class FounderInput(BaseModel):
    name: str
    linkedin_url: str
    github_username: Optional[str] = None
