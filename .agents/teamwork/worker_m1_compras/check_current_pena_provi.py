import json

with open("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas = json.load(f)

for c in comunas:
    if c["comuna"] in ["Peñalolén", "Providencia"]:
        print(f"=== {c['comuna']} ===")
        print("Monto total:", c["monto_total"])
        print("Top proveedores:", c["top_proveedores"])
        print("Top contratos:")
        for oc in c["top_contratos"]:
            print(" ", oc["codigo_oc"], oc["anio"], oc["monto"], oc["proveedor"], oc["descripcion"][:60])
