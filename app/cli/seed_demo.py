from __future__ import annotations
import random
from datetime import date, datetime, timedelta
from typing import List, Optional

from flask import current_app
from sqlalchemy import func
from app.extensions import db

# ------- Imports tolerantes -------
def _imports():
    Equipo = Operador = ParteDiaria = None
    ChecklistTemplate = ChecklistItem = ChecklistRun = ChecklistAnswer = None
    ArchivoAdjunto = None

    try:
        from app.models.equipo import Equipo as _Equipo
        Equipo = _Equipo
    except Exception:
        pass

    try:
        from app.models.operador import Operador as _Operador
        Operador = _Operador
    except Exception:
        pass

    try:
        from app.models.parte_diaria import ParteDiaria as _PD
        ParteDiaria = _PD
    except Exception:
        pass

    try:
        from app.models.checklist import (
            ChecklistTemplate as _Tpl,
            ChecklistItem as _Item,
            ChecklistRun as _Run,
            ChecklistAnswer as _Ans,
        )
        ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistAnswer = _Tpl, _Item, _Run, _Ans
    except Exception:
        pass

    try:
        from app.models.parte_diaria import ArchivoAdjunto as _Adj
        ArchivoAdjunto = _Adj
    except Exception:
        try:
            from app.models.archivo import ArchivoAdjunto as _Adj2
            ArchivoAdjunto = _Adj2
        except Exception:
            pass

    return (Equipo, Operador, ParteDiaria,
            ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistAnswer,
            ArchivoAdjunto)

# ------- Utilidades -------
def _commit():
    db.session.commit()

def _truncate(model):
    if model is None: return
    db.session.query(model).delete(synchronize_session=False)

def _get_or_create(model, defaults=None, **kwargs):
    if model is None: return None
    inst = db.session.query(model).filter_by(**kwargs).first()
    if inst:
        return inst
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    inst = model(**params)
    db.session.add(inst)
    return inst

# ------- Seeds -------
def seed_equipos(n: int = 5) -> List[object]:
    Equipo, *_ = _imports()
    if not Equipo: return []
    nombres = [
        "Retroexcavadora 320D", "Barcaza HFT-01", "Dragalina MX",
        "Bomba 12'' Dredger", "Bulldozer D6K", "Excavadora 336"
    ]
    random.shuffle(nombres)
    res = []
    for i in range(n):
        nm = nombres[i % len(nombres)]
        e = _get_or_create(
            Equipo,
            nombre=nm,
            defaults=dict(
                serie=f"S-{1000+i}",
                estatus="operativo",
                descripcion=f"Equipo demo {i+1}",
            ),
        )
        res.append(e)
    _commit()
    return res

def seed_operadores(n: int = 6) -> List[object]:
    _, Operador, *_ = _imports()
    if not Operador: return []
    base = [
        ("Juan Pérez", 10), ("María López", 25), ("Carlos Ruiz", -5),
        ("Ana Torres", 60), ("Luis Díaz", 0), ("Sofía Vega", -30)
    ]
    res = []
    for i in range(n):
        nombre, offset = base[i % len(base)]
        vence = date.today() + timedelta(days=offset)
        op = _get_or_create(
            Operador,
            nombre=nombre,
            defaults=dict(
                doc_id=f"LIC-{200+i}",
                licencia_vence=vence,
                estatus="activo",
                notas="Operador demo",
            ),
        )
        res.append(op)
    _commit()
    return res

def seed_partes(days: int = 10, partes_por_dia: int = 2):
    Equipo, Operador, ParteDiaria, *_ = _imports()
    if not (ParteDiaria and Equipo and Operador): return

    equipos = db.session.query(Equipo).all()
    ops = db.session.query(Operador).all()
    if not equipos or not ops: return

    start = date.today() - timedelta(days=days - 1)
    random.seed(42)

    for d in range(days):
        f = start + timedelta(days=d)
        for k in range(partes_por_dia):
            eq = random.choice(equipos)
            op = random.choice(ops)
            horas = round(random.uniform(4.0, 10.0), 1)
            incid = "" if random.random() > 0.3 else "Fuga menor en manguera"
            _get_or_create(
                ParteDiaria,
                fecha=f,
                equipo_id=eq.id if hasattr(eq, "id") else None,
                defaults=dict(
                    operador_id=getattr(op, "id", None),
                    horas_trabajo=horas,
                    incidencias=incid,
                    notas="Parte demo",
                ),
            )
    _commit()

