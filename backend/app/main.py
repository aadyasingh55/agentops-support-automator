from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tickets import router as tickets_router
from app.core.settings import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgentOps Support Automator",
    description="Multi-agent technical support workflow automation with human review.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tickets_router)
