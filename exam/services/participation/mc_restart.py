from exam.models import MultipleChoiceParticipation
from exam.services.participation.base_restart import BaseRestartService


class MCParticipationRestartService(BaseRestartService):
    def get_subtype_participation(self):
        return MultipleChoiceParticipation
