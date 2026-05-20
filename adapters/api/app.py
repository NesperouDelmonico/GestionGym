from fastapi import FastAPI

from adapters.api.routes.subscriptions import (
    router as subscriptions_router
)

app = FastAPI(
    title="GestionGym API"
)

app.include_router(subscriptions_router)