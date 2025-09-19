from datetime import date, timedelta
from random import randint

from app import create_app
from app.db import db
from app.models import MetricDaily, Project


def main():
    app = create_app()
    with app.app_context():
        if not Project.query.filter_by(name="Huasteca Fuel Terminal").first():
            project = Project(
                name="Huasteca Fuel Terminal",
                client="Gas Natural",
                status="activo",
                progress=35.0,
                budget=4_000_000,
                spent=1_450_000,
                start_date=date.today() - timedelta(days=60),
            )
            db.session.add(project)
            db.session.commit()

            base = date.today() - timedelta(days=29)
            progreso = 5.0
            gasto = 900_000
            for i in range(30):
                current_date = base + timedelta(days=i)
                progreso = min(100.0, progreso + randint(0, 3))
                gasto += randint(10_000, 40_000)
                db.session.add(
                    MetricDaily(
                        project_id=project.id,
                        kpi_name="progreso",
                        date=current_date,
                        value=progreso,
                    )
                )
                db.session.add(
                    MetricDaily(
                        project_id=project.id,
                        kpi_name="gasto",
                        date=current_date,
                        value=gasto,
                    )
                )

            db.session.commit()
            print("Seed demo listo.")


if __name__ == "__main__":
    main()
