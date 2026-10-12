from types import SimpleNamespace
from unittest.mock import patch

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
