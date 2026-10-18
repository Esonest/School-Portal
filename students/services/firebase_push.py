import json
import logging
import os

import firebase_admin

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from firebase_admin import credentials, messaging

from accounts.models import School
from students.models import (
    Announcement,
    DevicePushToken,
    Student,
)

from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


def get_firebase_app():
    """
    Initialize Firebase Admin once per Django process.
    Credentials come from the server environment.
    """

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    service_account_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    if not service_account_json:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not configured."
        )

    service_account_info = json.loads(
        service_account_json
    )

    credential = credentials.Certificate(
        service_account_info
    )

    return firebase_admin.initialize_app(
        credential
    )


def get_announcement_recipient_user_ids(announcement):
    """
    Return unique user IDs belonging to the announcement's
    selected audience, restricted to the same school.
    """

    targets = announcement.targets or []

    recipient_ids = set()

    # Entire school.
    if "all" in targets:
        students = Student.objects.filter(
            school=announcement.school,
            is_active=True,
            user__is_active=True,
        ).values_list(
            "user_id",
            flat=True,
        )

        recipient_ids.update(students)

    # Selected classes.
    if "class" in targets:
        class_ids = announcement.school_classes.filter(
            school=announcement.school
        ).values_list(
            "id",
            flat=True,
        )

        students = Student.objects.filter(
            school=announcement.school,
            school_class_id__in=class_ids,
            is_active=True,
            user__is_active=True,
        ).values_list(
            "user_id",
            flat=True,
        )

        recipient_ids.update(students)

    # Selected students.
    if "student" in targets:
        students = announcement.students.filter(
            school=announcement.school,
            is_active=True,
            user__is_active=True,
        ).values_list(
            "user_id",
            flat=True,
        )

        recipient_ids.update(students)

    # Teachers in this school.
    if "teachers" in targets:
        User = get_user_model()

        teacher_query = Q(role="teacher")

        # Support the legacy teacher flag as well.
        if any(
            field.name == "is_teacher"
            for field in User._meta.get_fields()
        ):
            teacher_query |= Q(is_teacher=True)

        teachers = User.objects.filter(
            teacher_query,
            school=announcement.school,
            is_active=True,
        ).values_list(
            "id",
            flat=True,
        )

        recipient_ids.update(teachers)

    return recipient_ids


def send_announcement_push(announcement_id):
    """
    Send one Firebase push notification for an announcement.

    The announcement's existing audience selection is respected.
    The existing email/WhatsApp announcement processor is untouched.
    """

    try:
        announcement = Announcement.objects.select_related(
            "school"
        ).get(pk=announcement_id)
    except Announcement.DoesNotExist:
        logger.warning(
            "Push skipped: announcement %s does not exist.",
            announcement_id,
        )
        return

    now = timezone.now()

    # Do not push inactive, not-yet-published, or expired items.
    if not announcement.is_active:
        return

    if announcement.publish_date and announcement.publish_date > now:
        logger.info(
            "Push skipped because announcement %s is scheduled for later.",
            announcement_id,
        )
        return

    if announcement.expiry_date and announcement.expiry_date < now:
        return

    # Prevent duplicate processing after a successful dispatch.
    if announcement.push_sent_at:
        logger.info(
            "Push already processed for announcement %s.",
            announcement_id,
        )
        return

    recipient_user_ids = get_announcement_recipient_user_ids(
        announcement
    )

    if not recipient_user_ids:
        logger.info(
            "No recipients for announcement %s.",
            announcement_id,
        )
        return

    tokens = list(
        DevicePushToken.objects.filter(
            user_id__in=recipient_user_ids,
            school=announcement.school,
            is_active=True,
        ).values_list(
            "token",
            flat=True,
        ).distinct()
    )

    if not tokens:
        logger.info(
            "No registered devices for announcement %s.",
            announcement_id,
        )
        return

    try:
        get_firebase_app()
    except Exception:
        logger.exception(
            "Firebase initialization failed."
        )
        return

    title = str(announcement.title)[:200]

    # Keep the notification body within a reasonable size.
    body = str(announcement.message)[:1000]

    successful = 0
    failed = 0

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                "announcement_id": str(announcement.id),
                "school_id": str(announcement.school_id),
                "type": "announcement",
            },
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="techcenter_announcements",
                    sound="default",
                ),
            ),
            token=token,
        )

        try:
            messaging.send(message)
            successful += 1

        except messaging.UnregisteredError:
            # Firebase confirms this token is no longer registered.
            DevicePushToken.objects.filter(
                token=token
            ).update(
                is_active=False
            )
            failed += 1

        except Exception:
            logger.exception(
                "Push failed for announcement %s.",
                announcement_id,
            )
            failed += 1

    if successful:
        Announcement.objects.filter(
            pk=announcement_id,
            push_sent_at__isnull=True,
        ).update(
            push_sent_at=timezone.now()
        )

    logger.info(
        "Announcement push %s: successful=%s failed=%s",
        announcement_id,
        successful,
        failed,
    )