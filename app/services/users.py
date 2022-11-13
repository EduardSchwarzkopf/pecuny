from .. import models, repository as repo


async def delete_self(current_user: models.User) -> bool:

    await repo.delete(current_user)

    return True
