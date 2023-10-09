import asyncio
from typing import Any, Callable, Iterable, List, Type

Signature = Iterable[Type]
Slot = Callable[..., Any]


class Signal:
    def __init__(self, *signature: Type) -> None:
        self._signature: Signature = signature
        self._slots: List[Slot] = []

    def connect(self, slot_: Slot) -> None:
        slot_signature = tuple(t for name, t in slot_.__annotations__.items() if name != "return")
        if slot_signature == self._signature:
            self._slots.append(slot_)
        else:
            raise ValueError(f"Slot signature {slot_signature} doesn't match Signal signature {self._signature}")

    async def emit(self, *args: Any) -> None:
        for slot_ in self._slots:
            if all(isinstance(argument, type_) for argument, type_ in zip(args, self._signature)):
                await slot_(*args)
            else:
                raise ValueError(f"Arguments {args} don't match the expected signature {self._signature}")


# class Slot:
#     def __init__(self, callable_: Callable):
#         self._callable = callable_
#         self._signature: Signature = tuple(t for _, t in callable_.__annotations__.items())
#
#     def __call__(self, *args: Any, **kwargs: Any):
#         return self._callable(*args, **kwargs)
#
#     def __getitem__(self, item):
#         return ...
#
#     @property
#     def signature(self) -> Signature:
#         return self._signature


# def slot(function: Callable[..., Any]) -> Slot[..., Any]:
#     return Slot(callable_=function)


# def slot():
#     def inner_function(function: Callable[..., Any]) -> Slot:
#         return Slot(function)
#     return inner_function


# class Signal:
#     def __init__(self, *signature: Type) -> None:
#         self._signature: Signature = signature
#         self._slots: List[Slot] = []
#
#     def connect(self, slot_: Slot) -> None:
#         if slot_.signature == self._signature:
#             self._slots.append(slot_)
#         else:
#             raise ValueError(f"Slot signature {slot_.signature} doesn't match Signal signature {self._signature}")
#
#     def emit(self, *args: Any) -> None:
#         for slot_ in self._slots:
#             if args == self._signature:
#                 slot_(*args)
#             else:
#                 raise ValueError(f"Arguments {args} don't match the expected signature {slot_.signature}")


if __name__ == "__main__":

    class _Publisher:
        sig = Signal(int, float)

        def __init__(self, subscriber):
            self.sig.connect(subscriber.slt)

    class _Subscriber:
        # @slot()
        async def slt(self, a: int, b: float):
            print(a, b)

    async def main():
        sub = _Subscriber()
        pub = _Publisher(sub)
        await pub.sig.emit(1, 2.3)
        # pub.connect(sub)

    asyncio.run(main())
