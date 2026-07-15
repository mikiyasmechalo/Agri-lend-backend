from app.db.session import async_session_factory
from app.models.auth import Role


ROLES = [
    "Farmer",
    "Bank Viewer",
    "Bank Analyst",
    "Bank Administrator",
    "Platform Admin",
    "Risk Analyst",
    "Loan Officer",
]


async def seed_roles() -> None:
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(Role))
        existing = {r.name for r in result.scalars().all()}
        for name in ROLES:
            if name not in existing:
                session.add(Role(name=name, description=f"{name} role"))
        await session.commit()
        print(f"Seeded {len(ROLES)} roles")