def _ensure_checklist_template():
    *_, ChecklistTemplate, ChecklistItem, _, _ = _imports()
    if not (ChecklistTemplate and ChecklistItem): return None
    tpl = _get_or_create(
        ChecklistTemplate,
        nombre="Seguridad Operativa (DEMO)",
        defaults=dict(norma="NOM-017-STPS", descripcion="Plantilla demo"),
    )
    _commit()

    # Crear 5 ítems booleanos si no existen
    try:
        existing = db.session.query(ChecklistItem).filter_by(template_id=tpl.id).count()
    except Exception:
        existing = 0
    if existing == 0:
        textos = [
            "EPP completo",
            "Área señalizada",
            "Equipo sin fugas",
            "Documentación a bordo",
            "Operador autorizado",
        ]
        for i, t in enumerate(textos, start=1):
            db.session.add(ChecklistItem(template_id=tpl.id, orden=i, texto=t, tipo="bool"))
        _commit()
    return tpl

def seed_checklist_runs(days: int = 10):
    *_, ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistAnswer, _ = _imports()
    if not (ChecklistTemplate and ChecklistItem and ChecklistRun and ChecklistAnswer):
        return

    tpl = _ensure_checklist_template()
    if not tpl: return

    items = db.session.query(ChecklistItem).filter_by(template_id=tpl.id).order_by(ChecklistItem.orden).all()
    if not items: return

    start = date.today() - timedelta(days=days - 1)
    random.seed(99)

    for d in range(days):
        f = start + timedelta(days=d)
        # Evitar duplicados por fecha+tpl
        run = db.session.query(ChecklistRun).filter_by(template_id=tpl.id, fecha=f).first()
        if run:
            continue
        run = ChecklistRun(template_id=tpl.id, fecha=f, notas="Ejecución demo")
        db.session.add(run)
        db.session.flush()  # para tener run.id

        ok = 0
        total = 0
        for it in items:
            val = random.random() > 0.2  # 80% OK
            db.session.add(ChecklistAnswer(run_id=run.id, item_id=it.id, valor_bool=val, comentario=""))
            total += 1
            if val:
                ok += 1

        run.pct_ok = round(100.0 * ok / max(total, 1), 1)
    _commit()

# ------- CLI -------
def register_cli(app):
    import click

    @app.cli.command("demo:seed")
    @click.option("--reset/--no-reset", default=False, help="Borra datos demo antes de sembrar.")
    @click.option("--days", default=10, help="Días hacia atrás para partes y checklists.")
    @click.option("--equipos", default=5, help="Cantidad de equipos demo.")
    @click.option("--operadores", default=6, help="Cantidad de operadores demo.")
    @click.option("--partes-por-dia", default=2, help="Partes diarias por día.")
    def demo_seed(reset, days, equipos, operadores, partes_por_dia):
        """
        Crea datos demostrativos uniformes para dashboard y módulos.
        """
        (Equipo, Operador, ParteDiaria,
         ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistAnswer,
         ArchivoAdjunto) = _imports()

        if reset:
            # Orden seguro (hijos -> padres)
            if ChecklistAnswer: _truncate(ChecklistAnswer)
            if ChecklistRun: _truncate(ChecklistRun)
            if ChecklistItem: _truncate(ChecklistItem)
            if ChecklistTemplate: _truncate(ChecklistTemplate)
            if ArchivoAdjunto: _truncate(ArchivoAdjunto)
            if ParteDiaria: _truncate(ParteDiaria)
            if Operador: _truncate(Operador)
            if Equipo: _truncate(Equipo)
            _commit()
            current_app.logger.info("[demo:seed] RESET completado")

        # Semillas
        seed_equipos(n=equipos)
        seed_operadores(n=operadores)
        seed_partes(days=days, partes_por_dia=partes_por_dia)
        seed_checklist_runs(days=days)

        # KPIs rápidos
        cnt_equipos = db.session.query(func.count(Equipo.id)).scalar() if Equipo else 0
        cnt_ops = db.session.query(func.count(Operador.id)).scalar() if Operador else 0
        cnt_partes = db.session.query(func.count(ParteDiaria.id)).scalar() if ParteDiaria else 0
        cnt_runs = db.session.query(func.count(ChecklistRun.id)).scalar() if ChecklistRun else 0

        click.echo({
            "equipos": cnt_equipos,
            "operadores": cnt_ops,
            "partes": cnt_partes,
            "checklist_runs": cnt_runs,
            "days": days
        })
