# Tool: BatchCalculatorTool
from typing import List, Union, Literal, Annotated, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


# ---- ops (discriminated union) ----
class Add(BaseModel):
    op: Literal["add"]
    nums: List[float] = Field(min_items=1)


class Mul(BaseModel):
    op: Literal["mul"]
    nums: List[float] = Field(min_items=1)


Op = Annotated[Union[Add, Mul], Field(discriminator="op")]


# ---- IO ----
class BatchInput(BaseToolInput):
    model_config = ConfigDict(
        title="BatchInput",
        json_schema_extra={
            "examples": [{"mode": "sum", "tasks": [{"op": "add", "nums": [1, 2, 3]}, {"op": "mul", "nums": [2, 3]}]}]
        },
    )
    tasks: List[Op] = Field(description="List of operations to run (add|mul)")
    mode: Literal["sum", "avg"] = Field(default="sum", description="Combine per-task results by sum or average")
    explain: bool = False


class BatchOutput(BaseModel):
    results: List[float]
    combined: float
    mode_used: Literal["sum", "avg"]
    summary: str | None = None


# ---- Tool ----
class BatchCalculatorTool(Tool):
    name = "BatchCalculator"
    description = (
        "Run a batch of simple ops. \nExamples:\n"
        '- {"tasks":[{"op":"add","nums":[1,2,3]}, {"op":"mul","nums":[4,5]}], "mode":"sum"}\n'
        '- {"tasks":[{"op":"mul","nums":[2,3,4]}], "mode":"avg"}\n'
        '- {"tasks":[{"op":"add","nums":[10,20]}, {"op":"add","nums":[30,40]}], "mode":"avg"}'
    )
    input_model = BatchInput
    output_model = BatchOutput

    def get_schema(self) -> Dict[str, Any]:
        inp = self.input_model.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "input": inp,
            "output": self.output_model.model_json_schema(),
            "examples": inp.get("examples", []),
        }

    async def execute(self, data: BatchInput) -> ToolResponse:
        def run(op: Op) -> float:
            if op.op == "add":
                return float(sum(op.nums))
            prod = 1.0
            for x in op.nums:
                prod *= float(x)
            return prod

        results = [run(t) for t in data.tasks]
        combined = float(sum(results)) if data.mode == "sum" else (float(sum(results)) / len(results) if results else 0.0)
        summary = (f"tasks={len(results)}, results={results}, combined={combined} ({data.mode})") if data.explain else None

        return ToolResponse.from_model(BatchOutput(results=results, combined=combined, mode_used=data.mode, summary=summary))
