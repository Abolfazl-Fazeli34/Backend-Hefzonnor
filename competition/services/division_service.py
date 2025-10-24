import logging

from django.db.models import Q

from account.models import Profile
from competition.choices import PromotionStatusChoices
from competition.models import Week, Division, DivisionMembership, League
from economy.choices import TransactionReasonChoices, TransactionTypeChoices
from economy.models import DiamondTransaction
from economy.services.diamond_service import DiamondTransactionService

logger = logging.getLogger(__name__)


class DivisionFinalizer:
    def __init__(self, division: Division):
        self.division = division
        self.next_league = League.objects.filter(
            order__gt=division.league.order
        ).first()
        self.previous_league = League.objects.filter(
            order__lt=division.league.order
        ).first()

    def finalize_division(self):
        """
        Finalize a single division by ranking the memberships and updating user's profile and applying the demotion penalty
        """
        memberships = (
            self.division.memberships.all()
            .select_related('user', 'user__current_league')
            .order_by('-weekly_score')
        )
        promote_zone, demote_zone = self._calculate_promote_and_demote_zone()
        memberships_to_update = []
        users_to_update = []
        transactions_to_create = []

        previous_score = None
        rank = 0
        for index, membership in enumerate(memberships, start=1):
            if membership.weekly_score != previous_score:
                rank = index
            previous_score = membership.weekly_score

            self._assign_rank_and_status(
                membership, rank, promote_zone, demote_zone
            )
            memberships_to_update.append(membership)
            self._update_user_league(membership)

            tx = self._build_demotion_penalty_tx(membership)
            if tx:
                transactions_to_create.append(tx)

            users_to_update.append(membership.user)

        DivisionMembership.objects.bulk_update(memberships_to_update, fields=['rank_in_division', 'promotion_status'])
        Profile.objects.bulk_update(users_to_update, fields=['current_league', 'diamonds'])
        DiamondTransaction.objects.bulk_create(transactions_to_create)

    def _update_user_league(self, membership: DivisionMembership):
        """
        Update the user's current league
        """
        if membership.promotion_status != PromotionStatusChoices.STAYED:
            user = membership.user
            if membership.promotion_status == PromotionStatusChoices.PROMOTED:
                user.current_league = self.next_league
            elif membership.promotion_status == PromotionStatusChoices.DEMOTED:
                user.current_league = self.previous_league

    def _build_demotion_penalty_tx(self, membership: DivisionMembership):
        """
        Build a demotion penalty tx
        """
        if membership.promotion_status == PromotionStatusChoices.DEMOTED:
            return DiamondTransactionService.build_transaction(
                user=membership.user,
                amount=self.division.league.demotion_penalty,
                tx_type=TransactionTypeChoices.Deduction,
                reason=TransactionReasonChoices.DEMOTION,
                description=f" سقوط به لیگ {self.division.league.name}",
                allow_partial=True,
            )
        else:
            return None

    def _assign_rank_and_status(self, membership: DivisionMembership, rank: int, demote_zone: int, promote_zone: int):
        """
        Sort memberships by weekly_score and assign rank and set status for promotion or demotion
        """
        membership.rank_in_division = rank
        if rank <= promote_zone and membership.weekly_score >= membership.division.league.promotion_minimum_score:
            membership.promotion_status = PromotionStatusChoices.PROMOTED
        elif rank > self.division.size - demote_zone:
            membership.promotion_status = PromotionStatusChoices.DEMOTED
        else:
            membership.promotion_status = PromotionStatusChoices.STAYED

    def _calculate_promote_and_demote_zone(self):
        """
        Calculate promotion and demote zone from League.promote_rate and League.demote_rate
        """
        division_size = self.division.size
        promote_rate = self.division.league.promote_rate
        demote_rate = self.division.league.demote_rate
        league_order = self.division.league.order
        min_order = League.objects.order_by('order').first().order
        max_order = League.objects.order_by('-order').first().order

        if league_order == max_order:
            promote_zone = 0
        else:
            promote_zone = max(1, round(promote_rate * division_size))

        if league_order == min_order:
            demote_zone = 0
        else:
            demote_zone = max(1, round(demote_rate * division_size))

        return promote_zone, demote_zone


class DivisionCreator:
    def __init__(self, league: League, week: Week):
        self.league = league
        self.week = week
        self.users = list(Profile.objects.filter(user__is_active=True, current_league=league).order_by('total_score'))
        self.divisions_sizes = self._calculate_division_size()

    def create_divisions_and_division_memberships(self):
        if Division.objects.filter(week=self.week, league=self.league).exists():
            raise ValueError(f'Divisions with week {self.week} and league {self.league} already exists')

        divisions_to_create = self._prepare_divisions()

        created_divisions = Division.objects.bulk_create(divisions_to_create)

        if not created_divisions:
            created_divisions = list(Division.objects.filter(week=self.week, league=self.league).order_by('id'))

        memberships_to_create = self._prepare_memberships(created_divisions)

        DivisionMembership.objects.bulk_create(memberships_to_create)

    def _assign_users_to_divisions(self):
        divisions = [[] for _ in self.divisions_sizes]
        idx = 0

        for user in self.users:
            while len(divisions[idx]) >= self.divisions_sizes[idx]:
                idx = (idx + 1) % len(divisions)
            divisions[idx].append(user)
            idx = (idx + 1) % len(divisions)

        return divisions

    def _prepare_divisions(self):
        divisions_to_create = []
        for size in self.divisions_sizes:
            division = Division(
                league=self.league,
                week=self.week,
                size=size,
            )
            divisions_to_create.append(division)
        return divisions_to_create

    def _prepare_memberships(self, created_divisions):
        assigned_users = self._assign_users_to_divisions()
        memberships_to_create = []
        for division, users_in_division in zip(created_divisions, assigned_users):
            for user in users_in_division:
                membership = DivisionMembership(
                    division=division,
                    user=user,
                )
                memberships_to_create.append(membership)

        return memberships_to_create

    def _calculate_division_size(self):
        users_count = len(self.users)
        target_division_size = self.league.target_division_size
        max_size = self.league.max_division_size
        min_size = self.league.min_division_size

        if users_count == 0:
            return []
        if users_count < min_size:
            return [users_count]

        divisions_count = users_count // target_division_size
        while True:

            base_size = users_count // divisions_count
            remainder = users_count % divisions_count
            sizes = [base_size+ 1  if i < remainder else base_size for i in range(divisions_count)]

            if all(min_size <= s <= max_size for s in sizes):
                return sizes

            if base_size < min_size:
                divisions_count -= 1
                if divisions_count == 0:
                    raise ValueError("Impossible to split users with given constraints")
            elif base_size > max_size:
                divisions_count += 1
            else:
                raise ValueError("Impossible to split with given constraints")


class DivisionManagerService:
    @staticmethod
    def finalize_all_divisions_for_this_week(week: Week):
        """
        Finalize all divisions for this week
        """
        for division in week.division_set.all():
            try:
                DivisionFinalizer(division).finalize_division()
            except Exception as e:
                logger.exception(f"Failed to finalize division {division.id}: {e}")
                raise

    @staticmethod
    def create_new_divisions_for_week(week: Week):
        leagues = League.objects.all()
        for league in leagues:
            try:
                DivisionCreator(league, week).create_divisions_and_division_memberships()
            except Exception as e:
                logger.exception(f"Failed to create new divisions for week {week.id}: {e}")
                raise
