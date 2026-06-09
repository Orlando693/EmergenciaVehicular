from collections import defaultdict
from datetime import datetime, timedelta, timezone
import random

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password, verify_password
from app.plataform_superAdmin.model import SuperAdmin
from app.plataform_superAdmin.schemas import (
    PlanCreate, PlanUpdate, TenantCreate, TenantEstadoUpdate, TenantPlanUpdate,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _platform_token(superadmin: SuperAdmin) -> str:
    payload = {
        "sub":    str(superadmin.id_superadmin),
        "email":  superadmin.email,
        "nombre": superadmin.nombre,
        "rol":    "SUPERADMIN",
        "exp":    datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_platform_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("rol") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="No es un token de plataforma")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token de plataforma inválido o expirado")


# ── Auth ──────────────────────────────────────────────────────────────────────

async def login_superadmin(email: str, password: str, db: AsyncSession) -> dict:
    res = await db.execute(select(SuperAdmin).where(SuperAdmin.email == email.lower().strip()))
    sa = res.scalar_one_or_none()
    if not sa or not verify_password(password, sa.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not sa.activo:
        raise HTTPException(status_code=403, detail="Cuenta de superadmin inactiva")
    return {
        "access_token": _platform_token(sa),
        "token_type":   "bearer",
        "nombre":       sa.nombre,
        "email":        sa.email,
        "rol":          "SUPERADMIN",
    }


# ── Tenants / Organizaciones ──────────────────────────────────────────────────

async def listar_tenants(db: AsyncSession) -> list:
    from app.administracion.tenants.model import Tenant
    from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion

    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = res.scalars().all()

    result = []
    for t in tenants:
        sus = await db.execute(
            select(TenantSuscripcion).where(
                TenantSuscripcion.id_tenant == t.id_tenant,
                TenantSuscripcion.estado == "ACTIVO",
            )
        )
        sus_obj = sus.scalar_one_or_none()
        plan_nombre = plan_slug = None
        if sus_obj:
            plan_res = await db.execute(select(Plan).where(Plan.id_plan == sus_obj.id_plan))
            plan = plan_res.scalar_one_or_none()
            if plan:
                plan_nombre = plan.nombre
                plan_slug   = plan.slug

        result.append({
            "id_tenant":   t.id_tenant,
            "nombre":      t.nombre,
            "slug":        t.slug,
            "estado":      t.estado,
            "plan_nombre": plan_nombre,
            "plan_slug":   plan_slug,
            "created_at":  t.created_at,
        })
    return result


async def _obtener_tenant_platform(id_tenant: int, db: AsyncSession) -> dict:
    tenants = await listar_tenants(db)
    tenant = next((item for item in tenants if item["id_tenant"] == id_tenant), None)
    if not tenant:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return tenant


async def crear_tenant(data: TenantCreate, db: AsyncSession):
    from app.administracion.tenants.model import Tenant
    from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion

    dup = await db.execute(select(Tenant).where(Tenant.slug == data.slug.lower().strip()))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un tenant con ese slug")

    if data.id_plan is not None:
        plan = await db.get(Plan, data.id_plan)
        if not plan or plan.estado != "ACTIVO":
            raise HTTPException(status_code=400, detail="El plan seleccionado no existe o está inactivo")

    tenant = Tenant(nombre=data.nombre, slug=data.slug.lower().strip(), estado="ACTIVO")
    db.add(tenant)
    await db.flush()

    if data.id_plan:
        sus = TenantSuscripcion(id_tenant=tenant.id_tenant, id_plan=data.id_plan, estado="ACTIVO")
        db.add(sus)

    await db.commit()
    return await _obtener_tenant_platform(tenant.id_tenant, db)


async def cambiar_estado_tenant(id_tenant: int, data: TenantEstadoUpdate, db: AsyncSession):
    from app.administracion.tenants.model import Tenant

    res = await db.execute(select(Tenant).where(Tenant.id_tenant == id_tenant))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    tenant.estado = data.estado
    await db.commit()
    return await _obtener_tenant_platform(id_tenant, db)


async def asignar_plan_tenant(id_tenant: int, data: TenantPlanUpdate, db: AsyncSession):
    from app.administracion.tenants.model import Tenant
    from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion

    if not await db.get(Tenant, id_tenant):
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    plan = await db.get(Plan, data.id_plan)
    if not plan or plan.estado != "ACTIVO":
        raise HTTPException(status_code=400, detail="El plan seleccionado no existe o está inactivo")

    sus_res = await db.execute(
        select(TenantSuscripcion).where(
            TenantSuscripcion.id_tenant == id_tenant,
            TenantSuscripcion.estado == "ACTIVO",
        )
    )
    sus = sus_res.scalar_one_or_none()
    if sus:
        sus.id_plan = data.id_plan
    else:
        db.add(TenantSuscripcion(id_tenant=id_tenant, id_plan=data.id_plan, estado="ACTIVO"))
    await db.commit()
    return await _obtener_tenant_platform(id_tenant, db)


# ── Planes ────────────────────────────────────────────────────────────────────

async def listar_planes(db: AsyncSession) -> list:
    from app.gestion_comercial_servicio.planes.model import Plan

    defaults = [
        dict(slug="demo", nombre="Demo", descripcion="Plan de evaluación para comenzar", precio=0,
             max_incidentes_mes=20, max_tecnicos=2, max_usuarios=5, tiene_ia=False,
             tiene_reportes_avanzados=False, tiene_soporte_prioritario=False,
             tiene_notificaciones_push=True, orden=1, estado="ACTIVO", moneda="BOB"),
        dict(slug="basico", nombre="Básico", descripcion="Operación esencial para talleres en crecimiento", precio=199,
             max_incidentes_mes=150, max_tecnicos=10, max_usuarios=25, tiene_ia=False,
             tiene_reportes_avanzados=False, tiene_soporte_prioritario=False,
             tiene_notificaciones_push=True, orden=2, estado="ACTIVO", moneda="BOB"),
        dict(slug="pro", nombre="Pro", descripcion="Automatización, IA y reportes avanzados", precio=499,
             max_incidentes_mes=0, max_tecnicos=0, max_usuarios=0, tiene_ia=True,
             tiene_reportes_avanzados=True, tiene_soporte_prioritario=True,
             tiene_notificaciones_push=True, orden=3, estado="ACTIVO", moneda="BOB"),
    ]
    existing = set((await db.execute(select(Plan.slug))).scalars().all())
    for item in defaults:
        if item["slug"] not in existing:
            db.add(Plan(**item))
    if any(item["slug"] not in existing for item in defaults):
        await db.commit()

    res = await db.execute(select(Plan).order_by(Plan.orden))
    return res.scalars().all()


async def crear_plan(data: PlanCreate, db: AsyncSession):
    from app.gestion_comercial_servicio.planes.model import Plan

    plan = Plan(**data.model_dump(), estado="ACTIVO", moneda="BOB")
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def actualizar_plan(id_plan: int, data: PlanUpdate, db: AsyncSession):
    from app.gestion_comercial_servicio.planes.model import Plan

    res = await db.execute(select(Plan).where(Plan.id_plan == id_plan))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    for k, v in data.model_dump().items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return plan


# -- Reportes predictivos ----------------------------------------------------

def _month_start(value: datetime) -> datetime:
    return datetime(value.year, value.month, 1)


def _add_months(value: datetime, amount: int) -> datetime:
    month_index = value.year * 12 + value.month - 1 + amount
    return datetime(month_index // 12, month_index % 12 + 1, 1)


def _tree_predict(tree: dict, features: list[float]) -> float:
    node = tree
    while "value" not in node:
        node = node["left"] if features[node["feature"]] <= node["threshold"] else node["right"]
    return node["value"]


def _build_regression_tree(rows, rng: random.Random, importance: list[int], depth: int = 0) -> dict:
    targets = [target for _, target in rows]
    if depth >= 4 or len(rows) < 4 or len(set(targets)) == 1:
        return {"value": sum(targets) / len(targets)}

    feature_count = len(rows[0][0])
    candidate_features = rng.sample(range(feature_count), k=max(1, int(feature_count ** 0.5)))
    best = None
    for feature in candidate_features:
        values = sorted(set(row[0][feature] for row in rows))
        thresholds = [(a + b) / 2 for a, b in zip(values, values[1:])]
        rng.shuffle(thresholds)
        for threshold in thresholds[:8]:
            left = [row for row in rows if row[0][feature] <= threshold]
            right = [row for row in rows if row[0][feature] > threshold]
            if not left or not right:
                continue
            error = sum(
                (y - sum(v for _, v in group) / len(group)) ** 2
                for group in (left, right) for _, y in group
            )
            if best is None or error < best[0]:
                best = (error, feature, threshold, left, right)

    if best is None:
        return {"value": sum(targets) / len(targets)}
    _, feature, threshold, left, right = best
    importance[feature] += 1
    return {
        "feature": feature,
        "threshold": threshold,
        "left": _build_regression_tree(left, rng, importance, depth + 1),
        "right": _build_regression_tree(right, rng, importance, depth + 1),
    }


def _random_forest_predictor(rows):
    rng = random.Random(49340)
    importance = [0] * len(rows[0][0])
    trees = []
    for _ in range(35):
        sample = [rng.choice(rows) for _ in rows]
        trees.append(_build_regression_tree(sample, rng, importance))

    def predict(features: list[float]) -> float:
        return sum(_tree_predict(tree, features) for tree in trees) / len(trees)

    return predict, importance


async def reporte_predictivo(db: AsyncSession) -> dict:
    from app.administracion.tenants.model import Tenant
    from app.administracion.usuarios.model import Usuario
    from app.gestion_comercial_servicio.planes.model import Plan, TenantSuscripcion
    from app.gestion_incidentes.incidentes.model import Incidente

    tenants = list((await db.execute(select(Tenant).order_by(Tenant.nombre))).scalars().all())
    incidents = (await db.execute(select(Incidente.id_tenant, Incidente.created_at))).all()
    user_counts = dict((await db.execute(
        select(Usuario.id_tenant, func.count(Usuario.id_usuario)).group_by(Usuario.id_tenant)
    )).all())
    subscriptions = (await db.execute(
        select(TenantSuscripcion.id_tenant, Plan.nombre, Plan.orden)
        .join(Plan, Plan.id_plan == TenantSuscripcion.id_plan)
        .where(TenantSuscripcion.estado == "ACTIVO")
    )).all()
    plans = {tenant_id: (name, order) for tenant_id, name, order in subscriptions}

    current_month = _month_start(datetime.now())
    months = [_add_months(current_month, offset) for offset in range(-6, 1)]
    counts = defaultdict(int)
    global_history = {month: 0 for month in months}
    for tenant_id, created_at in incidents:
        if not created_at:
            continue
        month = _month_start(created_at.replace(tzinfo=None))
        counts[(tenant_id, month)] += 1
        if month in global_history:
            global_history[month] += 1

    training = []
    for tenant in tenants:
        plan_order = plans.get(tenant.id_tenant, ("Sin plan", 0))[1]
        users = user_counts.get(tenant.id_tenant, 0)
        series = [counts[(tenant.id_tenant, month)] for month in months]
        for index in range(2, len(series)):
            features = [series[index - 1], sum(series[index - 2:index]) / 2, users, plan_order, index]
            training.append((features, float(series[index])))

    feature_names = ["Incidentes mes anterior", "Promedio móvil", "Usuarios", "Nivel del plan", "Tendencia temporal"]
    if training:
        predict, raw_importance = _random_forest_predictor(training)
    else:
        predict = lambda features: features[1]
        raw_importance = [0] * len(feature_names)

    predictions = []
    for tenant in tenants:
        series = [counts[(tenant.id_tenant, month)] for month in months]
        current = series[-1]
        features = [
            current, sum(series[-2:]) / 2, user_counts.get(tenant.id_tenant, 0),
            plans.get(tenant.id_tenant, ("Sin plan", 0))[1], len(months),
        ]
        forecast = max(0, round(predict(features)))
        growth = round(((forecast - current) / max(current, 1)) * 100, 1)
        risk = "ALTO" if growth >= 35 or forecast >= 100 else "MEDIO" if growth >= 10 or forecast >= 40 else "BAJO"
        recommendation = (
            "Revisar capacidad y considerar subir de plan." if risk == "ALTO"
            else "Monitorear demanda y disponibilidad de técnicos." if risk == "MEDIO"
            else "Capacidad operativa estable."
        )
        predictions.append({
            "id_tenant": tenant.id_tenant,
            "nombre": tenant.nombre,
            "plan_nombre": plans.get(tenant.id_tenant, ("Sin plan", 0))[0],
            "incidentes_mes_actual": current,
            "prediccion_proximo_mes": forecast,
            "crecimiento_pct": growth,
            "riesgo": risk,
            "recomendacion": recommendation,
        })

    predictions.sort(key=lambda item: (item["riesgo"] == "ALTO", item["prediccion_proximo_mes"]), reverse=True)
    total_importance = sum(raw_importance) or 1
    return {
        "modelo": "Random Forest Regressor",
        "modo": "entrenado" if len(training) >= 10 else "estimación con datos limitados",
        "registros_entrenamiento": len(training),
        "total_organizaciones": len(tenants),
        "prediccion_total_proximo_mes": sum(item["prediccion_proximo_mes"] for item in predictions),
        "organizaciones_riesgo_alto": sum(item["riesgo"] == "ALTO" for item in predictions),
        "historico_global": [
            {"periodo": month.strftime("%Y-%m"), "incidentes": total}
            for month, total in global_history.items()
        ],
        "importancia_variables": [
            {"nombre": name, "porcentaje": round(value * 100 / total_importance, 1)}
            for name, value in zip(feature_names, raw_importance)
        ],
        "predicciones": predictions,
    }
