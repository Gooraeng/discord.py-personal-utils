from __future__ import annotations
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from typing import (
    Any,
    Callable,
    Coroutine,
    Hashable,
    Iterable,
    Optional,
    TypeVar,
    Union 
)

import discord


__all__ = (
    'app_group_cooldown',
    'app_group_dynamic_cooldown'
)


T = TypeVar('T')

CooldownFunction = Union[
    Callable[[discord.Interaction[Any]], Coroutine[Any, Any, T]],
    Callable[[discord.Interaction[Any]], T],
]
AppCommandsTypes = Union[app_commands.Command[Any, ..., Any], app_commands.Group]
IterableAppCommands = Iterable[AppCommandsTypes]


def group_solver(
    check : Callable[[T], T],
    iters : IterableAppCommands,
    exclude_group : Iterable[str],
):
    """_summary_

    Args:
        check (_type_): _description_
        iters (Iterable[Any]): _description_
    """
    if not iters:
        return
    
    for children in iters:
        if isinstance(children, (app_commands.Command, commands.Command)):
            check(children)
        
        elif isinstance(children, (app_commands.Group, commands.Group)):
            if children._attr and exclude_group and children._attr in exclude_group:
                continue
            group_solver(check, children.walk_commands(), exclude_group)


def app_group_cooldown(
    rate : float,
    per : float,
    key : Optional[CooldownFunction[Hashable]] = MISSING,
    *exclude_group : str,    
) -> type[T]:
    """A decorator that shares Cooldown for within `app_commands.Group` or `commands.GroupCog` classes.
    
    Attributes
    -----------
        rate: :class:`float`
            The number of commands that can be executed within the specified time period.
        per: :class:`float`
            The time period (in seconds) for the cooldown.
        key: :class:`Optional[CooldownFunction[Hashable]]`
            A function to generate a unique key for the cooldown. Defaults to None.
        exclude_group :class:`str`
            parameter
    Raises
    -------
        TypeError: If the decorator is applied to a non-commands.GroupCog or non-app_commands.Group class.
        CommandsOnCooldown: Raised when cooldown is applied.

    Returns
    -------
        T: A decorator that applies the specified cooldown to the class.
    
    Examples
    --------
    
    .. code-block:: python
        @app_group_cooldown(1.0, 5.0, lambda i : i.user.id)
        class myGroup(app_commands.Group):
            pass
        
        @app_group_cooldown(1.0, 5.0, lambda i : i.guild_id)
        class myCogGroup(commands.GroupCog, name='mycog'):
            pass
    """
    
    if not rate and not per:
        raise TypeError('rate, per must be provided.')
    
    check = app_commands.checks.cooldown(abs(rate), abs(per), key=key)

    def decorator(func : type[T]) -> type[T]:
        # when using Group, not GroupCog
        
        if issubclass(func, app_commands.Group):
            group_solver(check, func.__discord_app_commands_group_children__, exclude_group)
        
        # when using GroupCog
        elif issubclass(func, commands.GroupCog):
            group_solver(check, func.walk_app_commands(func), exclude_group)
        
        else:
            if not isinstance(func, type):
                name = f'(Function) {type(func).__name__}'
            else:
                name = f'(Class) {func.__class__.__name__}'
            raise TypeError(f'This decorator can only be applied to commands.GroupCog or app_commands.Group, not {name}')
        
        return func
    
    return decorator


def app_group_dynamic_cooldown(
    factory : CooldownFunction[Optional[app_commands.Cooldown]],
    key : Optional[CooldownFunction[Hashable]] = MISSING,
    *exclude_group : str
) -> type[T]:
    
    check = app_commands.checks.dynamic_cooldown(factory, key=key)
    
    def decorator(func : type[T]) -> type[T]:
        # when using Group, not GroupCog
        
        if issubclass(func, app_commands.Group):
            group_solver(check, func.__discord_app_commands_group_children__, exclude_group)
        
        # when using GroupCog
        elif issubclass(func, commands.GroupCog):
            group_solver(check, func.walk_app_commands(func), exclude_group)
        
        else:
            if not isinstance(func, type):
                name = f'(Function) {type(func).__name__}'
            else:
                name = f'(Class) {func.__class__.__name__}'
            raise TypeError(f'This decorator can only be applied to commands.GroupCog or app_commands.Group, not {name}')
        
        return func
    
    return decorator
