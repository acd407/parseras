from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple, Type, Optional


class Value(ABC):
    @abstractmethod
    def __init__(self, value_str: Optional[str] = None):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @value.setter
    @abstractmethod
    def value(self, new_value: Any) -> None:
        pass


class StringValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = value_str.strip() if value_str else ""

    def __str__(self) -> str:
        return self._value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value


class IntValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = int(value_str.strip()) if value_str else 0

    def __str__(self) -> str:
        return str(self._value)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_value: int) -> None:
        self._value = new_value


class FloatValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = float(value_str.strip()) if value_str else 0.0

    def __str__(self) -> str:
        v = self._value
        return str(int(v) if v.is_integer() else v)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        self._value = new_value


class CommaSeparatedValue(Value):
    def __init__(self, value_str: Optional[str] = None, element_type: Type[Value] = StringValue):
        self._element_type = element_type
        if value_str:
            self._value = tuple(element_type(part.strip()) for part in value_str.split(","))
        else:
            self._value = tuple()

    def __str__(self) -> str:
        return ",".join(str(v) if v is not None else "" for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value

    @value.setter
    def value(self, new_value: Tuple[Any, ...]) -> None:
        self._value = new_value


class SpaceSeparatedValue(Value):
    def __init__(self, value_str: Optional[str] = None, element_type: Type[Value] = StringValue):
        self._element_type = element_type
        if value_str:
            self._value = tuple(element_type(part.strip()) for part in value_str.split())
        else:
            self._value = tuple()

    def __str__(self) -> str:
        return " ".join(str(v) for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value

    @value.setter
    def value(self, new_value: Tuple[Any, ...]) -> None:
        self._value = new_value


class LinesValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = value_str if value_str else ""

    def __str__(self) -> str:
        return self._value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value


@dataclass
class DataValue:
    data: Tuple
    value_width: int
    values_per_line: int
    items_per_value: int
    header_values: Tuple
    count: int


class DataBlockValue(Value):
    def __init__(
        self, value_str: Optional[str] = None, value_width: int = 0, values_per_line: int = 0, items_per_value: int = 0
    ):
        if value_str:
            lines = value_str.split("\n")

            header_line = lines[0].strip()
            header_parts = [part.strip() for part in header_line.split(",")]
            header_values = tuple(header_parts)
            count = int(header_parts[0])

            data_lines = lines[1:]

            result = []
            for line in data_lines:
                line = line.rstrip()
                pos = 0
                while pos < len(line):
                    chunk = line[pos : pos + value_width].lstrip()
                    result.append(FloatValue(chunk))
                    pos += value_width

            data = tuple(result)

            self._value = DataValue(data, value_width, values_per_line, items_per_value, header_values, count)
        else:
            # 创建空的DataBlockValue
            self._value = DataValue(tuple(), value_width, values_per_line, items_per_value, ("0",), 0)

    def __str__(self) -> str:
        data_lines = []
        for i in range(0, len(self._value.data), self._value.values_per_line):
            chunk = self._value.data[i : i + self._value.values_per_line]
            line = "".join(str(v).rjust(self._value.value_width)[:self._value.value_width] for v in chunk)
            data_lines.append(line)

        return "\n".join([",".join(self._value.header_values)] + data_lines)

    @property
    def value(self) -> DataValue:
        return self._value

    @value.setter
    def value(self, new_value: DataValue) -> None:
        self._value = new_value
