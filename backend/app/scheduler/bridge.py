"""
Bridge to C optimization engine via subprocess.

This module provides the interface between the Python backend and the
C-based constraint satisfaction scheduler engine.

Requirements: 3.1 (Bridge interface from design)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SchedulerErrorCode(str, Enum):
    """Error codes from the C scheduler engine."""

    NO_SOLUTION = "E002"
    TIMEOUT = "E005"
    MEMORY = "E005"
    PARSE_ERROR = "E007"
    ENGINE_NOT_FOUND = "E005"
    UNKNOWN = "E002"


class SchedulerError(Exception):
    """Exception raised when the C scheduler engine fails."""

    def __init__(
        self,
        code: SchedulerErrorCode,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert error to dictionary for API response."""
        return {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
                "suggestion": self.suggestion,
                "context": self.context,
            },
        }


@dataclass
class TaskInput:
    """Task input for the C scheduler."""

    id: int
    name: str
    type: str
    duration_slots: int
    priority: int = 50
    deadline_slot: int = -1
    is_fixed: bool = False
    preferred_energy: int = 0  # 0=any, 1=low, 2=medium, 3=peak

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "duration_slots": self.duration_slots,
            "priority": self.priority,
            "deadline_slot": self.deadline_slot,
            "is_fixed": self.is_fixed,
            "preferred_energy": self.preferred_energy,
        }


@dataclass
class TimeSlotInput:
    """Fixed time slot input for the C scheduler."""

    slot_index: int
    task_id: int = -1
    energy_level: int = 5
    is_fixed: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "slot_index": self.slot_index,
            "task_id": self.task_id,
            "energy_level": self.energy_level,
            "is_fixed": self.is_fixed,
        }


@dataclass
class TimeSlotOutput:
    """Time slot output from the C scheduler."""

    slot_index: int
    task_id: int
    energy_level: int
    is_fixed: bool

    @classmethod
    def from_dict(cls, data: dict) -> "TimeSlotOutput":
        """Create from dictionary."""
        return cls(
            slot_index=data.get("slot_index", 0),
            task_id=data.get("task_id", -1),
            energy_level=data.get("energy_level", 5),
            is_fixed=data.get("is_fixed", False),
        )


@dataclass
class ScheduleResult:
    """Result from the C scheduler optimization."""

    success: bool
    error_message: str = ""
    num_slots: int = 0
    slots: list[TimeSlotOutput] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleResult":
        """Create from dictionary."""
        slots = [TimeSlotOutput.from_dict(s) for s in data.get("slots", [])]
        return cls(
            success=data.get("success", False),
            error_message=data.get("error_message", ""),
            num_slots=data.get("num_slots", 0),
            slots=slots,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "error_message": self.error_message,
            "num_slots": self.num_slots,
            "slots": [
                {
                    "slot_index": s.slot_index,
                    "task_id": s.task_id,
                    "energy_level": s.energy_level,
                    "is_fixed": s.is_fixed,
                }
                for s in self.slots
            ],
        }


