"""Servicio de permisos y autorización."""

from flask import g
from app.models.user import User, UserRole


class PermissionService:
    """Valida permisos de usuario sobre recursos."""

    @staticmethod
    def is_admin_or_coordinator(user_role: str) -> bool:
        """Verifica si el usuario es admin o coordinador."""
        return user_role in (UserRole.ADMIN.value, UserRole.COORDINATOR.value)

    @staticmethod
    def is_tutor_or_higher(user_role: str) -> bool:
        """Verifica si el usuario es tutor o superior."""
        return user_role in (
            UserRole.TUTOR.value,
            UserRole.COORDINATOR.value,
            UserRole.ADMIN.value,
            UserRole.DIRECTOR.value,
        )

    @staticmethod
    def can_view_student(user_role: str, user_area: str, student_area: str) -> bool:
        """
        Verifica si el usuario puede ver los datos del estudiante.
        - Admin/Coordinador: ve todo
        - Tutor: solo ve estudiantes de su área
        """
        if PermissionService.is_admin_or_coordinator(user_role):
            return True
        if user_role == UserRole.TUTOR.value:
            return user_area == student_area
        return False

    @staticmethod
    def can_create_student(user_role: str) -> bool:
        """
        Verifica si el usuario puede crear estudiantes.
        - Solo tutores, coordinadores y admins pueden crear
        """
        return PermissionService.is_tutor_or_higher(user_role)

    @staticmethod
    def can_manage_users(user_role: str) -> bool:
        """
        Verifica si el usuario puede gestionar otros usuarios.
        - Solo admin y coordinador pueden gestionar usuarios
        """
        return PermissionService.is_admin_or_coordinator(user_role)

    @staticmethod
    def can_manage_results(user_role: str, user_area: str, result_area: str) -> bool:
        """
        Verifica si el usuario puede gestionar resultados de prueba.
        - Admin/Coordinador: ve/modifica todo
        - Tutor: solo sus resultados (misma área)
        """
        if PermissionService.is_admin_or_coordinator(user_role):
            return True
        if user_role == UserRole.TUTOR.value:
            return user_area == result_area
        return False

    @staticmethod
    def get_area_filter(user_role: str, user_area: str) -> dict:
        """
        Retorna filtro de área para queries.
        - Admin/Coordinador: sin filtro (None)
        - Tutor: filtra por su área
        """
        if PermissionService.is_admin_or_coordinator(user_role):
            return None
        return {"area": user_area}
