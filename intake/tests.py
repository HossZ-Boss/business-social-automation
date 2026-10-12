from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from intake.telegram_workflow import TelegramWorkflowService


class TelegramReviewCardTests(SimpleTestCase):
    def test_review_card_includes_tattoo_details(self):
        intake = SimpleNamespace(
            pk=12,
            source="whatsapp",
            approved_price="",
            ai_suggested_price="",
            price_note="",
            appointment_date="",
            appointment_time="",
            pending_hold_status="none",
            scheduled_date="",
            scheduled_time="",
            payment_status="",
            latest_summary="",
            appointment_type="",
            preferred_artist="",
            tattoo_project_type="",
            placement="left forearm",
            size_estimate_cm="8 cm",
            color_preference="black and grey",
            style_tags=["fine line", "floral"],
            tattoo_idea="A small flower",
            suggested_artist="",
            latest_draft_reply="",
        )
        service = TelegramWorkflowService()

        with (
            patch.object(service, "_format_client_identity_lines", return_value=[]),
            patch.object(service, "_reference_image_section", return_value=""),
            patch.object(service, "_ai_reply_draft_hidden", return_value=True),
        ):
            text = service._format_review_text(intake)

        self.assertIn("Placement: left forearm", text)
        self.assertIn("Size: 8 cm", text)
        self.assertIn("Color: black and grey", text)
        self.assertIn("Style: fine line, floral", text)

    def test_price_refresh_edits_current_artist_assignment_card(self):
        intake = SimpleNamespace(pk=12, assigned_artist_id=7)
        link = SimpleNamespace(
            telegram_chat_id=100,
            telegram_message_id=200,
            raw_message={"text": "old card"},
            save=Mock(),
        )
        links = Mock()
        links.order_by.return_value.first.return_value = link
        service = TelegramWorkflowService()
        service.telegram = Mock()
        service.telegram.edit_message_text.return_value = {"result": {"text": "updated card"}}

        with (
            patch("intake.telegram_workflow.TelegramMessageLink.objects.filter", return_value=links) as filter_links,
            patch.object(service, "_format_artist_update_text", return_value="updated card") as format_text,
        ):
            service._refresh_latest_artist_assignment_card(intake)

        filter_links.assert_called_once_with(
            intake=intake,
            artist_id=7,
            purpose="artist_assignment",
            is_active=True,
        )
        format_text.assert_called_once_with(
            intake,
            "You have been assigned to this request.",
            [],
            include_summary=True,
        )
        service.telegram.edit_message_text.assert_called_once_with(
            chat_id=100,
            message_id=200,
            text="updated card",
        )
        self.assertEqual(link.raw_message, {"text": "updated card"})
        link.save.assert_called_once_with(update_fields=["raw_message"])
