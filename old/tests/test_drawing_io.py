import json
import pytest
import ezdxf
from app.diagrams import DEMO
from app.db import one

def inspect(client,project_id,artifact_id):
    return client.post(f"/api/projects/{project_id}/tools/drawing_read",json={"arguments":{"artifact_id":artifact_id}})

def test_semantic_drawing_roundtrip_and_dxf_preview(client,project_id):
    result=client.post(f"/api/projects/{project_id}/tools/pfd",json={"arguments":DEMO})
    assert result.status_code==200,result.text
    for artifact in result.json()["artifacts"]:
        if artifact["kind"] not in {"svg","dxf","json"}:continue
        downloaded=client.get(artifact["download_url"]).content
        uploaded=client.post(f"/api/projects/{project_id}/upload",files={"file":(artifact["name"],downloaded)})
        assert uploaded.status_code==200,uploaded.text
        parsed=inspect(client,project_id,uploaded.json()["id"])
        assert parsed.status_code==200,parsed.text
        r=parsed.json()
        assert r["encoded_topology"]==DEMO
        assert r["topology_status"]=="encoded_unverified"
        assert r["source_sha256"]==uploaded.json()["metadata"]["sha256"]
        if artifact["kind"]=="dxf":
            preview=client.get(uploaded.json()["preview_url"])
            assert preview.headers["content-type"].startswith("image/svg+xml")
            assert "<svg" in preview.text and "R-101" in preview.text
            assert "脱氢反应器" in preview.text and "\\U+" not in preview.text
            assert any(t["text"]=="脱氢反应器" for t in r["text_elements"])

def test_plain_dxf_has_candidates_without_invented_connections(client,project_id,tmp_path):
    doc=ezdxf.new("R2004")
    model=doc.modelspace()
    model.add_line((0,0),(100,0))
    model.add_text("R-101",dxfattribs={"height":3,"insert":(0,5)})
    path=tmp_path/"external.dxf";doc.saveas(path)
    r=client.post(f"/api/projects/{project_id}/upload",files={"file":(path.name,path.read_bytes())})
    assert r.status_code==200,r.text
    parsed=inspect(client,project_id,r.json()["id"]).json()
    assert parsed["equipment_tag_candidates"]==["R-101"]
    assert parsed["topology_status"]=="not_reconstructed"
    assert parsed["encoded_topology"] is None

@pytest.mark.parametrize("content",[
    '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    '<!DOCTYPE svg [<!ENTITY a "text">]><svg>&a;</svg>',
    '<svg><image href="https://example.com/track"/></svg>',
    '<svg onload="alert(1)"/>',
    '<svg><path fill="url(https://example.com/x)"/></svg>',
])
def test_active_or_external_svg_content_is_rejected(client,project_id,content):
    r=client.post(f"/api/projects/{project_id}/upload",files={"file":("bad.svg",content.encode())})
    assert r.status_code==422,r.text

def test_drawing_read_scoped_to_project(client,project_id):
    r=client.post(f"/api/projects/{project_id}/tools/pfd",json={"arguments":DEMO}).json()
    other=client.post("/api/projects",json={"name":"隔离项目"}).json()["id"]
    assert inspect(client,other,r["artifacts"][0]["id"]).status_code==422

def test_authored_routes_survive_svg_json_and_dxf_roundtrip(client,project_id):
    from copy import deepcopy
    diagram=deepcopy(DEMO)
    route=[[150,230],[180,230],[180,300],[260,300],[260,230]]
    diagram["edges"][0]["route"]=route
    result=client.post(f"/api/projects/{project_id}/tools/pfd",json={"arguments":diagram})
    assert result.status_code==200,result.text
    for artifact in result.json()["artifacts"]:
        if artifact["kind"] in {"svg","json","dxf"}:
            parsed=inspect(client,project_id,artifact["id"]).json()
            assert parsed["encoded_topology"]["edges"][0]["route"]==route
    diagram["edges"][0]["route"]=[[2000,230],[300,230]]
    assert client.post(f"/api/projects/{project_id}/tools/pfd",json={"arguments":diagram}).status_code==422
