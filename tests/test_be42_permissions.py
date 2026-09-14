"""Tests para BE-42: Perfiles de permisos y autorización."""

import pytest
from app.models.user import User, UserRole
from app.models.student import Student
from app.services.permission_service import PermissionService


class TestPermissionService:
    """Tests para PermissionService."""

    def test_is_admin_or_coordinator(self):
        """Admin y coordinador son detectados."""
        assert PermissionService.is_admin_or_coordinator("admin")
        assert PermissionService.is_admin_or_coordinator("coordinador")
        assert not PermissionService.is_admin_or_coordinator("tutor")
        assert not PermissionService.is_admin_or_coordinator("pendiente")

    def test_is_tutor_or_higher(self):
        """Tutor, coordinador y admin son detectados."""
        assert PermissionService.is_tutor_or_higher("tutor")
        assert PermissionService.is_tutor_or_higher("coordinador")
        assert PermissionService.is_tutor_or_higher("admin")
        assert PermissionService.is_tutor_or_higher("director")
        assert not PermissionService.is_tutor_or_higher("pendiente")

    def test_can_view_student_admin(self):
        """Admin puede ver cualquier estudiante."""
        assert PermissionService.can_view_student("admin", "Cualquiera", "Cualquiera")
        assert PermissionService.can_view_student("admin", "Fontanería", "Electricidad")

    def test_can_view_student_tutor_same_area(self):
        """Tutor solo puede ver estudiantes de su área."""
        assert PermissionService.can_view_student("tutor", "Fontanería", "Fontanería")
        assert not PermissionService.can_view_student("tutor", "Fontanería", "Electricidad")

    def test_can_create_student(self):
        """Solo tutor y superior pueden crear estudiantes."""
        assert PermissionService.can_create_student("tutor")
        assert PermissionService.can_create_student("coordinador")
        assert PermissionService.can_create_student("admin")
        assert not PermissionService.can_create_student("pendiente")

    def test_can_manage_users(self):
        """Solo admin y coordinador pueden gestionar usuarios."""
        assert PermissionService.can_manage_users("admin")
        assert PermissionService.can_manage_users("coordinador")
        assert not PermissionService.can_manage_users("tutor")
        assert not PermissionService.can_manage_users("pendiente")

    def test_can_manage_results_admin(self):
        """Admin puede gestionar cualquier resultado."""
        assert PermissionService.can_manage_results("admin", "Fontanería", "Electricidad")

    def test_can_manage_results_tutor_same_area(self):
        """Tutor solo puede gestionar resultados de su área."""
        assert PermissionService.can_manage_results("tutor", "Fontanería", "Fontanería")
        assert not PermissionService.can_manage_results("tutor", "Fontanería", "Electricidad")

    def test_get_area_filter_admin(self):
        """Admin no tiene filtro de área."""
        result = PermissionService.get_area_filter("admin", "Fontanería")
        assert result is None

    def test_get_area_filter_tutor(self):
        """Tutor solo ve su área."""
        result = PermissionService.get_area_filter("tutor", "Fontanería")
        assert result == {"area": "Fontanería"}


class TestUserPermissions:
    """Tests de permisos del modelo User."""

    def test_user_with_tutor_role(self, app, db_session):
        """Crear usuario con rol tutor."""
        user = User(
            email="tutor@grupopenascal.com",
            name="Tutor",
            lastname="Test",
            area="Electricidad",
            role=UserRole.TUTOR.value,
        )
        user.set_password("securepass123")
        db_session.add(user)
        db_session.commit()

        assert user.role == "tutor"
        assert user.area == "Electricidad"
        assert user.has_role("tutor")

    def test_user_with_admin_role(self, app, db_session):
        """Crear usuario con rol admin."""
        user = User(
            email="admin@grupopenascal.com",
            name="Admin",
            lastname="Test",
            area="Administración",
            role=UserRole.ADMIN.value,
        )
        user.set_password("securepass123")
        db_session.add(user)
        db_session.commit()

        assert user.role == "admin"
        assert user.has_role("admin")


class TestStudentAreaAssignment:
    """Tests de asignación de área en estudiantes."""

    def test_student_inherits_tutor_area(self, app, db_session):
        """Estudiante hereda área del tutor que lo creó."""
        # Crear tutor
        tutor = User(
            email="tutor@grupopenascal.com",
            name="Tutor",
            lastname="Test",
            area="Fontanería",
            role=UserRole.TUTOR.value,
        )
        tutor.set_password("pass123")
        db_session.add(tutor)
        db_session.flush()

        # Crear estudiante asignado al tutor
        student = Student(
            name="Juan",
            area=tutor.area,
            created_by_user_id=tutor.id,
        )
        db_session.add(student)
        db_session.commit()

        assert student.area == "Fontanería"
        assert student.created_by_user_id == tutor.id
