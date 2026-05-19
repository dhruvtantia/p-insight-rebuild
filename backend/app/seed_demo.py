from app.core.auth import get_development_user
from app.db.session import get_session_factory
from app.modules.demo.service import DemoSeedService


def main() -> None:
    SessionLocal = get_session_factory()
    with SessionLocal() as db:
        user = get_development_user(db)
        result = DemoSeedService(db).seed_for_user(user=user)
        print(
            f"Seeded {result.portfolio_name} ({result.portfolio_id}) "
            f"with {result.holdings_count} holdings: {', '.join(result.symbols)}"
        )


if __name__ == "__main__":
    main()