class CSchedulerBridge:
    """
    Bridge to C optimization engine via subprocess.

    This class handles communication with the C-based constraint satisfaction
    scheduler engine, including input serialization, output parsing, timeout
    handling, and error translation.
    """

    DEFAULT_TIMEOUT = 5.0  # 5 seconds

    def __init__(self, engine_path: Optional[str] = None):
        """
        Initialize the bridge.

        Args:
            engine_path: Path to the C engine executable.
                        If None, uses ENGINE_PATH from settings.
        """
        if engine_path is None:
            settings = get_settings()
            engine_path = settings.engine_path

        self.engine_path = Path(engine_path)

        # Check for .exe extension on Windows
        if not self.engine_path.exists():
            exe_path = self.engine_path.with_suffix(".exe")
            if exe_path.exists():
                self.engine_path = exe_path

    def _validate_engine(self) -> None:
        """Validate that the engine executable exists."""
        if not self.engine_path.exists():
            raise SchedulerError(
                code=SchedulerErrorCode.ENGINE_NOT_FOUND,
                message=f"C engine not found at: {self.engine_path}",
                suggestion="Ensure the C engine is compiled. Run 'make' in the engine/ directory.",
            )

    def _serialize_input(
        self,
        tasks: list[TaskInput],
        fixed_slots: list[TimeSlotInput],
        num_days: int = 7,
    ) -> str:
        """
        Serialize input data to JSON for the C engine.

        Args:
            tasks: List of tasks to schedule
            fixed_slots: List of fixed time slots
            num_days: Number of days to optimize

        Returns:
            JSON string for the C engine
        """
        input_data = {
            "tasks": [t.to_dict() for t in tasks],
            "fixed_slots": [s.to_dict() for s in fixed_slots],
            "num_days": num_days,
        }
        return json.dumps(input_data)

    def _parse_output(self, output: str) -> ScheduleResult:
        """
        Parse JSON output from the C engine.

        Args:
            output: JSON string from the C engine

        Returns:
            Parsed ScheduleResult

        Raises:
            SchedulerError: If parsing fails
        """
        try:
            data = json.loads(output)
            return ScheduleResult.from_dict(data)
        except json.JSONDecodeError as e:
            raise SchedulerError(
                code=SchedulerErrorCode.PARSE_ERROR,
                message=f"Failed to parse C engine output: {e}",
                suggestion="Check the C engine for errors.",
                context={"raw_output": output[:500]},
            )

    def _translate_error(self, result: ScheduleResult) -> SchedulerError:
        """
        Translate C engine error to SchedulerError.

        Args:
            result: Failed ScheduleResult

        Returns:
            SchedulerError with appropriate code and message
        """
        error_msg = result.error_message.lower()

        if "no solution" in error_msg or "no valid" in error_msg:
            return SchedulerError(
                code=SchedulerErrorCode.NO_SOLUTION,
                message="Cannot find a valid schedule placement",
                suggestion="Try removing some tasks or extending deadlines.",
            )
        elif "timeout" in error_msg:
            return SchedulerError(
                code=SchedulerErrorCode.TIMEOUT,
                message="Optimization took too long",
                suggestion="Try reducing the number of tasks or days to optimize.",
            )
        elif "memory" in error_msg:
            return SchedulerError(
                code=SchedulerErrorCode.MEMORY,
                message="Engine ran out of memory",
                suggestion="Try reducing the number of tasks.",
            )
        else:
            return SchedulerError(
                code=SchedulerErrorCode.UNKNOWN,
                message=result.error_message or "Scheduling failed",
                suggestion="Try removing some tasks or extending deadlines.",
            )

    async def optimize(
        self,
        tasks: list[TaskInput],
        fixed_slots: list[TimeSlotInput],
        num_days: int = 7,
        timeout: Optional[float] = None,
    ) -> ScheduleResult:
        """
        Call C engine to optimize schedule.

        Args:
            tasks: List of tasks to schedule
            fixed_slots: List of fixed time slots (classes, sleep, etc.)
            num_days: Number of days to optimize
            timeout: Timeout in seconds (default: 5.0)

        Returns:
            Optimized schedule result

        Raises:
            SchedulerError: If optimization fails
        """
        self._validate_engine()

        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        # Serialize input
        input_json = self._serialize_input(tasks, fixed_slots, num_days)

        logger.debug(
            f"Calling C engine with {len(tasks)} tasks, {len(fixed_slots)} fixed slots"
        )

        try:
            # Run the C engine as subprocess
            process = await asyncio.create_subprocess_exec(
                str(self.engine_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Send input and wait for output with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_json.encode()),
                timeout=timeout,
            )

            # Check for process errors
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else "Unknown error"
                logger.error(
                    f"C engine failed with code {process.returncode}: {error_output}"
                )

                # Try to parse error from stderr
                try:
                    error_data = json.loads(error_output)
                    result = ScheduleResult.from_dict(error_data)
                    raise self._translate_error(result)
                except json.JSONDecodeError:
                    raise SchedulerError(
                        code=SchedulerErrorCode.UNKNOWN,
                        message=f"C engine failed: {error_output}",
                        suggestion="Check the C engine logs for details.",
                    )

            # Parse output
            output = stdout.decode()
            result = self._parse_output(output)

            # Check for logical errors
            if not result.success:
                raise self._translate_error(result)

            logger.debug(f"C engine returned {result.num_slots} slots")
            return result

        except asyncio.TimeoutError:
            logger.error(f"C engine timed out after {timeout}s")
            raise SchedulerError(
                code=SchedulerErrorCode.TIMEOUT,
                message=f"C engine exceeded {timeout}s time limit",
                suggestion="Try reducing the number of tasks or days to optimize.",
            )
        except FileNotFoundError:
            raise SchedulerError(
                code=SchedulerErrorCode.ENGINE_NOT_FOUND,
                message=f"C engine not found at: {self.engine_path}",
                suggestion="Ensure the C engine is compiled. Run 'make' in the engine/ directory.",
            )

    def optimize_sync(
        self,
        tasks: list[TaskInput],
        fixed_slots: list[TimeSlotInput],
        num_days: int = 7,
        timeout: Optional[float] = None,
    ) -> ScheduleResult:
        """
        Synchronous version of optimize for testing.

        Args:
            tasks: List of tasks to schedule
            fixed_slots: List of fixed time slots
            num_days: Number of days to optimize
            timeout: Timeout in seconds

        Returns:
            Optimized schedule result
        """
        return asyncio.run(self.optimize(tasks, fixed_slots, num_days, timeout))


# Singleton instance
_bridge_instance: Optional[CSchedulerBridge] = None


def get_scheduler_bridge() -> CSchedulerBridge:
    """Get the singleton scheduler bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CSchedulerBridge()
    return _bridge_instance
