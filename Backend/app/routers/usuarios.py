from fastapi import APIRouter, Depends

from app.core.dependencies import DBDep, CurrentUser, require_roles
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut, UsuarioEstadoUpdate, CambiarPasswordRequest
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("", response_model=UsuarioOut, status_code=201, summary="CU2 - Registrar usuario")
async def registrar_usuario(data: UsuarioCreate, db: DBDep):
    """Registro público. El rol puede ser CLIENTE, TALLER o ADMINISTRADOR."""
    return await usuario_service.registrar_usuario(data, db)


@router.get("/me", response_model=UsuarioOut, summary="CU3 - Ver mi perfil")
async def mi_perfil(current_user: CurrentUser):
    """Devuelve el perfil del usuario autenticado."""
    from app.schemas.usuario import UsuarioOut
    return UsuarioOut.from_orm_with_roles(current_user)


@router.put("/me", response_model=UsuarioOut, summary="CU3 - Actualizar mi perfil")
async def actualizar_mi_perfil(data: UsuarioUpdate, current_user: CurrentUser, db: DBDep):
    return await usuario_service.actualizar_perfil(current_user.id_usuario, data, db)


@router.post("/me/cambiar-password", summary="CU3 - Cambiar contraseña")
async def cambiar_password(data: CambiarPasswordRequest, current_user: CurrentUser, db: DBDep):
    return await usuario_service.cambiar_password(current_user.id_usuario, data, db)


@router.get("", response_model=list[UsuarioOut], summary="Admin - Listar usuarios",
            dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def listar_usuarios(db: DBDep):
    return await usuario_service.listar_usuarios(db)


@router.get("/{id_usuario}", response_model=UsuarioOut, summary="Admin - Obtener usuario",
            dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def obtener_usuario(id_usuario: int, db: DBDep):
    return await usuario_service.obtener_usuario(id_usuario, db)


@router.put("/{id_usuario}", response_model=UsuarioOut, summary="Admin - Actualizar usuario",
            dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def actualizar_usuario(id_usuario: int, data: UsuarioUpdate, db: DBDep):
    return await usuario_service.actualizar_perfil(id_usuario, data, db)


@router.patch("/{id_usuario}/estado", response_model=UsuarioOut, summary="Admin - Cambiar estado usuario",
              dependencies=[Depends(require_roles("ADMINISTRADOR"))])
async def cambiar_estado(id_usuario: int, data: UsuarioEstadoUpdate, db: DBDep):
    return await usuario_service.cambiar_estado(id_usuario, data.estado, db)
