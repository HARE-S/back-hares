"""Tests para BE-43: Gestión de usuarios y asignación de roles."""

import pytest
from app.models.user import User, UserRole
from app.models.center import Center, Section
from app.services.user_service import UserService
from app.core.exceptions import ValidationError, ConflictError, NotFoundError


class TestUserManagement:
    """Tests para UserService (BE-43)."""

    def test_create_user(self, app, db_session):
        """Crear un nuevo usuario."""
        service = UserService(db_session)
        result = service.create_user(
            email="admin@grupopenascal.com",
            name="Admin",
            role=UserRole.ADMIN.value,
        )

        assert result["email"] == "admin@grupopenascal.com"
        assert result["name"] == "Admin"
        assert result["role"] == "admin"
        assert result["is_active"] is True

    def test_create_user_invalid_role(self, app, db_session):
        """No se puede crear usuario con rol inválido."""
        service = UserService(db_session)
        with pytest.raises(ValidationError):
            service.create_user(
                email="user@grupopenascal.com",
                name="User",
                role="invalid_role",
            )

    def test_create_user_duplicate_email(self, app, db_session):
        """No se puede crear usuario con email duplicado."""
        service = UserService(db_session)
        service.create_user(
            email="dup@grupopenascal.com",
            name="User1",
            role="tutor",
        )

        with pytest.raises(ConflictError):
            service.create_user(
                email="dup@grupopenascal.com",
                name="User2",
                role="admin",
            )

    def test_get_user(self, app, db_session):
        """Obtener un usuario por ID."""
        # Crear usuario
        user = User(
            email="get@grupopenascal.com",
            name="Get",
            role=UserRole.TUTOR.value,
        )
        db_session.add(user)
        db_session.flush()

        # Obtener
        service = UserService(db_session)
        result = service.get_user(str(user.id))

        assert result["email"] == "get@grupopenascal.com"
        assert result["name"] == "Get"

    def test_get_user_not_found(self, app, db_session):
        """No se encuentra usuario inexistente."""
        service = UserService(db_session)
        with pytest.raises(NotFoundError):
            service.get_user("00000000-0000-0000-0000-000000000000")

    def test_list_users_paginated(self, app, db_session):
        """Listar usuarios con paginación."""
        # Crear varios usuarios
        for i in range(15):
            user = User(
                email=f"user{i}@grupopenascal.com",
                name=f"User{i}",
                role=UserRole.TUTOR.value,
            )
            db_session.add(user)
        db_session.commit()

        # Listar
        service = UserService(db_session)
        result = service.list_users(page=1, limit=10)

        assert len(result["items"]) == 10
        assert result["total"] == 15
        assert result["pages"] == 2

    def test_update_user_role(self, app, db_session):
        """Cambiar rol de un usuario."""
        user = User(
            email="rolechange@grupopenascal.com",
            name="RoleChange",
            role=UserRole.TUTOR.value,
        )
        db_session.add(user)
        db_session.flush()

        service = UserService(db_session)
        result = service.update_user_role(str(user.id), UserRole.COORDINATOR.value)

        assert result["role"] == "coordinador"

    def test_update_user_role_invalid(self, app, db_session):
        """No se puede cambiar a rol inválido."""
        user = User(
            email="badrole@grupopenascal.com",
            name="BadRole",
            role=UserRole.TUTOR.value,
        )
        db_session.add(user)
        db_session.flush()

        service = UserService(db_session)
        with pytest.raises(ValidationError):
            service.update_user_role(str(user.id), "invalid_role")

    def test_assign_section(self, app, db_session):
        """Asignar usuario a sección."""
        # Crear usuario y sección
        user = User(
            email="assign@grupopenascal.com",
            name="Assign",
            role=UserRole.TUTOR.value,
        )
        section = Section(name="Section1", center=Center(name="Centro"))
        db_session.add(user)
        db_session.add(section)
        db_session.flush()

        # Asignar
        service = UserService(db_session)
        service.assign_section(str(user.id), str(section.id))

        # Verificar
        db_session.refresh(user)
        assert len(user.sections) == 1
        assert str(user.sections[0].id) == str(section.id)

    def test_assign_section_duplicate(self, app, db_session):
        """No se puede asignar usuario a misma sección dos veces."""
        user = User(
            email="dup@grupopenascal.com",
            name="Dup",
            role=UserRole.TUTOR.value,
        )
        section = Section(name="Section2", center=Center(name="Centro"))
        db_session.add(user)
        db_session.add(section)
        db_session.flush()

        service = UserService(db_session)
        service.assign_section(str(user.id), str(section.id))

        with pytest.raises(ConflictError):
            service.assign_section(str(user.id), str(section.id))

    def test_deactivate_user(self, app, db_session):
        """Desactivar un usuario."""
        user = User(
            email="deactivate@grupopenascal.com",
            name="Deactivate",
            role=UserRole.TUTOR.value,
        )
        db_session.add(user)
        db_session.flush()

        service = UserService(db_session)
        result = service.deactivate_user(str(user.id))

        assert result["is_active"] is False
