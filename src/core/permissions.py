from typing import Any

from lcacollect_config.context import get_user
from lcacollect_config.exceptions import AuthenticationError
from lcacollect_config.validate import is_super_admin
from strawberry import BasePermission
from strawberry.types import Info


class IsAdmin(BasePermission):
    message = "User is not an admin"

    async def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        if user := get_user(info):
            if is_super_admin(user):
                return True
            else:
                raise AuthenticationError(self.message)
        else:
            raise AuthenticationError(self.message)
