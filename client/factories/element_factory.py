from __future__ import annotations

from client.models.elements    import FlowchartElement, ElementType
from client.models.connections import Connection


class TemplateFactory:

    @staticmethod
    def create_sequence(x: float = 150, y: float = 80):
        start   = FlowchartElement(ElementType.TERMINATOR, x=x, y=y,          text="Начало")
        process = FlowchartElement(ElementType.PROCESS,    x=x, y=y + 100,    text="Действие")
        end     = FlowchartElement(ElementType.TERMINATOR, x=x, y=y + 200,    text="Конец")
        conns = [
            Connection(source_id=start.id,   target_id=process.id),
            Connection(source_id=process.id, target_id=end.id),
        ]
        return [start, process, end], conns

    @staticmethod
    def create_if_else(x: float = 150, y: float = 80):
        decision  = FlowchartElement(ElementType.DECISION, x=x,        y=y,       text="Условие?")
        yes_block = FlowchartElement(ElementType.PROCESS,  x=x - 120,  y=y + 120, text="Да")
        no_block  = FlowchartElement(ElementType.PROCESS,  x=x + 120,  y=y + 120, text="Нет")
        conns = [
            Connection(source_id=decision.id,  target_id=yes_block.id, label="Да"),
            Connection(source_id=decision.id,  target_id=no_block.id,  label="Нет"),
        ]
        return [decision, yes_block, no_block], conns

    @staticmethod
    def create_while_loop(x: float = 150, y: float = 80):
        condition = FlowchartElement(ElementType.DECISION, x=x, y=y,       text="Условие?")
        body      = FlowchartElement(ElementType.PROCESS,  x=x, y=y + 120, text="Тело цикла")
        conns = [
            Connection(source_id=condition.id, target_id=body.id,      label="Да"),
            Connection(source_id=body.id,      target_id=condition.id, label=""),
        ]
        return [condition, body], conns

    @staticmethod
    def create_io_process(x: float = 150, y: float = 80):
        inp  = FlowchartElement(ElementType.IO,      x=x, y=y,       text="Ввод данных")
        proc = FlowchartElement(ElementType.PROCESS, x=x, y=y + 100, text="Обработка")
        out  = FlowchartElement(ElementType.IO,      x=x, y=y + 200, text="Вывод результата")
        conns = [
            Connection(source_id=inp.id,  target_id=proc.id),
            Connection(source_id=proc.id, target_id=out.id),
        ]
        return [inp, proc, out], conns
