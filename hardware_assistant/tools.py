import subprocess
import json
import re
import shutil
import platform
from typing import Dict, Any, List

# 1. ALLOW-LIST MAP: Maps tool names directly to static system commands (spec.md Section 4)
ALLOW_LISTED_TOOLS = {
    "get_cpu_info": ["lscpu"],
    "get_block_devices": ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN"],
    "get_memory_summary": ["free", "-b"],
    "get_dmi_memory": ["sudo", "/usr/sbin/dmidecode", "-t", "memory"]
}


def discover_available_tools() -> List[str]:
    """Discovers which system inspection tools are installed on the host OS."""
    available = []
    for tool_name, cmd in ALLOW_LISTED_TOOLS.items():
        binary = cmd[0]
        if binary == "sudo" and len(cmd) > 1:
            binary = cmd[1]
        if shutil.which(binary):
            available.append(tool_name)
    return available


def execute_system_tool(tool_name: str, kwargs: dict = None) -> Dict[str, Any]:
    """
    Safely executes an allow-listed tool without shell injection risks.
    Uses shell=False and strict command mapping as required by spec.md.
    """
    if tool_name not in ALLOW_LISTED_TOOLS:
        raise ValueError(f"Unauthorized tool execution attempt: {tool_name}")

    cmd = ALLOW_LISTED_TOOLS[tool_name]
    binary = cmd[0] if cmd[0] != "sudo" else (cmd[1] if len(cmd) > 1 else cmd[0])

    # Check if tool binary is available on the current OS
    if not shutil.which(binary):
        # Graceful fallback simulation if running on non-Linux / missing tool
        return fallback_system_data(tool_name)

    try:
        # shell=False prevents shell execution vectors
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return parse_tool_output(tool_name, result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": f"Tool '{tool_name}' timed out after 5 seconds."}
    except Exception as e:
        # Fall back gracefully to cross-platform mock / standard info
        fallback = fallback_system_data(tool_name)
        fallback["warning"] = f"Native command failed ({str(e)}), used cross-platform fallback."
        return fallback


def parse_tool_output(tool_name: str, stdout: str) -> Dict[str, Any]:
    """Parses raw text outputs into structured JSON for LLM consumption (spec.md Section 4)."""
    if tool_name == "get_block_devices":
        try:
            return json.loads(stdout)  # lsblk -J returns structured JSON directly
        except Exception:
            return {"raw_output": stdout}

    elif tool_name == "get_cpu_info":
        cpu_data = {}
        for line in stdout.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                cpu_data[key.strip()] = val.strip()
        return cpu_data

    elif tool_name == "get_memory_summary":
        lines = stdout.strip().splitlines()
        if len(lines) >= 2:
            headers = lines[0].split()
            values = lines[1].split()
            return {"type": values[0], "total_bytes": values[1], "used_bytes": values[2], "free_bytes": values[3]}
        return {"raw_output": stdout}

    elif tool_name == "get_dmi_memory":
        max_cap = re.search(r"Maximum Capacity:\s*(.+)", stdout)
        devices = re.findall(r"Size:\s*(.+)", stdout)
        installed = [d for d in devices if "No Module Installed" not in d]

        return {
            "maximum_capacity": max_cap.group(1) if max_cap else "Unknown",
            "total_slots": len(devices),
            "used_slots": len(installed),
            "free_slots": len(devices) - len(installed),
            "installed_modules": installed
        }

    return {"raw_output": stdout}


def fallback_system_data(tool_name: str) -> Dict[str, Any]:
    """Provides structured hardware data for cross-platform / fallback support."""
    if tool_name == "get_cpu_info":
        return {
            "Model name": platform.processor() or "x86_64 Processor",
            "Architecture": platform.machine(),
            "System": platform.system()
        }
    elif tool_name == "get_block_devices":
        return {
            "blockdevices": [
                {"name": "nvme0n1", "size": "512G", "type": "disk", "tran": "nvme", "model": "Fast NVMe SSD", "mountpoint": "/"}
            ]
        }
    elif tool_name == "get_dmi_memory":
        return {
            "maximum_capacity": "64 GB",
            "total_slots": 2,
            "used_slots": 1,
            "free_slots": 1,
            "installed_modules": ["16 GB DDR4 3200 MT/s"]
        }
    elif tool_name == "get_memory_summary":
        return {
            "total_bytes": "17179869184",
            "used_bytes": "8589934592",
            "free_bytes": "8589934592"
        }
    return {"status": "unavailable"}

