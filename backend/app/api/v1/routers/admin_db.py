import json
from datetime import date, datetime, time
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models  # noqa: F401 -- ensure all models register on Base.metadata
from app.database import Base, get_db


router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


_TABLE_WHITELIST: dict[str, Table] = dict(Base.metadata.tables)

_MAX_STR = 200


class AdminDbColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class AdminDbTable(BaseModel):
    name: str
    columns: list[AdminDbColumn]
    row_count: int


class AdminDbRowsResponse(BaseModel):
    table: str
    columns: list[AdminDbColumn]
    rows: list[dict[str, Any]]
    total: int


def _describe_columns(table: Table) -> list[AdminDbColumn]:
    return [
        AdminDbColumn(
            name=col.name,
            type=str(col.type),
            nullable=bool(col.nullable),
            primary_key=bool(col.primary_key),
        )
        for col in table.columns
    ]


def _json_default(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    return str(v)


def _serialize_value(col_type_str: str, v: Any) -> Any:
    if v is None:
        return None
    if col_type_str.upper().startswith("VECTOR"):
        try:
            n = len(v)
        except TypeError:
            n = "?"
        return f"vector[{n}]"
    if isinstance(v, (bytes, bytearray)):
        return f"<bytes len={len(v)}>"
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    if isinstance(v, (list, tuple, set)):
        s = json.dumps(list(v), ensure_ascii=False, default=_json_default)
        return s if len(s) <= _MAX_STR else s[:_MAX_STR] + "…"
    if isinstance(v, dict):
        s = json.dumps(v, ensure_ascii=False, default=_json_default)
        return s if len(s) <= _MAX_STR else s[:_MAX_STR] + "…"
    if isinstance(v, str):
        return v if len(v) <= _MAX_STR else v[:_MAX_STR] + "…"
    if isinstance(v, (int, float, bool)):
        return v
    return str(v)


@router.get("/tables", response_model=list[AdminDbTable])
async def list_tables(db: DbSession) -> list[AdminDbTable]:
    out: list[AdminDbTable] = []
    for name in sorted(_TABLE_WHITELIST.keys()):
        table = _TABLE_WHITELIST[name]
        count_result = await db.execute(select(func.count()).select_from(table))
        row_count = int(count_result.scalar() or 0)
        out.append(
            AdminDbTable(
                name=name,
                columns=_describe_columns(table),
                row_count=row_count,
            )
        )
    return out


@router.get("/tables/{table_name}", response_model=AdminDbRowsResponse)
async def query_table(
    table_name: str,
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> AdminDbRowsResponse:
    table = _TABLE_WHITELIST.get(table_name)
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table not found: {table_name}",
        )

    if sort is not None:
        if sort not in table.c:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown sort column: {sort}",
            )
        sort_col = table.c[sort]
    else:
        pk_cols = [c for c in table.columns if c.primary_key]
        sort_col = pk_cols[0] if pk_cols else None

    stmt = select(table)
    if sort_col is not None:
        stmt = stmt.order_by(
            sort_col.desc() if order == "desc" else sort_col.asc()
        )
    stmt = stmt.limit(limit).offset(offset)

    rows_result = await db.execute(stmt)
    count_result = await db.execute(select(func.count()).select_from(table))

    type_by_col = {c.name: str(c.type) for c in table.columns}
    rows: list[dict[str, Any]] = []
    for mapping in rows_result.mappings().all():
        rows.append(
            {
                name: _serialize_value(type_by_col.get(name, ""), mapping[name])
                for name in type_by_col
            }
        )

    return AdminDbRowsResponse(
        table=table_name,
        columns=_describe_columns(table),
        rows=rows,
        total=int(count_result.scalar() or 0),
    )
