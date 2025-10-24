from exam.models import OrderingParticipation
from exam.services.participation.base_restart import BaseRestartService


class OrderingParticipationRestartService(BaseRestartService):
    def get_subtype_participation(self):
        return OrderingParticipation
