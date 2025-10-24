from exam.models import MatchingParticipation
from exam.services.participation.base_restart import BaseRestartService


class MatchingParticipationRestartService(BaseRestartService):
    def get_subtype_participation(self):
        return MatchingParticipation
