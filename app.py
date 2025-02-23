from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import logging
import subprocess

TERRAFORM_DIR = r"C:\Users\Dell\Desktop\SSP_metrics\terraform"

load_dotenv()

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
API_HOST = os.getenv("VMWARE_API_HOST")
VMWARE_USER = os.getenv("VMWARE_USER", "shuvechhya@vsphere.local")  
VMWARE_PASSWORD = os.getenv("VMWARE_PASSWORD", "Nepal1234$#@!#") 

# Request Models
class MemoryUpdateRequest(BaseModel):
    size_MiB: int

class CpuUpdateRequest(BaseModel):
    count: int = Field(gt=0, description="Number of CPUs must be a positive integer")
    cores_per_socket: int = Field(gt=0, description="Cores per socket must be a positive integer")
    hot_add_enabled: bool = Field(default=True, description="Enable or disable CPU hot-add")

# Helper Functions
async def get_vmware_session_id():
    url = f"https://{API_HOST}/rest/com/vmware/cis/session"
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, auth=(VMWARE_USER, VMWARE_PASSWORD))
            response.raise_for_status()
            session_id = response.json().get("value")
            if not session_id:
                raise ValueError("Session ID not found in response")
            return session_id
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail="VMware API request error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def update_vm_hardware(vm_id: str, hardware_type: str, payload: dict, session_id: str):
    url = f"https://{API_HOST}/rest/vcenter/vm/{vm_id}/hardware/{hardware_type}"
    headers = {
        "vmware-api-session-id": session_id,
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.patch(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() if response.content.strip() != b'' else {"message": f"{hardware_type.capitalize()} updated successfully"}
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail="VMware API request error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Routes
@app.patch("/vsphere/vm/{vm_id}/memory")
async def update_memory(vm_id: str, request: MemoryUpdateRequest):
    """
    Update the memory size of a VM in vSphere.
    """
    session_id = await get_vmware_session_id()
    payload = {"spec": {"size_MiB": request.size_MiB}}
    result = await update_vm_hardware(vm_id, "memory", payload, session_id)
    return {"message": "Memory updated successfully", "vm": result}

@app.patch("/vsphere/vm/{vm_id}/cpu")
async def update_cpu(vm_id: str, cpu_data: CpuUpdateRequest):
    """
    Update the CPU settings of a VM in vSphere.
    """
    session_id = await get_vmware_session_id()
    payload = {
        "spec": {
            "count": cpu_data.count,
            "cores_per_socket": cpu_data.cores_per_socket,
            "hot_add_enabled": cpu_data.hot_add_enabled
        }
    }
    result = await update_vm_hardware(vm_id, "cpu", payload, session_id)
    return {"message": "CPU updated successfully", "vm": result}

@app.post("/createvm")
def create_vm():
    try:
        os.chdir(TERRAFORM_DIR)

        # Initialize Terraform
        init_result = subprocess.run(["terraform", "init"], capture_output=True, text=True)
        if init_result.returncode != 0:
            return JSONResponse(status_code=500, content={"error": "Terraform init failed", "details": init_result.stderr})

        # Apply Terraform
        apply_result = subprocess.run(["terraform", "apply", "-auto-approve"], capture_output=True, text=True)
        if apply_result.returncode != 0:
            return JSONResponse(status_code=500, content={"error": "Terraform apply failed", "details": apply_result.stderr})

        return JSONResponse(content={"message": "VM creation triggered", "output": apply_result.stdout})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
