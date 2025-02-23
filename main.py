from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient
import uvicorn
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class VMRequest(BaseModel):
    vmname: str
    start: str = "-1h"
    stop: str = "now()"

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
ORG = os.getenv("ORG")
BUCKET = os.getenv("BUCKET")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
query_api = client.query_api()

@app.post("/vsphere/memory")
async def get_vm_memory(request: VMRequest):
    """
    Fetch 'usage_average' memory data for a specific VM.
    The VM name and time range are provided in the request body.
    """
    query = f"""
        from(bucket: "{BUCKET}")
          |> range(start: {request.start}, stop: {request.stop})
          |> filter(fn: (r) => r["_measurement"] == "vsphere_vm_mem")
          |> filter(fn: (r) => r["_field"] == "usage_average")
          |> filter(fn: (r) => r["vmname"] == "{request.vmname}")
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
    """
    
    try:
        result = query_api.query(org=ORG, query=query)
        data = [{"time": record.get_time(), "value": record.get_value()} for table in result for record in table.records]
        return {"vmname": request.vmname, "memory_usage": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"InfluxDB query error: {str(e)}")

@app.post("/vsphere/cpu")
async def get_vm_cpu(request: VMRequest):
    """
    Fetch 'usage_average' CPU data for a specific VM.
    The VM name and time range are provided in the request body.
    """
    query = f"""
        from(bucket: "{BUCKET}")
          |> range(start: {request.start}, stop: {request.stop})
          |> filter(fn: (r) => r["_measurement"] == "vsphere_vm_cpu")
          |> filter(fn: (r) => r["_field"] == "usage_average")
          |> filter(fn: (r) => r["vmname"] == "{request.vmname}")
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
    """
    
    try:
        result = query_api.query(org=ORG, query=query)
        data = [{"time": record.get_time(), "value": record.get_value()} for table in result for record in table.records]
        return {"vmname": request.vmname, "cpu_usage": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"InfluxDB query error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)