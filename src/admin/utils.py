from sqladmin import ModelView

from src.core.models import TimeStampedModel


def get_sqladmin_mixin(model: TimeStampedModel) -> ModelView:
    class SQLAdminMixin(ModelView):
        form_excluded_columns = [model.created_at, model.updated_at]

    return SQLAdminMixin
