from exam.models import TypingParticipation
from exam.services.participation.base_restart import BaseRestartService


class TypingParticipationRestartService(BaseRestartService):
    def get_subtype_participation(self):
        return TypingParticipation
