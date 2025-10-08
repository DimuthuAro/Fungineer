from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs import Component, Entity

class TraceBackLogging:
    @staticmethod
    def log_traceback(msg: str):
        import traceback
        stack = "".join(traceback.format_stack()[:-1])  # omit this frame
        print(f"{msg}\nCall stack (most recent call last):\n{stack}")
        
    @staticmethod
    def log(entity: 'Entity | Component | None'):
        from ecs import Component
        msg = (
            f"Entity {getattr(entity, 'name', '<unknown>')} missing "
            "PositionComponent or SizeComponent. "
        )
        if isinstance(entity, Component):
            msg += f"Component {getattr(entity, 'name', '<unknown>')} is None."
        elif entity is None:
            msg += "Entity is None."
        TraceBackLogging.log_traceback(msg)
        
    