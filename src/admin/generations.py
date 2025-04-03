from sqladmin import ModelView

from src.admin.utils import get_sqladmin_mixin
from src.generations.models import Generation
from src.utils.constants import (
    AdminIcons,
)


class GenerationAdmin(get_sqladmin_mixin(Generation), ModelView, model=Generation):
    """
    Admin view for Generation model.

    """

    column_list = [
        Generation.id,
        Generation.user_id,
        Generation.storage_key,
        Generation.updated_at,
    ]
    column_searchable_list = [Generation.id]
    column_sortable_list = [Generation.id, Generation.status, Generation.updated_at]

    name = "Generation"
    name_plural = "Generations"
    icon = AdminIcons.GENERATIONS_ICON
