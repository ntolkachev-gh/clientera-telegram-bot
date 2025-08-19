"""
Тесты для функции handle_create_booking с локальной базой данных
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from database.models import Client, Appointment
from database.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class TestCreateBookingWithDB:
    """Тесты для создания записей в локальной БД"""

    @pytest.mark.asyncio
    async def test_create_booking_in_local_db(self, tools_handler_mock):
        """Тест создания записи в локальной базе данных"""
        # Arrange - подготавливаем данные
        test_phone = "+79991234567"
        test_name = "Тестовый Клиент"
        test_datetime = "2024-01-15T10:00:00"

        # Act - создаем запись
        result = await tools_handler_mock.handle_create_booking(
            service_ids=[456],
            staff_id=123,
            booking_datetime=test_datetime,
            fullname=test_name,
            phone=test_phone,
            comment="Тестовая запись"
        )

        # Assert
        assert result["success"] is True
        assert "booking" in result
        booking = result["booking"]
        assert booking["record_id"] > 0
        assert booking["client_name"] == test_name
        assert booking["phone"] == test_phone
        assert booking["status"] == "scheduled"

        # Проверяем, что запись действительно создана в БД
        with SessionLocal() as db:
            appointment = db.query(Appointment).filter(
                Appointment.id == booking["record_id"]
            ).first()

            assert appointment is not None
            assert appointment.status == "scheduled"
            assert appointment.service_name == "Услуга #456"
            assert appointment.master_name == "Мастер #123"

            # Удаляем тестовую запись
            db.delete(appointment)
            db.commit()

    @pytest.mark.asyncio
    async def test_create_booking_with_existing_client(self, tools_handler_mock):
        """Тест создания записи для существующего клиента"""
        # Arrange - создаем клиента в БД
        with SessionLocal() as db:
            test_client = Client(
                telegram_id="test_telegram_123",
                first_name="Иван",
                last_name="Иванов",
                phone="+79991234567"
            )
            db.add(test_client)
            db.commit()
            client_id = test_client.id

        # Устанавливаем telegram_id в handler
        tools_handler_mock.telegram_id = "test_telegram_123"

        try:
            # Act
            result = await tools_handler_mock.handle_create_booking(
                service_ids=[456, 457],
                staff_id=123,
                booking_datetime="2024-01-15T14:00:00",
                fullname="Иван Иванов",
                phone="+79991234567"
            )

            # Assert
            assert result["success"] is True
            booking = result["booking"]

            # Проверяем в БД
            with SessionLocal() as db:
                appointment = db.query(Appointment).filter(
                    Appointment.id == booking["record_id"]
                ).first()

                assert appointment is not None
                assert appointment.client_id == client_id
                assert appointment.service_name == "Услуга #456, Услуга #457"

                # Удаляем тестовые данные
                db.delete(appointment)
                db.commit()

        finally:
            # Cleanup - удаляем тестового клиента
            with SessionLocal() as db:
                test_client = db.query(Client).filter(
                    Client.id == client_id
                ).first()
                if test_client:
                    db.delete(test_client)
                    db.commit()

    @pytest.mark.asyncio
    async def test_create_multiple_bookings(self, tools_handler_mock):
        """Тест создания нескольких записей подряд"""
        created_ids = []

        try:
            # Создаем несколько записей
            for i in range(3):
                result = await tools_handler_mock.handle_create_booking(
                    service_ids=[456 + i],
                    staff_id=123 + i,
                    booking_datetime=f"2024-01-15T{10+i}:00:00",
                    fullname=f"Клиент {i+1}",
                    phone=f"+7999123456{i}"
                )

                assert result["success"] is True
                created_ids.append(result["booking"]["record_id"])

            # Проверяем, что все записи созданы
            assert len(created_ids) == 3
            assert len(set(created_ids)) == 3  # Все ID уникальны

            # Проверяем в БД
            with SessionLocal() as db:
                appointments = db.query(Appointment).filter(
                    Appointment.id.in_(created_ids)
                ).all()

                assert len(appointments) == 3

        finally:
            # Cleanup
            with SessionLocal() as db:
                for app_id in created_ids:
                    appointment = db.query(Appointment).filter(
                        Appointment.id == app_id
                    ).first()
                    if appointment:
                        db.delete(appointment)
                db.commit()

    @pytest.mark.asyncio
    async def test_booking_with_invalid_datetime(self, tools_handler_mock):
        """Тест обработки некорректной даты"""
        # Act
        result = await tools_handler_mock.handle_create_booking(
            service_ids=[456],
            staff_id=123,
            booking_datetime="некорректная дата",
            fullname="Клиент",
            phone="+79991234567"
        )

        # Assert
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_booking_status_tracking(self, tools_handler_mock):
        """Тест отслеживания статуса записи"""
        # Act - создаем запись
        result = await tools_handler_mock.handle_create_booking(
            service_ids=[456],
            staff_id=123,
            booking_datetime="2024-01-20T15:00:00",
            fullname="Статусный Клиент",
            phone="+79991234567"
        )

        assert result["success"] is True
        booking_id = result["booking"]["record_id"]

        try:
            # Проверяем начальный статус
            with SessionLocal() as db:
                appointment = db.query(Appointment).filter(
                    Appointment.id == booking_id
                ).first()

                assert appointment.status == "scheduled"

                # Меняем статус на completed
                appointment.status = "completed"
                db.commit()

                # Проверяем изменение
                updated = db.query(Appointment).filter(
                    Appointment.id == booking_id
                ).first()
                assert updated.status == "completed"

        finally:
            # Cleanup
            with SessionLocal() as db:
                appointment = db.query(Appointment).filter(
                    Appointment.id == booking_id
                ).first()
                if appointment:
                    db.delete(appointment)
                    db.commit()

    @pytest.mark.asyncio
    async def test_booking_with_duration(self, tools_handler_mock):
        """Тест создания записи с указанием длительности"""
        # Act
        result = await tools_handler_mock.handle_create_booking(
            service_ids=[456],
            staff_id=123,
            booking_datetime="2024-01-25T10:00:00",
            fullname="Клиент с длительностью",
            phone="+79991234567",
            duration_minutes=90  # Если метод поддерживает
        )

        assert result["success"] is True
        booking_id = result["booking"]["record_id"]

        try:
            # Проверяем в БД
            with SessionLocal() as db:
                appointment = db.query(Appointment).filter(
                    Appointment.id == booking_id
                ).first()

                assert appointment is not None
                # По умолчанию 60 минут, если не передано иначе
                assert appointment.duration_minutes == 60

        finally:
            # Cleanup
            with SessionLocal() as db:
                appointment = db.query(Appointment).filter(
                    Appointment.id == booking_id
                ).first()
                if appointment:
                    db.delete(appointment)
                    db.commit()


class TestAppointmentQueries:
    """Тесты для запросов к записям в БД"""

    @pytest.mark.asyncio
    async def test_get_client_appointments(self):
        """Тест получения записей клиента"""
        # Создаем тестового клиента и записи
        with SessionLocal() as db:
            client = Client(
                telegram_id="test_query_client",
                first_name="Тест",
                phone="+79991234567"
            )
            db.add(client)
            db.commit()

            # Создаем несколько записей
            for i in range(3):
                appointment = Appointment(
                    client_id=client.id,
                    service_name=f"Услуга {i+1}",
                    master_name=f"Мастер {i+1}",
                    appointment_datetime=datetime(2024, 1, 15+i, 10, 0),
                    status="scheduled" if i < 2 else "completed"
                )
                db.add(appointment)
            db.commit()

            # Запрашиваем записи клиента
            appointments = db.query(Appointment).filter(
                Appointment.client_id == client.id
            ).all()

            assert len(appointments) == 3

            # Проверяем только активные записи
            active = db.query(Appointment).filter(
                Appointment.client_id == client.id,
                Appointment.status == "scheduled"
            ).all()

            assert len(active) == 2

            # Cleanup
            for app in appointments:
                db.delete(app)
            db.delete(client)
            db.commit()

    @pytest.mark.asyncio
    async def test_get_appointments_by_date(self):
        """Тест получения записей по дате"""
        target_date = datetime(2024, 2, 1, 10, 0)

        with SessionLocal() as db:
            # Создаем тестового клиента
            test_client = Client(
                telegram_id="test_date_client",
                first_name="Дата",
                phone="+79991234567"
            )
            db.add(test_client)
            db.commit()

            # Создаем записи на разные даты
            appointments = []
            for i in range(5):
                appointment = Appointment(
                    client_id=test_client.id,
                    service_name="Тестовая услуга",
                    master_name="Тестовый мастер",
                    appointment_datetime=datetime(2024, 2, 1+i, 10, 0),
                    status="scheduled"
                )
                db.add(appointment)
                appointments.append(appointment)
            db.commit()

            # Запрашиваем записи на конкретную дату
            from sqlalchemy import func
            daily_appointments = db.query(Appointment).filter(
                func.date(Appointment.appointment_datetime) == target_date.date()
            ).all()

            assert len(daily_appointments) == 1

            # Cleanup
            for app in appointments:
                db.delete(app)
            db.delete(test_client)
            db.commit()
