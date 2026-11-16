import json
from typing import Dict, Any, List
from hardware_assistant.tools import execute_system_tool, discover_available_tools


SYSTEM_PROMPT = """
You are a Linux Hardware Assistant.
Base your response solely on the provided JSON tool output.
If the JSON does not contain the answer, state 'I cannot determine this hardware detail from system data' and list missing tools.
Never guess or hallucinate hardware parameters.
"""


class HardwareAgent:
    def __init__(self):
        self.context_memory: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, str]] = []

    def answer_query(self, user_query: str) -> str:
        """Processes natural-language hardware query using allow-listed tools."""
        q = user_query.lower()

        # Determine tools to execute
        needed_tools = []
        if "ram" in q or "memory" in q or "slot" in q:
            needed_tools.extend(["get_dmi_memory", "get_memory_summary"])
        if "cpu" in q or "processor" in q:
            needed_tools.append("get_cpu_info")
        if "disk" in q or "ssd" in q or "nvme" in q or "storage" in q:
            needed_tools.append("get_block_devices")

        if not needed_tools:
            # Default discovery
            needed_tools = ["get_cpu_info", "get_dmi_memory"]

        # Execute safe tools and update memory cache
        for tool in needed_tools:
            if tool not in self.context_memory:
                self.context_memory[tool] = execute_system_tool(tool)

        # Synthesize verified response
        return self._synthesize_answer(user_query, self.context_memory)

    def _synthesize_answer(self, query: str, data: Dict[str, Any]) -> str:
        q = query.lower()

        if "ram" in q or "memory" in q or "upgrade" in q or "slot" in q:
            dmi = data.get("get_dmi_memory", {})
            max_cap = dmi.get("maximum_capacity", "Unknown")
            total_slots = dmi.get("total_slots", 0)
            used_slots = dmi.get("used_slots", 0)
            modules = dmi.get("installed_modules", [])
            installed_desc = ", ".join(modules) if modules else "Unknown capacity"

            if total_slots > 0:
                free_slots = total_slots - used_slots
                return (
                    f"You have {installed_desc} installed across {used_slots} of {total_slots} memory slot(s). "
                    f"The motherboard supports a maximum capacity of {max_cap}. "
                    f"You have {free_slots} free slot(s) available for RAM upgrades."
                )
            return f"Memory topology: Maximum capacity supported is {max_cap}."

        if "ssd" in q or "nvme" in q or "storage" in q or "disk" in q:
            blocks = data.get("get_block_devices", {}).get("blockdevices", [])
            if blocks:
                details = [f"{b.get('name')} ({b.get('size')}, {b.get('tran', 'unknown').upper()})" for b in blocks]
                return f"Detected storage drives: {', '.join(details)}. Drives using 'nvme' transport are NVMe SSDs."
            return "No block storage devices could be determined from system data."

        if "cpu" in q or "processor" in q:
            cpu = data.get("get_cpu_info", {})
            model = cpu.get("Model name") or cpu.get("model name") or "x86_64 CPU"
            arch = cpu.get("Architecture") or cpu.get("System") or "Standard"
            return f"Your CPU model is {model} (Architecture: {arch})."

        return "I cannot determine this hardware detail from system data. Missing specialized tools."

